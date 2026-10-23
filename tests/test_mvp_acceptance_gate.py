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


RUN = "r" * 32
QSHA = "9" * 40


def junit(tests, overrides=None, drop=(), suite="mvp-acceptance-" + RUN):
    overrides = overrides or {}
    lines = [f'<?xml version="1.0"?><testsuites><testsuite name="{suite}">']
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
                                                            "identity_sha256": G.sha256_file(identity), "qualification_sha": QSHA, "run_id": RUN, "overrides": {}, "components": comps}))
        anchor = {"ref": "main", "files": {rel: {"main_blob": G.blob_id(ROOT / rel)} for rel in G.frozen_files(ROOT)}}
        (rd / "anchor.json").write_text(json.dumps(anchor))
        (rd / "mvp-chain/artifacts/ingress-modules.json").write_text(json.dumps(
            {"run_id": RUN, "modules": {"os": "/usr/lib/os.py", "tools.mvp_ingress.server": "/hub/tools/mvp_ingress/server.py"}, "sys_path": ["/hub"]}))
        rows = [{"id": t["row"], "status": (row_status or {}).get(t["row"], "PASS")} for t in BATTERY["tests"] if t["kind"] == "oracle_row"]
        v3 = BATTERY["oracle"]["unchanged_files_sha256"][BATTERY["oracle"]["expectations_in_force"]]
        (rd / "mvp-chain/results.json").write_text(json.dumps({"run_id": RUN, "expectations_sha256": v3, "rows": rows, "counts": {},
                                                               "tuple": {"heads": {n: c["sha"] for n, c in comps.items()}}}))
        vrun = {}
        for label, rep, code in (("A", report_a(), 3), ("B", report_b(), 3)):
            if verifier_mutate:
                rep, code = verifier_mutate(label, rep, code)
            raw = json.dumps(rep).encode()
            (rd / f"mvp-chain/artifacts/verifier/{label}-report.json").write_bytes(raw)
            vrun[label] = {"exit_code": code, "overall": "abstain" if code == 3 else "accept", "crashed": False, "report_sha256": hashlib.sha256(raw).hexdigest(),
                           "module_path": "/x/src/cognous_verify/__init__.py", "module_path_under_pin": True}
        (rd / "mvp-chain/observations.json").write_text(json.dumps({"run": {"run_id": RUN}, "env": {"python": "3.13.1 (main)", "pydantic_version": "2.13.5"}, "chain": {"verifier": vrun}}))
        for tag, inv in BATTERY["invocations"].items():
            tests = [t for t in BATTERY["tests"] if t["invocation"] == tag]
            (rd / inv["junit"]).write_text(junit(tests, junit_overrides, junit_drop))
            (rd / inv["collected"]).write_text("\n".join(f"{t['file']}::{t['test']}" for t in tests if t["id"] not in collect_drop) + "\n\n50 tests collected\n")
            (rd / inv["exit_file"]).write_text("0\n")
            (rd / inv["exclusion_observation"]).write_text(json.dumps(exclusion or {"run_id": RUN, "exchange_modules_loaded": [], "modules_from_exchange_paths": [], "sys_path_exchange_entries": []}))

    def verdict(self):
        doc = G.run_gate(self.run_dir, ROOT, QSHA)
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
        self.build(exclusion={"run_id": RUN, "exchange_modules_loaded": ["experiments.odex_gax_imx_reference"], "modules_from_exchange_paths": [], "sys_path_exchange_entries": []})
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


class ReviewFixTests(GateTests):
    """Independent review F1-F7."""

    def test_unknown_oracle_verdict_strings_are_never_a_pass(self):
        for status in ("KNOWN LIMITATION", "XFAIL", "pass", "", "SKIPPED"):
            with self.subTest(status):
                self.build(row_status={"NC4-01": status})
                v, checks, _ = self.verdict()
                self.assertEqual((v, checks["G-05"]), ("INCOMPLETE", "INCOMPLETE"))

    def test_oracle_fail_with_passing_junit_is_reject(self):
        self.build(row_status={"NC1-04": "FAIL"})
        v, checks, _ = self.verdict()
        self.assertEqual((v, checks["G-06"]), ("REJECT", "FAIL"))

    def _declared_root(self, entries):
        declared = copy.deepcopy(BATTERY)
        declared["declared_not_applicable"] = entries
        root = self.tmp / "rootd"
        shutil.rmtree(root, ignore_errors=True)
        shutil.copytree(ROOT / "process", root / "process")
        shutil.copytree(ROOT / "suites/v1-scenarios", root / "suites/v1-scenarios")
        (root / "process/mvp-acceptance/mandatory-battery.proposed.v1.json").write_text(json.dumps(declared))
        return root

    def test_declared_not_applicable_must_be_valid(self):
        self.build(row_status={"VER-03": "NOT APPLICABLE"})
        for entries in ([{"id": "VER-03", "justification": ""}], [{"id": "VER-03", "justification": "   "}], [{"id": "VER-03"}],
                        [{"id": "NOT-A-ROW", "justification": "x"}], ["VER-03"]):
            with self.subTest(entries):
                doc = G.run_gate(self.run_dir, self._declared_root(entries), QSHA)
                self.assertEqual(doc["verdict"], "INCOMPLETE")
                self.assertEqual({c["id"]: c["status"] for c in doc["checks"]}["G-03b"], "INCOMPLETE")
        ok = G.run_gate(self.run_dir, self._declared_root([{"id": "VER-03", "justification": "run B exited 0, nothing to attribute"}]), QSHA)
        self.assertEqual(ok["verdict"], "ACCEPT", [c for c in ok["checks"] if c["status"] != "PASS"])

    def test_malformed_verifier_reports_are_incomplete_and_a_verdict_is_still_written(self):
        for label, content in (("B", b"{not json"), ("A", b'{"summary": {}}'), ("B", b'{"checks": 5, "summary": {}}'), ("A", b'{"checks": [{}], "summary": {}}')):
            with self.subTest(label, content=content):
                self.build()
                path = self.run_dir / f"mvp-chain/artifacts/verifier/{label}-report.json"
                path.write_bytes(content)
                obs_path = self.run_dir / "mvp-chain/observations.json"
                obs = json.loads(obs_path.read_text())
                obs["chain"]["verifier"][label]["report_sha256"] = hashlib.sha256(content).hexdigest()
                obs_path.write_text(json.dumps(obs))
                v, checks, _ = self.verdict()
                self.assertEqual((v, checks["G-07"]), ("INCOMPLETE", "INCOMPLETE"))
        self.build()
        out = self.tmp / "verdict.json"
        (self.run_dir / "mvp-chain/artifacts/verifier/B-report.json").write_bytes(b"{not json")
        self.assertEqual(G.main(["gate", "--run-dir", str(self.run_dir), "--repo-root", str(ROOT), "--out", str(out)]), 2)
        self.assertEqual(json.loads(out.read_text())["verdict"], "INCOMPLETE")

    def test_unreadable_artifact_does_not_crash_the_gate(self):
        (self.run_dir / "mvp-chain/results.json").write_text("{")
        (self.run_dir / "junit-mvp-chain.xml").write_text("<not xml")
        self.assertEqual(self.verdict()[0], "INCOMPLETE")

    def test_exit_code_and_overall_are_rederived_from_the_retained_report(self):
        path = self.run_dir / "mvp-chain/observations.json"
        obs = json.loads(path.read_text())
        obs["chain"]["verifier"]["B"]["exit_code"] = 0  # claims accept; the retained report abstains
        path.write_text(json.dumps(obs))
        self.assertEqual(self.verdict()[1]["G-07"], "FAIL")

    def test_ingress_process_exchange_module_is_reject_and_missing_dump_is_incomplete(self):
        p = self.run_dir / "mvp-chain/artifacts/ingress-modules.json"
        p.write_text(json.dumps({"run_id": RUN, "modules": {"experiments.x": "/w/components/exchange/x.py"}, "sys_path": []}))
        self.assertEqual(self.verdict()[1]["G-08"], "FAIL")
        p.write_text(json.dumps({"run_id": RUN, "modules": {"ok": "/w/components/exchange/x.py"}, "sys_path": []}))
        self.assertEqual(self.verdict()[1]["G-08"], "FAIL")  # path pattern alone
        p.unlink()
        self.assertEqual(self.verdict()[1]["G-08"], "INCOMPLETE")

    def test_anchor_mismatch_is_reject_and_missing_anchor_is_incomplete(self):
        path = self.run_dir / "anchor.json"
        doc = json.loads(path.read_text())
        doc["files"]["suites/v1-scenarios/test_scn_d09.py"]["main_blob"] = "0" * 40
        path.write_text(json.dumps(doc))
        self.assertEqual(self.verdict()[1]["G-02c"], "FAIL")
        doc["files"]["suites/v1-scenarios/test_scn_d09.py"]["main_blob"] = None
        path.write_text(json.dumps(doc))
        self.assertEqual(self.verdict()[1]["G-02c"], "INCOMPLETE")
        path.unlink()
        self.assertEqual(self.verdict()[1]["G-02c"], "INCOMPLETE")

    def test_run_binding_and_qualification_sha(self):
        for victim in ("mvp-chain/results.json", "exchange-exclusion-applicability.json", "mvp-chain/artifacts/ingress-modules.json"):
            with self.subTest(victim):
                self.build()
                path = self.run_dir / victim
                doc = json.loads(path.read_text())
                doc["run_id"] = "stale"
                path.write_text(json.dumps(doc))
                self.assertEqual(self.verdict()[1]["G-10"], "INCOMPLETE")
        self.build()
        (self.run_dir / "junit-applicability.xml").write_text(junit([t for t in BATTERY["tests"] if t["invocation"] == "applicability"], suite="mvp-acceptance-old"))
        self.assertEqual(self.verdict()[1]["G-10"], "INCOMPLETE")
        self.build()
        self.assertEqual(G.run_gate(self.run_dir, ROOT, "8" * 40)["verdict"], "INCOMPLETE")

    def test_resolve_records_qualification_sha_and_run_id(self):
        tmp = Path(tempfile.mkdtemp(prefix="res-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        identity = ROOT / "process/mvp-acceptance/candidate-identity.inputs.json"
        doc = G.resolve(identity, {}, tmp / "p.json", tmp / "r.json", tmp / "o.txt", qualification_sha=QSHA, github_env=tmp / "e.txt")
        self.assertEqual(doc["qualification_sha"], QSHA)
        self.assertIn("MVP_RUN_ID=" + doc["run_id"], (tmp / "e.txt").read_text())
        self.assertIn("qualification=" + QSHA, (tmp / "o.txt").read_text())
        for bad in (None, "main", "9" * 39):
            with self.assertRaises(SystemExit):
                G.resolve(identity, {}, tmp / "p.json", tmp / "r.json", qualification_sha=bad)


class CheckoutAndProbeTests(unittest.TestCase):
    def test_verify_checkouts_detects_modified_untracked_and_ignored_files(self):
        import subprocess
        base = Path(tempfile.mkdtemp(prefix="vc-"))
        self.addCleanup(shutil.rmtree, base, True)
        def git(*a, cwd):
            return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()
        resolved = {"components": {}}
        for name, d in G.COMPONENT_DIRS.items():
            repo = base / "components" / d
            repo.mkdir(parents=True)
            git("init", "-q", cwd=repo)
            (repo / ".gitignore").write_text("ignored.txt\n")
            (repo / "f.txt").write_text("x")
            git("add", "-A", cwd=repo)
            git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "c", cwd=repo)
            resolved["components"][name] = {"sha": git("rev-parse", "HEAD", cwd=repo), "dir": f"components/{d}"}
        path = base / "resolved.json"
        path.write_text(json.dumps(resolved))
        G.verify_checkouts(path, base)  # clean: accepted
        for label, make in (("ignored", lambda r: (r / "ignored.txt").write_text("y")), ("untracked", lambda r: (r / "new.txt").write_text("y")),
                            ("modified", lambda r: (r / "f.txt").write_text("changed"))):
            with self.subTest(label):
                repo = base / "components/runtime"
                make(repo)
                path.write_text(json.dumps(resolved))
                with self.assertRaises(SystemExit):
                    G.verify_checkouts(path, base)
                for f in ("ignored.txt", "new.txt"):
                    (repo / f).unlink(missing_ok=True)
                (repo / "f.txt").write_text("x")

    def test_ingress_probe_writes_loaded_modules_at_exit(self):
        import os
        import subprocess
        out = Path(tempfile.mkdtemp(prefix="probe-")) / "m.json"
        self.addCleanup(shutil.rmtree, out.parent, True)
        probe = ROOT / "suites/mvp-applicability/plugin/ingress_probe"
        env = {**os.environ, "PYTHONPATH": str(probe), "MVP_INGRESS_MODULE_DUMP": str(out), "MVP_RUN_ID": "abc"}
        subprocess.run([sys.executable, "-c", "import json"], env=env, check=True)
        doc = json.loads(out.read_text())
        self.assertEqual(doc["run_id"], "abc")
        self.assertIn("json", doc["modules"])


class ResolveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="resolve-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.identity = ROOT / "process/mvp-acceptance/candidate-identity.inputs.json"

    def run_resolve(self, overrides=None):
        return G.resolve(self.identity, overrides or {}, self.tmp / "pin.json", self.tmp / "resolved.json", self.tmp / "out.txt", qualification_sha="9" * 40)

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
