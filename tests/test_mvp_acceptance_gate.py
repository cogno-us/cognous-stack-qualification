"""Gate semantics of tools/mvp_acceptance_gate.py (proposed): synthetic artifacts only, no component is run.

Each test builds a complete ACCEPT-able run directory from the real battery file, then damages exactly one thing and asserts the
verdict. A skipped, undiscovered, unexecuted or errored mandatory test is INCOMPLETE; a declared NOT APPLICABLE is accepted only when
listed; a Verifier disposition that is not exactly the expected one is a REJECT; frozen expectations are never changed to pass.
"""
import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import mvp_acceptance_gate as G  # noqa: E402

BATTERY = json.loads((ROOT / "process/mvp-acceptance/mandatory-battery.proposed.v1.json").read_text())
V4_NA = ["v4.ledger.acknowledged-attempts-have-rows", "v4.ledger.observations-agree"]
A_CNC = ["v4.ledger.acknowledged-attempts-have-rows", "v4.ledger.counts", "v4.ledger.effects-have-authorized-decisions", "v4.ledger.keys",
         "v4.ledger.observations-agree", "v4.ledger.row-matches-binding", "v4.ledger.rows-agree-with-attempts"]


def check(cid, tier, verdict="confirmed", reason=None):
    c = {"check_id": cid, "tier": tier, "verdict": verdict, "findings": []}
    if reason:
        c["could_not_check_reason"] = reason
    return c


def report_b():
    checks = [check(f"v1.c{i}", "V1") for i in range(5)] + [check(f"v2.c{i}", "V2") for i in range(18)]
    checks += [check(f"v4.ledger.ok{i}", "V4") for i in range(4)] + [check("v4.ledger.rows-agree-with-attempts", "V4", "could_not_check", "tier_unavailable")]
    na = [{"check_id": f"v2.na{i}", "tier": "V2"} for i in range(6)] + [{"check_id": i, "tier": "V4"} for i in V4_NA]
    return {"checks": checks, "summary": {"checks": 28, "confirmed": 27, "could_not_check": 1, "refuted": 0}, "extensions": {"x-not-applicable": na}}


def report_a():
    checks = [check(f"v1.c{i}", "V1") for i in range(5)] + [check(f"v2.c{i}", "V2") for i in range(17)]
    checks += [check(i, "V4", "could_not_check", "input_absent") for i in A_CNC]
    return {"checks": checks, "summary": {"checks": 29, "confirmed": 22, "could_not_check": 7, "refuted": 0}, "extensions": {"x-not-applicable": []}}


def junit(tests, overrides=None, drop=()):
    overrides = overrides or {}
    lines = ['<?xml version="1.0"?><testsuites><testsuite name="pytest">']
    for t in tests:
        if t["id"] in drop:
            continue
        cls = t["file"][:-3].replace("/", ".")
        status = overrides.get(t["id"], "PASSED")
        body = {"PASSED": "", "SKIPPED": '<skipped type="pytest.skip" message="x"/>', "FAILED": '<failure message="x"/>', "ERROR": '<error message="x"/>'}[status]
        lines.append(f'<testcase classname="{cls}" name="{t["test"]}">{body}</testcase>')
    lines.append("</testsuite></testsuites>")
    return "\n".join(lines)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gate-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.run_dir = self.tmp / "run"
        self.build()

    def build(self, *, collect_drop=(), junit_overrides=None, junit_drop=(), row_status=None, verifier_mutate=None, exclusion=None):
        shutil.rmtree(self.run_dir, ignore_errors=True)
        rd = self.run_dir
        (rd / "mvp-chain/artifacts/verifier").mkdir(parents=True)
        identity = ROOT / "process/mvp-acceptance/candidate-identity.inputs.json"
        ident = json.loads(identity.read_text())
        comps = {n: {"repository": c["repository"], "sha": c["sha"], "source": "candidate-identity", "verified_head": c["sha"], "pristine": True}
                 for n, c in ident["components"].items()}
        (rd / "tuple-resolved.json").write_text(json.dumps({"identity_file": "process/mvp-acceptance/candidate-identity.inputs.json",
                                                            "identity_sha256": G.sha256_file(identity), "overrides": {}, "components": comps}))
        rows = [{"id": t["row"], "status": (row_status or {}).get(t["row"], "PASS")} for t in BATTERY["tests"] if t["kind"] == "oracle_row"]
        v3 = BATTERY["oracle"]["unchanged_files_sha256"][BATTERY["oracle"]["expectations_in_force"]]
        (rd / "mvp-chain/results.json").write_text(json.dumps({"expectations_sha256": v3, "rows": rows, "counts": {},
                                                               "tuple": {"heads": {n: c["sha"] for n, c in comps.items()}}}))
        vrun = {}
        for label, rep, code in (("A", report_a(), 3), ("B", report_b(), 3)):
            if verifier_mutate:
                rep, code = verifier_mutate(label, rep, code)
            raw = json.dumps(rep).encode()
            (rd / f"mvp-chain/artifacts/verifier/{label}-report.json").write_bytes(raw)
            vrun[label] = {"exit_code": code, "overall": "abstain" if code == 3 else "accept", "crashed": False, "report_sha256": hashlib.sha256(raw).hexdigest(),
                           "module_path": "/x/src/cognous_verify/__init__.py", "module_path_under_pin": True}
        (rd / "mvp-chain/observations.json").write_text(json.dumps({"env": {"python": "3.13.1 (main)", "pydantic_version": "2.13.5"}, "chain": {"verifier": vrun}}))
        for tag, inv in BATTERY["invocations"].items():
            tests = [t for t in BATTERY["tests"] if t["invocation"] == tag]
            (rd / inv["junit"]).write_text(junit(tests, junit_overrides, junit_drop))
            (rd / inv["collected"]).write_text("\n".join(f"{t['file']}::{t['test']}" for t in tests if t["id"] not in collect_drop) + "\n\n50 tests collected\n")
            (rd / inv["exit_file"]).write_text("0\n")
            (rd / inv["exclusion_observation"]).write_text(json.dumps(exclusion or {"exchange_modules_loaded": [], "modules_from_exchange_paths": [], "sys_path_exchange_entries": []}))

    def verdict(self):
        doc = G.run_gate(self.run_dir, ROOT)
        self.assertIs(doc["authorizes"], False)
        self.assertEqual(doc["release"], "HOLD")
        return doc["verdict"], {c["id"]: c["status"] for c in doc["checks"]}, doc

    def test_complete_run_is_accept(self):
        v, checks, doc = self.verdict()
        self.assertEqual(v, "ACCEPT", [c for c in doc["checks"] if c["status"] != "PASS"])

    def test_skipped_mandatory_test_is_incomplete(self):
        self.build(junit_overrides={"CHAIN-03": "SKIPPED"})
        v, checks, _ = self.verdict()
        self.assertEqual((v, checks["G-05"]), ("INCOMPLETE", "INCOMPLETE"))

    def test_skipped_ruling4_and_applicability_tests_are_incomplete(self):
        for tid in ("R4-01", "AP01"):
            with self.subTest(tid):
                ids = [t["id"] for t in BATTERY["tests"]]
                self.assertIn(tid, ids)
                self.build(junit_overrides={tid: "SKIPPED"})
                self.assertEqual(self.verdict()[0], "INCOMPLETE")

    def test_not_discovered_is_incomplete(self):
        self.build(collect_drop={"NC2-02"}, junit_drop={"NC2-02"})
        v, checks, doc = self.verdict()
        self.assertEqual(v, "INCOMPLETE")
        self.assertIn("NC2-02", doc["checks"][[c["id"] for c in doc["checks"]].index("G-05")]["buckets"]["not_discovered"])

    def test_discovered_but_not_executed_is_incomplete(self):
        self.build(junit_drop={"NC3-01"})
        v, _, doc = self.verdict()
        self.assertEqual(v, "INCOMPLETE")
        self.assertIn("NC3-01", [c for c in doc["checks"] if c["id"] == "G-05"][0]["buckets"]["not_executed"])

    def test_errored_test_is_incomplete(self):
        self.build(junit_overrides={"ENV-01": "ERROR"})
        self.assertEqual(self.verdict()[0], "INCOMPLETE")

    def test_pytest_exit_status_must_be_recorded_and_judgeable(self):
        (self.run_dir / "pytest-exit-mvp-chain.txt").write_text("5\n")
        self.assertEqual(self.verdict()[1]["G-09"], "INCOMPLETE")
        (self.run_dir / "pytest-exit-mvp-chain.txt").unlink()
        self.assertEqual(self.verdict()[1]["G-09"], "INCOMPLETE")
        (self.run_dir / "pytest-exit-mvp-chain.txt").write_text("1\n")  # some tests failed: judged per test, not here
        self.assertEqual(self.verdict()[1]["G-09"], "PASS")

    def test_failed_test_is_reject_not_incomplete(self):
        self.build(junit_overrides={"NC1-04": "FAILED"}, row_status={"NC1-04": "FAIL"})
        v, checks, _ = self.verdict()
        self.assertEqual((v, checks["G-06"]), ("REJECT", "FAIL"))

    def test_incomplete_takes_precedence_over_reject(self):
        self.build(junit_overrides={"NC1-04": "FAILED", "CHAIN-03": "SKIPPED"})
        self.assertEqual(self.verdict()[0], "INCOMPLETE")

    def test_blocked_or_not_run_oracle_row_is_incomplete(self):
        for status in ("BLOCKED", "NOT RUN"):
            with self.subTest(status):
                self.build(row_status={"NC4-01": status})
                self.assertEqual(self.verdict()[0], "INCOMPLETE")

    def test_undeclared_not_applicable_is_incomplete_and_declared_is_distinct_from_a_skip(self):
        self.build(row_status={"VER-03": "NOT APPLICABLE"})
        self.assertEqual(self.verdict()[0], "INCOMPLETE")
        declared = copy.deepcopy(BATTERY)
        declared["declared_not_applicable"] = [{"id": "VER-03", "justification": "test"}]
        root = self.tmp / "root"
        shutil.copytree(ROOT / "process", root / "process", dirs_exist_ok=True)
        shutil.copytree(ROOT / "suites/v1-scenarios", root / "suites/v1-scenarios", dirs_exist_ok=True)
        (root / "process/mvp-acceptance/mandatory-battery.proposed.v1.json").write_text(json.dumps(declared))
        self.assertEqual(G.run_gate(self.run_dir, root)["verdict"], "ACCEPT")

    def test_verifier_exact_dispositions_are_asserted_not_assumed(self):
        def abstain_count(label, rep, code):
            if label == "B":
                rep["checks"][-1]["check_id"] = "v4.ledger.counts"  # a different V4 check abstains
            return rep, code
        self.build(verifier_mutate=abstain_count)
        v, checks, doc = self.verdict()
        self.assertEqual((v, checks["G-07"]), ("REJECT", "FAIL"))
        self.assertIn("abstained checks", [c for c in doc["checks"] if c["id"] == "G-07"][0]["detail"])

        def v4_confirmed_swap(label, rep, code):
            if label == "B":
                rep["checks"][23]["verdict"] = "refuted"  # one V4 check no longer confirmed
                rep["summary"] = {"checks": 28, "confirmed": 26, "could_not_check": 1, "refuted": 1}
            return rep, code
        self.build(verifier_mutate=v4_confirmed_swap)
        self.assertEqual(self.verdict()[1]["G-07"], "FAIL")

        def accept_exit(label, rep, code):
            return rep, (0 if label == "B" else code)
        self.build(verifier_mutate=accept_exit)
        self.assertEqual(self.verdict()[1]["G-07"], "FAIL")

        def fewer_na(label, rep, code):
            if label == "B":
                rep["extensions"]["x-not-applicable"] = [n for n in rep["extensions"]["x-not-applicable"] if n["tier"] != "V4"][:6]
            return rep, code
        self.build(verifier_mutate=fewer_na)
        self.assertEqual(self.verdict()[1]["G-07"], "FAIL")

    def test_report_bytes_must_match_the_recorded_hash(self):
        (self.run_dir / "mvp-chain/artifacts/verifier/B-report.json").write_text(json.dumps(report_b(), indent=3))
        self.assertEqual(self.verdict()[1]["G-07"], "FAIL")

    def test_missing_verifier_report_is_incomplete(self):
        (self.run_dir / "mvp-chain/artifacts/verifier/A-report.json").unlink()
        self.assertEqual(self.verdict()[1]["G-07"], "INCOMPLETE")

    def test_exchange_module_loaded_is_reject_and_missing_observation_is_incomplete(self):
        self.build(exclusion={"exchange_modules_loaded": ["experiments.odex_gax_imx_reference"], "modules_from_exchange_paths": [], "sys_path_exchange_entries": []})
        self.assertEqual(self.verdict()[1]["G-08"], "FAIL")
        self.build()
        (self.run_dir / "exchange-exclusion-mvp-chain.json").unlink()
        self.assertEqual(self.verdict()[1]["G-08"], "INCOMPLETE")

    def test_tuple_must_be_exact_and_pristine(self):
        path = self.run_dir / "tuple-resolved.json"
        doc = json.loads(path.read_text())
        doc["components"]["runtime"]["verified_head"] = "0" * 40
        path.write_text(json.dumps(doc))
        self.assertEqual(self.verdict()[1]["G-01"], "INCOMPLETE")

    def test_changed_frozen_expectation_is_refused(self):
        root = self.tmp / "root2"
        shutil.copytree(ROOT / "process", root / "process")
        shutil.copytree(ROOT / "suites/v1-scenarios", root / "suites/v1-scenarios")
        target = root / "process/mvp-chain/expectations.proposed.v3.json"
        target.write_text(target.read_text().replace('"mandatory": true', '"mandatory": true ', 1))
        doc = G.run_gate(self.run_dir, root)
        self.assertEqual({c["id"]: c["status"] for c in doc["checks"]}["G-02"], "FAIL")
        self.assertNotEqual(doc["verdict"], "ACCEPT")

    def test_old_python_or_pydantic_is_incomplete(self):
        path = self.run_dir / "mvp-chain/observations.json"
        doc = json.loads(path.read_text())
        doc["env"]["pydantic_version"] = "2.11.9"
        path.write_text(json.dumps(doc))
        self.assertEqual(self.verdict()[1]["G-04"], "INCOMPLETE")


class ResolveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="resolve-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.identity = ROOT / "process/mvp-acceptance/candidate-identity.inputs.json"

    def run_resolve(self, overrides=None):
        return G.resolve(self.identity, overrides or {}, self.tmp / "pin.json", self.tmp / "resolved.json", self.tmp / "out.txt")

    def test_identity_inputs_are_a_full_pinned_tuple_without_exchange(self):
        doc = self.run_resolve()
        self.assertEqual(sorted(doc["components"]), sorted(G.EXPECTED_COMPONENTS))
        short = {"control_plane": "7a4bcd40", "runtime": "ec728da6", "replay": "ab421ad0", "evidence_pack": "79ae34d9", "odes": "eae95dd3",
                 "verifier": "c0b8ba1f", "action_manifest": "fa170815", "hub": "43c526eb"}
        for name, prefix in short.items():
            self.assertTrue(doc["components"][name]["sha"].startswith(prefix), name)
            self.assertEqual(doc["components"][name]["source"], "candidate-identity")
        self.assertNotIn("exchange", json.dumps(doc["components"]).lower())
        pin = json.loads((self.tmp / "pin.json").read_text())
        self.assertEqual({n: c["sha"] for n, c in pin["components"].items()}, {n: c["sha"] for n, c in doc["components"].items()})

    def test_runtime_override_is_an_input_change_only(self):
        post_f3 = "1" * 40
        doc = self.run_resolve({"runtime": post_f3})
        self.assertEqual(doc["components"]["runtime"]["sha"], post_f3)
        self.assertEqual(doc["components"]["runtime"]["source"], "input-override")
        self.assertEqual(doc["overrides"], {"runtime": post_f3})
        for name in G.EXPECTED_COMPONENTS:
            if name != "runtime":
                self.assertEqual(doc["components"][name]["source"], "candidate-identity")

    def test_floating_or_short_values_are_refused(self):
        for bad in ("main", "ec728da6", "EC728DA6DC301A664B331AC8986AFD6E850A1273", "refs/heads/main", "1" * 39):
            with self.subTest(bad):
                with self.assertRaises(SystemExit):
                    self.run_resolve({"runtime": bad})

    def test_unknown_component_override_is_refused(self):
        with self.assertRaises(SystemExit):
            self.run_resolve({"exchange": "1" * 40})


if __name__ == "__main__":
    unittest.main()
