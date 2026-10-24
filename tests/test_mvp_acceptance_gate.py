"""Gate semantics of tools/mvp_acceptance_gate.py (proposed): synthetic artifacts only, no component is run.

Each test builds a complete ACCEPT-able run directory from the real battery file, then damages exactly one thing and asserts the
verdict. A skipped, undiscovered, unexecuted or errored mandatory test is INCOMPLETE; a declared NOT APPLICABLE is accepted only when
listed; a Verifier disposition that is not exactly the expected one is a REJECT; frozen expectations are never changed to pass.
"""
import copy
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
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


PY = f"{sys.version_info[0]}.{sys.version_info[1]}"
ENV_PROFILE = json.loads((ROOT / "process/mvp-acceptance/environment-profile.proposed.v1.json").read_text())["hub_record"]


def make_root(dest: Path, mutate=None, real_pin=False) -> tuple[Path, str]:
    """A copy of the files the gate reads, with a freshly generated candidate commitment (so these tests do not depend on the committed hash)."""
    ignore = shutil.ignore_patterns("__pycache__")
    for rel in ("process", "suites/mvp-chain", "suites/mvp-applicability", "suites/v1-scenarios", "suites/operation-identity", "tools", ".github"):
        shutil.copytree(ROOT / rel, dest / rel, ignore=ignore, dirs_exist_ok=True, symlinks=True)
    shutil.copy(ROOT / "pytest.ini", dest / "pytest.ini")
    for f in (ROOT / "suites").iterdir():  # every file directly in suites/ is on sys.path and committed
        if f.is_file():
            shutil.copy(f, dest / "suites" / f.name)
    if not real_pin:
        pin_fake_script(dest)
    if mutate:
        mutate(dest)
    G.build_commitment(dest, dest / G.COMMITMENT_FILE)
    return dest, G.sha256_file(dest / G.COMMITMENT_FILE)


FAKE_SCRIPT = b"# stands in for the hub capture script in these synthetic runs\n"
FAKE_SCRIPT_SHA = hashlib.sha256(FAKE_SCRIPT).hexdigest()
FAKE_MANIFEST = b'{"manifest": "synthetic"}\n'
IDS = {"ingress_uid": 990, "ingress_gid": 990, "client_uid": 991, "client_gid": 991, "ipc_gid": 992}


def pin_fake_script(root):
    """Synthetic runs use a stand-in capture script; the pin in the (copied) profile is set to its sha so only the tests about the pin look at the real one."""
    p = root / G.ENV_PROFILE_FILE
    d = json.loads(p.read_text())
    d["hub_record"]["capture_script"]["sha256"] = FAKE_SCRIPT_SHA
    p.write_text(json.dumps(d, indent=2) + "\n")


def env_record(tuple_shas, mutate=None, ingress_sources=None, comps=None):
    checks = [{"id": i, "status": "PASS", "detail": "x", "data": {}} for i in ENV_PROFILE["required_pass_check_ids"]]
    man = ENV_PROFILE["manifest"]
    rec = {"schema": "mvp-ingress-env-record/1", "evidence_label": f"hosted-runner acceptance run {RUN}, profile=approved",
           "python": {"version": "3.13.1", "implementation": "CPython"}, "isolation_limits": {"yama_ptrace_scope": "1"},
           "ipc": {"connection_policy": {"socket_group_policy": "dedicated"}, "stat": {"path": "/run/ipc/ingress.sock", "type": "socket", "mode": "0660", "uid": IDS["ingress_uid"], "gid": IDS["ipc_gid"]}},
           "filesystem": {"state_dir": "/var/lib/ingress/state"},
           "process_identity": {"ingress_uid": IDS["ingress_uid"], "ingress_gid": IDS["ingress_gid"], "client_uid": IDS["client_uid"], "client_gid": IDS["client_gid"],
                                "ingress_process": {"uid": [IDS["ingress_uid"]] * 3}},
           "configuration": {"source_pins": {n: c["sha"] for n, c in (comps or {}).items()} or {f"c{i}": sha for i, sha in enumerate(sorted(tuple_shas))},
                             "ingress_source_sha256": ingress_sources or {},
                             "manifest_sha256": {pathlib_name(man["path"]): hashlib.sha256(FAKE_MANIFEST).hexdigest()}},
           "checks": checks, "overall": "PASS"}
    if mutate:
        mutate(rec)
    rec["record_sha256"] = G._record_digest(rec)
    return rec


def pathlib_name(rel):
    return rel.rsplit("/", 1)[-1]


class GateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="gate-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.run_dir = self.tmp / "run"
        self.root, self.commit = make_root(self.tmp / "root")
        self.build()

    def build(self, *, collect_drop=(), junit_overrides=None, junit_drop=(), row_status=None, verifier_mutate=None, exclusion=None, env_mutate=None, envelope_mutate=None, ingress_mutate=None, composite_mutate=None, no_record=False, script_on_hub=FAKE_SCRIPT):
        shutil.rmtree(self.run_dir, ignore_errors=True)
        rd = self.run_dir
        (rd / "mvp-chain/artifacts/verifier").mkdir(parents=True)
        identity = ROOT / "process/mvp-acceptance/candidate-identity.inputs.json"
        ident = json.loads(identity.read_text())
        comps = {n: {"repository": c["repository"], "sha": c["sha"], "source": "candidate-identity", "verified_head": c["sha"], "pristine": True}
                 for n, c in ident["components"].items()}
        cd = ident["composite"]
        verified = {"hub": {"revision": cd["hub"]["revision"], "git_tree_ids": dict(cd["hub"]["git_tree_ids"]), "launcher_entry_point_is_file": True,
                            "capture_script_sha256": cd["hub"]["capture_script_sha256"], "registry_catalogue_manifest_digest": cd["hub"]["registry_catalogue_manifest"]["digest"]},
                    "python": {"version": cd["python"]["version"], "lock_files_sha256": dict(cd["python"]["lock_files_sha256"])},
                    "environment_profile": {"sha256": cd["environment_profile"]["sha256"]}}
        if composite_mutate:
            composite_mutate(verified)
        (rd / "tuple-resolved.json").write_text(json.dumps({"identity_file": "process/mvp-acceptance/candidate-identity.inputs.json",
                                                            "identity_sha256": G.sha256_file(identity), "qualification_sha": QSHA, "run_id": RUN, "overrides": {}, "components": comps,
                                                            "composite_verified": verified}))
        anchor = {"ref": "main", "files": {rel: {"main_blob": G.blob_id(ROOT / rel)} for rel in G.frozen_files(ROOT)}}
        (rd / "anchor.json").write_text(json.dumps(anchor))
        hub = self.tmp / "components" / "hub" / "tools" / "mvp_ingress"
        hub.mkdir(parents=True, exist_ok=True)
        (hub / "server.py").write_text("print('x')\n")
        script = self.tmp / "components" / "hub" / ENV_PROFILE["capture_script"]["path"]
        script.parent.mkdir(parents=True, exist_ok=True)
        if script_on_hub is None:
            script.unlink(missing_ok=True)
        else:
            script.write_bytes(script_on_hub)
        man = self.tmp / "components" / "manifest" / ENV_PROFILE["manifest"]["path"]
        man.parent.mkdir(parents=True, exist_ok=True)
        man.write_bytes(FAKE_MANIFEST)
        sources = {"tools/mvp_ingress/server.py": G.sha256_file(hub / "server.py")}
        self.record_path = rd / "mvp-chain/artifacts/environment-record.json"
        self.envelope_path = rd / "mvp-chain/artifacts/environment-record.envelope.json"
        if not no_record:
            self.record_path.write_text(json.dumps(env_record({c["sha"] for c in comps.values()}, env_mutate, sources, comps)))
            envelope = {"schema": G.ENVELOPE_SCHEMA, "run_id": RUN, "qualification_sha": QSHA, "record_sha256": json.loads(self.record_path.read_text())["record_sha256"],
                        "record_file_sha256": G.sha256_file(self.record_path), "capture_script_sha256": FAKE_SCRIPT_SHA,
                        "environment_profile_sha256": G.sha256_file(self.root / G.ENV_PROFILE_FILE)}
            if envelope_mutate:
                envelope_mutate(envelope)
            self.envelope_path.write_text(json.dumps(envelope))
        self.ingress_obs = {"profile": "approved", "probe_ran": True, "ingress_is_root": False, **IDS}
        if ingress_mutate:
            ingress_mutate(self.ingress_obs)
        (rd / "mvp-chain/artifacts/ingress-modules.json").write_text(json.dumps(
            {"run_id": RUN, "modules": {"os": "/usr/lib/os.py", "tools.mvp_ingress.server": "/hub/tools/mvp_ingress/server.py"}, "sys_path": ["/hub"]}))
        rows = [{"id": t["row"], "status": (row_status or {}).get(t["row"], "PASS")} for t in BATTERY["tests"] if t["kind"] == "oracle_row"]
        v3 = BATTERY["oracle"]["unchanged_files_sha256"][BATTERY["oracle"]["expectations_in_force"]]  # the oracle in force (v6 in this proposal)
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
        (rd / "mvp-chain/observations.json").write_text(json.dumps({"run": {"run_id": RUN}, "env": {"python": "3.13.1 (main)", "pydantic_version": "2.13.5"}, "chain": {"verifier": vrun},
                                                                  "nc_unmediated": {"ingress": self.ingress_obs}}))
        for tag, inv in BATTERY["invocations"].items():
            tests = [t for t in BATTERY["tests"] if t["invocation"] == tag]
            (rd / inv["junit"]).write_text(junit(tests, junit_overrides, junit_drop))
            (rd / inv["collected"]).write_text("\n".join(f"{t['file']}::{t['test']}" for t in tests if t["id"] not in collect_drop) + "\n\n50 tests collected\n")
            (rd / inv["exit_file"]).write_text("0\n")
            (rd / inv["exclusion_observation"]).write_text(json.dumps(exclusion or {"run_id": RUN, "exchange_modules_loaded": [], "modules_from_exchange_paths": [], "sys_path_exchange_entries": []}))

    def gate(self, root=None, commit=None, **kw):
        args = {"expect_qualification": QSHA, "expect_commitment": (self.commit if root is None else None) if commit is None else commit, "require_python": PY,
                "components_dir": self.tmp / "components"}
        args.update(kw)
        return G.run_gate(self.run_dir, root or self.root, **args)

    def verdict(self):
        doc = self.gate()
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
        root, commit = make_root(self.tmp / "rootx", lambda r: (r / "process/mvp-acceptance/mandatory-battery.proposed.v1.json").write_text(json.dumps(declared)))
        self.assertEqual(self.gate(root, commit)["verdict"], "ACCEPT")

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
        def edit(r):
            t = r / "process/mvp-chain/expectations.proposed.v3.json"
            t.write_text(t.read_text().replace('"mandatory": true', '"mandatory": true ', 1))
        root, commit = make_root(self.tmp / "root2", edit)
        doc = self.gate(root, commit)
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
        shutil.rmtree(self.tmp / "rootd", ignore_errors=True)
        return make_root(self.tmp / "rootd", lambda r: (r / "process/mvp-acceptance/mandatory-battery.proposed.v1.json").write_text(json.dumps(declared)))

    def test_declared_not_applicable_must_be_valid(self):
        self.build(row_status={"VER-03": "NOT APPLICABLE"})
        for entries in ([{"id": "VER-03", "justification": ""}], [{"id": "VER-03", "justification": "   "}], [{"id": "VER-03"}],
                        [{"id": "NOT-A-ROW", "justification": "x"}], ["VER-03"]):
            with self.subTest(entries):
                doc = self.gate(*self._declared_root(entries))
                self.assertEqual(doc["verdict"], "INCOMPLETE")
                self.assertEqual({c["id"]: c["status"] for c in doc["checks"]}["G-03b"], "INCOMPLETE")
        ok = self.gate(*self._declared_root([{"id": "VER-03", "justification": "run B exited 0, nothing to attribute"}]))
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
        self.assertEqual(G.main(["gate", "--run-dir", str(self.run_dir), "--repo-root", str(self.root), "--out", str(out),
                                 "--expect-commitment-sha256", self.commit, "--require-python", PY,
                                 "--components-dir", str(self.tmp / "components")]), 2)
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
        self.assertEqual(self.gate(expect_qualification="8" * 40)["verdict"], "INCOMPLETE")

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


class RulingsTwoTests(GateTests):
    """Architect rulings #2 item 6: commitment, environment record, Python 3.13, pending NC4-03 placeholder."""

    def test_committed_candidate_matches_the_files_in_this_repository(self):
        doc = json.loads((ROOT / G.COMMITMENT_FILE).read_text())
        self.assertEqual(sorted(doc["files"]), G.commit_files(ROOT))
        for rel, digest in doc["files"].items():
            self.assertEqual(G.sha256_file(ROOT / rel), digest, f"{rel} changed: regenerate the commitment as a NEW versioned candidate (python tools/mvp_acceptance_gate.py commit)")
        self.assertIn("PROPOSED", doc["status"])
        self.assertEqual(doc["candidate_version"], f"mvp-qualification-candidate-v{G.COMMITMENT_VERSION}")
        self.assertEqual(G.COMMITMENT_VERSION, 4)

    def test_commitment_requires_an_independent_hash_and_detects_any_change(self):
        self.assertEqual({c["id"]: c["status"] for c in self.gate(commit="")["checks"]}["G-12"], "INCOMPLETE")
        self.assertEqual({c["id"]: c["status"] for c in self.gate(commit="0" * 64)["checks"]}["G-12"], "FAIL")
        t = self.root / "suites/mvp-chain/test_ruling4_lost_ack.py"
        t.write_text(t.read_text() + "\n# edited after commitment\n")
        doc = self.gate()
        self.assertEqual({c["id"]: c["status"] for c in doc["checks"]}["G-12"], "FAIL")
        self.assertNotEqual(doc["verdict"], "ACCEPT")

    def test_an_uncommitted_new_mandatory_test_file_is_refused(self):
        (self.root / "suites/mvp-chain/test_new_mandatory.py").write_text("def test_x():\n    pass\n")
        c = {c["id"]: c for c in self.gate()["checks"]}["G-12"]
        self.assertEqual(c["status"], "FAIL")
        self.assertIn("not committed", c["detail"])

    def test_an_uncommitted_collected_test_is_incomplete(self):
        path = self.run_dir / "collected-mvp-chain.txt"
        path.write_text(path.read_text() + "suites/mvp-chain/test_mvp_chain.py::test_surprise\n")
        self.assertEqual(self.verdict()[1]["G-13"], "INCOMPLETE")

    def test_environment_record_must_be_pass_on_the_selected_profile(self):
        def set_check(cid, status):
            def m(rec):
                next(c for c in rec["checks"] if c["id"] == cid)["status"] = status
                rec["overall"] = "FAIL" if status == "FAIL" else "BLOCKED"
            return m
        cases = [("BLOCKED", set_check("isolation.ptrace_scope", "BLOCKED"), "INCOMPLETE"),
                 ("yama absent", lambda r: (r["isolation_limits"].update(yama_ptrace_scope=None), set_check("isolation.ptrace_scope", "BLOCKED")(r)), "INCOMPLETE"),
                 ("FAIL", set_check("identity.ingress_not_root", "FAIL"), "FAIL"),
                 ("python 3.12", lambda r: r["python"].update(version="3.12.7"), "FAIL"),
                 ("scope 0", lambda r: r["isolation_limits"].update(yama_ptrace_scope="0"), "FAIL"),
                 ("missing check", lambda r: r["checks"].pop(), "INCOMPLETE"),
                 ("relaxed", lambda r: r["checks"][0].update(data={"relaxed": True}), "FAIL"),
                 ("other tuple", lambda r: r["configuration"]["source_pins"].update(x="e" * 40), "FAIL"),
                 ("no pins", lambda r: r["configuration"].update(source_pins={}), "INCOMPLETE"),
                 ("wrong schema", lambda r: r.update(schema="other/1"), "FAIL")]
        for label, mut, want in cases:
            with self.subTest(label):
                self.build(env_mutate=mut)
                v, checks, _ = self.verdict()
                self.assertEqual(checks["G-11"], want)
                self.assertNotEqual(v, "ACCEPT")

    def test_edited_environment_record_is_refused_and_missing_is_incomplete(self):
        path = self.record_path
        rec = json.loads(path.read_text())
        rec["python"]["version"] = "3.13.9"  # edited without re-hashing
        path.write_text(json.dumps(rec))
        self.assertEqual(self.verdict()[1]["G-11"], "FAIL")
        path.unlink()
        self.assertEqual(self.verdict()[1]["G-11"], "INCOMPLETE")

    def _g12(self, doc=None):
        return {c["id"]: c for c in (doc or self.gate())["checks"]}["G-12"]

    def test_transitive_imports_config_locks_and_all_suite_files_are_committed(self):
        files = G.commit_files(ROOT)
        for needed in ("suites/operation-identity/_oi_flow.py", "tools/pristine_checkout.py", "pytest.ini",
                       ".github/locks/cryptography-pydantic-pytest-a9a750.txt", ".github/locks/cryptography-pydantic-pytest-a9a750.in",
                       "suites/mvp-chain/README.md", "suites/mvp-chain/_chain.py", "process/mvp-chain/expectations.proposed.v3.json"):
            self.assertIn(needed, files)

    def test_tampering_with_each_reviewer_case_is_a_g12_fail(self):
        def tamper(label, fn):
            with self.subTest(label):
                shutil.rmtree(self.tmp / "t", ignore_errors=True)
                root, commit = make_root(self.tmp / "t")
                self.assertEqual(self._g12(self.gate(root, commit))["status"], "PASS")
                fn(root)
                c = self._g12(self.gate(root, commit))
                self.assertEqual(c["status"], "FAIL", c["detail"])
        def append(rel):
            return lambda r: (r / rel).write_text((r / rel).read_text() + "\n# tampered\n")
        tamper("_oi_flow.py", append("suites/operation-identity/_oi_flow.py"))
        tamper("pristine_checkout.py", append("tools/pristine_checkout.py"))
        tamper("pytest.ini addopts", lambda r: (r / "pytest.ini").write_text((r / "pytest.ini").read_text() + "addopts = -k 'not NC1'\n"))
        tamper("non-py file under suite", lambda r: (r / "suites/mvp-chain/extra.txt").write_text("x"))
        tamper("lock file", append(".github/locks/cryptography-pydantic-pytest-a9a750.txt"))
        tamper("lock .in file", append(".github/locks/cryptography-pydantic-pytest-a9a750.in"))
        tamper("root conftest planted", lambda r: (r / "conftest.py").write_text("collect_ignore_glob = ['*']\n"))
        tamper("suites conftest planted", lambda r: (r / "suites/conftest.py").write_text("x = 1\n"))
        def symlink_dir(r):
            (r / "elsewhere").mkdir()
            (r / "elsewhere/test_x.py").write_text("def test_x():\n    pass\n")
            (r / "suites/mvp-chain/linked").symlink_to(r / "elsewhere", target_is_directory=True)
        tamper("symlinked directory of .py files", symlink_dir)
        def symlink_file(r):
            (r / "suites/mvp-chain/verdict.py").rename(r / "verdict_real.py")
            (r / "suites/mvp-chain/verdict.py").symlink_to(r / "verdict_real.py")
        tamper("committed file replaced by a symlink", symlink_file)
        def symlink_ancestor(r):
            shutil.move(str(r / "suites/operation-identity"), str(r / "oi_real"))
            (r / "suites/operation-identity").symlink_to(r / "oi_real", target_is_directory=True)
        tamper("committed ancestor directory replaced by a symlink", symlink_ancestor)

    def test_every_file_directly_in_a_sys_path_directory_is_committed(self):
        committed = set(json.loads((ROOT / G.COMMITMENT_FILE).read_text())["files"])
        for rel in ("suites", "suites/operation-identity", "tools"):
            for f in sorted((ROOT / rel).iterdir()):
                if f.is_file():
                    self.assertIn(f"{rel}/{f.name}", committed, f"{rel}/{f.name} is on sys.path and must be committed")
        for f in sorted(ROOT.iterdir()):  # the repository root is first on sys.path under ``python -m pytest``: every importable file and package __init__
            if f.is_file() and f.name.endswith(G.IMPORTABLE_SUFFIXES):
                self.assertIn(f.name, committed)
            if f.is_dir() and (f / "__init__.py").exists():
                self.assertIn(f"{f.name}/__init__.py", committed)
        self.assertEqual(set(G.syspath_entries(ROOT)) - committed, set())

    def test_a_planted_shadow_module_on_sys_path_is_a_g12_fail(self):
        plants = {"tools/yaml.py": "x = 1\n", "suites/jsonschema.py": "x = 1\n", "suites/operation-identity/pydantic.py": "x = 1\n", "sitecustomize.py": "x = 1\n",
                  "usercustomize.py": "x = 1\n", "tools/shadow.pth": "/tmp\n", "suites/pkg/__init__.py": "x = 1\n", "tools/pkg/__init__.py": "x = 1\n",
                  "tools/native.cpython-313-x86_64-linux-gnu.so": "x", "yaml.pyc": "x", "suites/data.txt": "any file directly in suites/", "tools/notes.md": "any file directly in tools/",
                  "suites/operation-identity/notes.md": "any file directly in suites/operation-identity/"}
        for rel, content in plants.items():
            with self.subTest(rel):
                shutil.rmtree(self.tmp / "p", ignore_errors=True)
                root, commit = make_root(self.tmp / "p")
                self.assertEqual(self._g12(self.gate(root, commit))["status"], "PASS")
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_text(content)
                c = self._g12(self.gate(root, commit))
                self.assertEqual(c["status"], "FAIL", c["detail"])
                self.assertIn("not committed", c["detail"])
        with self.subTest("symlink planted"):
            shutil.rmtree(self.tmp / "p", ignore_errors=True)
            root, commit = make_root(self.tmp / "p")
            (root / "tools/yaml.py").symlink_to(root / "tools/pristine_checkout.py")
            self.assertEqual(self._g12(self.gate(root, commit))["status"], "FAIL")
        with self.subTest("edited committed module"):
            shutil.rmtree(self.tmp / "p", ignore_errors=True)
            root, commit = make_root(self.tmp / "p")
            (root / "suites/_pins.py").write_text((root / "suites/_pins.py").read_text() + "\n# shadow\n")
            self.assertEqual(self._g12(self.gate(root, commit))["status"], "FAIL")
        with self.subTest("a directory that is not on sys.path is not part of the set"):
            shutil.rmtree(self.tmp / "p", ignore_errors=True)
            root, commit = make_root(self.tmp / "p")
            (root / "docs").mkdir(exist_ok=True)
            (root / "docs/unrelated.py").write_text("x = 1\n")
            self.assertEqual(self._g12(self.gate(root, commit))["status"], "PASS")

    def test_build_commitment_refuses_symlinks(self):
        root, _ = make_root(self.tmp / "ts")
        (root / "suites/mvp-chain/ln.py").symlink_to(root / "suites/mvp-chain/verdict.py")
        with self.assertRaises(SystemExit):
            G.build_commitment(root, root / "c.json")

    def g11(self, **kw):
        doc = self.gate(**kw)
        return {c["id"]: c for c in doc["checks"]}["G-11"]

    def test_environment_record_file_replaced_symlinked_or_unbound_is_refused(self):
        self.assertEqual(self.g11()["status"], "PASS")
        # no envelope: the record cannot be bound to the run
        self.envelope_path.unlink()
        self.assertEqual(self.g11()["status"], "INCOMPLETE")
        # the record file replaced after capture (the envelope pins its file hash)
        self.build()
        rec = json.loads(self.record_path.read_text())
        rec["python"]["version"] = "3.13.9"
        rec["record_sha256"] = G._record_digest(rec)
        self.record_path.write_text(json.dumps(rec))
        self.assertEqual(self.g11()["status"], "FAIL")
        # symbolic link
        self.build()
        real = self.tmp / "real-record.json"
        shutil.copy(self.record_path, real)
        self.record_path.unlink()
        self.record_path.symlink_to(real)
        self.assertEqual(self.g11()["status"], "FAIL")

    def test_run_binding_lives_in_the_envelope_not_in_a_committed_record(self):
        for label, mut, want in (("run_id absent", lambda e: e.pop("run_id"), "INCOMPLETE"), ("run_id other", lambda e: e.update(run_id="other"), "FAIL"),
                                 ("qualification_sha absent", lambda e: e.pop("qualification_sha"), "INCOMPLETE"),
                                 ("qualification_sha other", lambda e: e.update(qualification_sha="1" * 40), "FAIL"),
                                 ("record hash other", lambda e: e.update(record_sha256="0" * 64), "FAIL"),
                                 ("record file hash other", lambda e: e.update(record_file_sha256="0" * 64), "FAIL"),
                                 ("profile hash other", lambda e: e.update(environment_profile_sha256="0" * 64), "FAIL"),
                                 ("schema other", lambda e: e.update(schema="x/1"), "FAIL")):
            with self.subTest(label):
                self.build(envelope_mutate=mut)
                self.assertEqual(self.g11()["status"], want, self.g11()["detail"])
        self.build()
        self.assertEqual(self.g11()["status"], "PASS")

    def test_capture_script_is_pinned_in_the_profile_and_at_the_tuple_hub_sha(self):
        real_pin = ENV_PROFILE["capture_script"]
        self.assertRegex(real_pin["sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(real_pin["path"], "tools/mvp_env_record/capture_env_record.py")
        self.assertEqual(real_pin["forbidden_paths"], ["tools/mvp_ingress/capture_env_record.py"])
        self.assertIn("3fff3dfb0fb909774cdae77557689dde4cb90f12", real_pin["hub_pr"])
        self.assertIn("050dcd670ff23faf0a5e33d3bd6cb0db5e65c74e", real_pin["hub_pr"])
        self.assertEqual(real_pin["sha256"], "faf8f26117b9e0d4616528250b97099c037117fd5df60c7032ac8347464af461")
        self.assertIn("0e2b52a0", real_pin["hub_pr"])
        self.assertIn("bytes identical to the approved 050dcd67", real_pin["hub_pr"].replace("050dcd670ff23faf0a5e33d3bd6cb0db5e65c74e", "050dcd67"))
        # the envelope names a script other than the pinned one
        self.build(envelope_mutate=lambda e: e.update(capture_script_sha256="a" * 64))
        c = self.g11()
        self.assertEqual(c["status"], "FAIL")
        self.assertIn("not the pinned", c["detail"])
        # the hub checkout at the tuple sha holds a different script than the pin (a moved #219 is a new candidate)
        self.build(script_on_hub=b"# a later revision of the capture script\n")
        c = self.g11()
        self.assertEqual(c["status"], "FAIL")
        self.assertIn("differs from the pinned sha256", c["detail"])
        # the tuple's hub sha predates the script
        self.build(script_on_hub=None, env_mutate=None)
        c = self.g11()
        self.assertEqual(c["status"], "INCOMPLETE")
        self.assertIn("predates the capture script", c["detail"])
        # and with the REAL pin (not the stand-in) the stand-in script is refused
        real_root, real_commit = make_root(self.tmp / "realpin", real_pin=True)
        self.build()
        self.assertEqual({c["id"]: c for c in self.gate(real_root, real_commit)["checks"]}["G-11"]["status"], "FAIL")

    def test_developer_optout_and_unrecorded_profile_are_incomplete_never_a_pass(self):
        self.build(ingress_mutate=lambda o: o.update(profile="developer-optout"))
        c = self.g11()
        self.assertEqual(c["status"], "INCOMPLETE")
        self.assertIn("developer opt-out", c["detail"])
        self.assertNotEqual(self.verdict()[0], "ACCEPT")
        self.build(ingress_mutate=lambda o: o.pop("profile"))
        self.assertEqual(self.g11()["status"], "INCOMPLETE")
        # opt-out takes precedence even though a record happens to exist
        self.build(no_record=True, ingress_mutate=lambda o: o.update(profile="developer-optout"))
        self.assertEqual(self.g11()["status"], "INCOMPLETE")
        self.build(no_record=True)
        self.assertEqual(self.g11()["status"], "INCOMPLETE")

    def test_identities_in_the_record_are_the_ones_the_suite_observed(self):
        for key in IDS:
            with self.subTest(key):
                self.build(ingress_mutate=lambda o, k=key: o.update({k: o[k] + 1000}))
                c = self.g11()
                self.assertEqual(c["status"], "FAIL")
                self.assertIn(f"identity {key}", c["detail"])
            with self.subTest(key + " not observed"):
                self.build(ingress_mutate=lambda o, k=key: o.pop(k))
                self.assertEqual(self.g11()["status"], "INCOMPLETE")
        self.build(ingress_mutate=lambda o: o.update(ingress_is_root=True))
        self.assertEqual(self.g11()["status"], "FAIL")
        self.build(ingress_mutate=lambda o: o.pop("ingress_is_root"))
        self.assertEqual(self.g11()["status"], "FAIL")

    def test_evidence_label_is_required_and_bound_to_this_run(self):
        self.assertIn("capture.evidence_label", ENV_PROFILE["required_pass_check_ids"])
        self.build(env_mutate=lambda r: r.pop("evidence_label"))
        self.assertEqual(self.g11()["status"], "INCOMPLETE")
        self.build(env_mutate=lambda r: r.update(evidence_label="  "))
        self.assertEqual(self.g11()["status"], "INCOMPLETE")
        self.build(env_mutate=lambda r: r.update(evidence_label="hosted-runner acceptance run other, profile=approved"))
        self.assertEqual(self.g11()["status"], "FAIL")
        self.build(env_mutate=lambda r: r.update(evidence_label=f"development container run {RUN}"))
        self.assertEqual(self.g11()["status"], "FAIL")
        def blocked(r):
            next(c for c in r["checks"] if c["id"] == "capture.evidence_label")["status"] = "BLOCKED"
            r["overall"] = "BLOCKED"
        self.build(env_mutate=blocked)
        self.assertEqual(self.g11()["status"], "INCOMPLETE")

    def test_outsider_must_be_denied_at_the_socket_not_at_the_ipc_directory(self):
        self.assertEqual(ENV_PROFILE["optional_informational_check_ids"], ["qualification.outsider_denied_by_ipc_directory"])
        def only_directory(r):  # what the hub script emits when the outsider cannot traverse the IPC directory
            next(c for c in r["checks"] if c["id"] == "qualification.outsider_denied_socket")["status"] = "BLOCKED"
            r["checks"].append({"id": "qualification.outsider_denied_by_ipc_directory", "status": "PASS", "detail": "x", "data": {}})
            r["overall"] = "BLOCKED"
        self.build(env_mutate=only_directory)
        c = self.g11()
        self.assertEqual(c["status"], "INCOMPLETE")
        self.assertIn("qualification.outsider_denied_socket", c["detail"])
        def socket_fail(r):
            next(c for c in r["checks"] if c["id"] == "qualification.outsider_denied_socket")["status"] = "FAIL"
            r["overall"] = "FAIL"
        self.build(env_mutate=socket_fail)
        self.assertEqual(self.g11()["status"], "FAIL")
        def info_only(r):  # the informational id is optional and never a problem by itself
            r["checks"].append({"id": "qualification.outsider_denied_by_ipc_directory", "status": "PASS", "detail": "x", "data": {}})
        self.build(env_mutate=info_only)
        self.assertEqual(self.g11()["status"], "PASS")
        self.build()
        self.assertEqual(self.g11()["status"], "PASS")

    def test_ipc_directory_is_traversable_by_others_but_never_listable_or_writable(self):
        src = (ROOT / "suites/mvp-chain/_ingress.py").read_text()
        self.assertIn("0o2751", src)
        self.assertNotIn("0o2750", src)
        mode = 0o2751
        self.assertEqual(mode & 0o022, 0)  # the hub check refuses only group/other WRITE
        self.assertEqual(mode & 0o004, 0)  # others cannot list
        self.assertTrue(mode & 0o001)      # others can traverse: the denial is on the 0660 socket itself
        self.assertEqual(ENV_PROFILE["ipc"]["directory_mode"], "2751")
        self.assertEqual(ENV_PROFILE["ipc"]["socket_mode"], "0660")

    def test_g11_fails_when_the_script_is_also_carried_inside_the_ingress_package(self):
        self.build()
        self.assertEqual(self.g11()["status"], "PASS")
        old = self.tmp / "components/hub/tools/mvp_ingress/capture_env_record.py"
        old.write_bytes(FAKE_SCRIPT)
        c = self.g11()
        self.assertEqual(c["status"], "FAIL")
        self.assertIn("inside the ingress package", c["detail"])

    def test_component_pins_and_manifest_are_the_tuples(self):
        def pin(name, value):
            return lambda r: r["configuration"]["source_pins"].update({name: value}) if value else r["configuration"]["source_pins"].pop(name)
        self.build(env_mutate=pin("runtime", "d" * 40))
        self.assertEqual(self.g11()["status"], "FAIL")
        self.build(env_mutate=pin("control_plane", None))
        self.assertEqual(self.g11()["status"], "INCOMPLETE")
        self.build(env_mutate=lambda r: r["configuration"].update(manifest_sha256={"refund_integration_v1_1.manifest.json": "0" * 64}))
        self.assertEqual(self.g11()["status"], "FAIL")
        self.build(env_mutate=lambda r: r["configuration"].pop("manifest_sha256"))
        self.assertEqual(self.g11()["status"], "INCOMPLETE")

    HUB_EMITTED_IDS = (  # every check id the hub capture script (PR #219 hub 3fff3dfb, script bytes identical to 050dcd67) always emits when the inputs are given; the *.exception and *_present ids are BLOCKED markers emitted only on failure
        "capture.evidence_label", "configuration.journal_mode", "configuration.pins_and_manifests", "filesystem.ancestors_not_writable_by_others", "filesystem.no_acl_entries",
        "filesystem.no_extra_group_access", "filesystem.state_tree_owner_only", "identity.client_distinct_unprivileged", "identity.declared",
        "identity.ingress_command", "identity.ingress_not_root", "identity.ingress_process", "invocation.client_entry_point",
        "invocation.operation_identity_fixed_true", "invocation.simulate_fixed_none", "ipc.directory_separate_and_protected", "ipc.peer_credentials",
        "ipc.socket_mode_owner_group", "isolation.ingress_capabilities", "isolation.ingress_dumpability", "isolation.ptrace_scope", "platform.linux",
        "platform.fs_enforces_unix_perms.socket_dir", "platform.fs_enforces_unix_perms.state_dir",
        "python.interpreter_matches_ingress", "python.profile", "qualification.client_capabilities_empty", "qualification.client_denied_ingress_process",
        "qualification.client_denied_state_access", "qualification.client_socket_reachable", "qualification.outsider_denied_socket")

    def test_required_ids_equal_the_ids_the_hub_script_emits(self):
        self.assertEqual(sorted(ENV_PROFILE["required_pass_check_ids"]), sorted(self.HUB_EMITTED_IDS))
        for stale in ("ipc.socket_mode_owner", "isolation.ingress_capabilities_recorded"):  # names the hub does not emit (they made the gate unsatisfiable)
            self.assertNotIn(stale, ENV_PROFILE["required_pass_check_ids"])

    def test_every_hub_emitted_check_id_is_required(self):
        for needed in self.HUB_EMITTED_IDS:
            with self.subTest(needed):
                self.build(env_mutate=lambda r, n=needed: r["checks"].remove(next(c for c in r["checks"] if c["id"] == n)))
                self.assertEqual(self.verdict()[1]["G-11"], "INCOMPLETE")
        for needed in ("ipc.directory_separate_and_protected", "qualification.outsider_denied_socket"):
            with self.subTest("not PASS " + needed):
                self.build(env_mutate=lambda r, n=needed: (next(c for c in r["checks"] if c["id"] == n).update(status="FAIL"), r.update(overall="FAIL")))
                self.assertEqual(self.verdict()[1]["G-11"], "FAIL")

    def test_environment_record_bound_to_run_sources_interpreter_and_ipc(self):
        def setp(path, value):
            def m(rec):
                node = rec
                for k in path[:-1]:
                    node = node[k]
                if value is KeyError:
                    node.pop(path[-1], None)
                else:
                    node[path[-1]] = value
            return m
        cases = [("interpreter differs", setp(["python", "version"], "3.13.9"), "FAIL"),
                 ("sources absent", setp(["configuration", "ingress_source_sha256"], KeyError), "INCOMPLETE"),
                 ("sources differ", setp(["configuration", "ingress_source_sha256"], {"tools/mvp_ingress/server.py": "0" * 64}), "FAIL"),
                 ("group policy absent", setp(["ipc", "connection_policy"], KeyError), "INCOMPLETE"),
                 ("group policy shared", setp(["ipc", "connection_policy", "socket_group_policy"], "shared"), "FAIL"),
                 ("socket mode 0600", setp(["ipc", "stat", "mode"], "0600"), "FAIL"),
                 ("socket mode absent", setp(["ipc", "stat"], KeyError), "INCOMPLETE"),
                 ("socket inside state dir", setp(["ipc", "stat", "path"], "/var/lib/ingress/state/ingress.sock"), "FAIL"),
                 ("ingress uid absent", setp(["process_identity", "ingress_uid"], KeyError), "INCOMPLETE"),
                 ("ingress root", setp(["process_identity", "ingress_uid"], 0), "FAIL")]
        for label, mut, want in cases:
            if label == "ingress root":  # the suite's observation then disagrees with the record too: still a FAIL
                pass
        for label, mut, want in cases:
            with self.subTest(label):
                self.build(env_mutate=mut)
                self.assertEqual(self.verdict()[1]["G-11"], want)
        self.build()
        self.assertEqual({c["id"]: c["status"] for c in self.gate(components_dir=None)["checks"]}["G-11"], "INCOMPLETE")

    def test_gate_interpreter_must_be_the_required_python(self):
        self.assertEqual({c["id"]: c["status"] for c in self.gate(require_python="3.12" if PY != "3.12" else "3.13")["checks"]}["G-04b"], "INCOMPLETE")
        self.assertEqual({c["id"]: c["status"] for c in self.gate(require_python=None)["checks"]}["G-04b"], "INCOMPLETE")

    def test_nc4_03_origin_rule_placeholder_holds_no_rows(self):
        battery = json.loads((ROOT / "process/mvp-acceptance/mandatory-battery.proposed.v1.json").read_text())
        (placeholder,) = battery["pending_rows"]
        self.assertEqual(placeholder["rows"], [])
        self.assertIn("PLACEHOLDER", placeholder["status"])
        bad = copy.deepcopy(battery)
        bad["pending_rows"][0]["rows"] = [{"id": "NC4-03-ORIGIN-01"}]
        root, commit = make_root(self.tmp / "rootp", lambda r: (r / "process/mvp-acceptance/mandatory-battery.proposed.v1.json").write_text(json.dumps(bad)))
        self.assertEqual({c["id"]: c["status"] for c in self.gate(root, commit)["checks"]}["G-14"], "INCOMPLETE")


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
        short = {"control_plane": "7a4bcd40", "runtime": "c5e97e87", "replay": "40012b8c", "evidence_pack": "7b9511f2", "odes": "1a5e1d30",
                 "verifier": "c0b8ba1f", "action_manifest": "fa170815", "hub": "330ccc31"}  # final PROVISIONAL, UNQUALIFIED tuple
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


class IngressProfileTests(unittest.TestCase):
    """suites/mvp-chain/_ingress.py: the approved profile is explicit, never silently weaker."""

    def setUp(self):
        sys.path.insert(0, str(ROOT / "suites/mvp-chain"))
        self.addCleanup(sys.path.remove, str(ROOT / "suites/mvp-chain"))
        for m in ("_ingress", "_state"):
            sys.modules.pop(m, None)
        import _ingress, _state  # noqa: E401
        self.I, self.S = _ingress, _state
        self.tmp = Path(tempfile.mkdtemp(prefix="ingress-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.addCleanup(lambda: [sys.modules.pop(m, None) for m in ("_ingress", "_state")])

    def env(self, **kw):
        import os
        from unittest import mock
        return mock.patch.dict(os.environ, kw, clear=False)

    def test_unknown_profile_is_blocked(self):
        with self.env(MVP_INGRESS_PROFILE="whatever"):
            out = self.I.run(self.tmp)
        self.assertEqual(out["status"], "blocked")
        self.assertFalse(out["ingress"]["probe_ran"])

    def test_default_profile_is_approved_and_optout_is_explicit_and_recorded(self):
        import os
        self.S.ENV["dirs"].pop("hub", None)
        with self.env():
            os.environ.pop("MVP_INGRESS_PROFILE", None)
            self.assertEqual(self.I.run(self.tmp)["ingress"]["profile"], "approved")
        with self.env(MVP_INGRESS_PROFILE="developer-optout"):
            self.assertEqual(self.I.run(self.tmp)["ingress"]["profile"], "developer-optout")

    def test_identities_must_be_named_exist_and_be_dedicated(self):
        import os
        for k in ("MVP_INGRESS_USER", "MVP_CLIENT_USER", "MVP_IPC_GROUP"):
            os.environ.pop(k, None)
        with self.assertRaises(self.I.ProfileBlocked) as cm:
            self.I._identities()
        self.assertIn("developer-optout", str(cm.exception))
        with self.env(MVP_INGRESS_USER="no-such-user-xyz", MVP_CLIENT_USER="root", MVP_IPC_GROUP="root"):
            with self.assertRaises(self.I.ProfileBlocked):
                self.I._identities()
        with self.env(MVP_INGRESS_USER="root", MVP_CLIENT_USER="root", MVP_IPC_GROUP="root"):
            with self.assertRaises(self.I.ProfileBlocked) as cm:
                self.I._identities()
            self.assertIn("non-root", str(cm.exception))

    def test_workflow_provisions_the_profile_and_no_longer_takes_a_precommitted_record(self):
        wf = (ROOT / ".github/workflows/mvp-acceptance.yml").read_text()
        for needed in ("sysctl -w kernel.yama.ptrace_scope=1", "MVP_INGRESS_PROFILE=approved", "MVP_INGRESS_USER=mvp-ingress", "MVP_CLIENT_USER=mvp-client",
                       "MVP_IPC_GROUP=mvp-ipc", "MVP_QUALIFICATION_SHA=", "useradd", "groupadd --system mvp-ipc"):
            self.assertIn(needed, wf)
        for gone in ("environment_record_sha256", "inputs.environment_record", "expect-environment-record-sha256", "--socket-mode 666"):
            self.assertNotIn(gone, wf)
        self.assertNotIn("developer-optout", wf)
        src = (ROOT / "suites/mvp-chain/_ingress.py").read_text()
        self.assertIn('"666" if optout else "660"', src)
        self.assertNotIn("--socket-mode\", \"666\"]", src)

    def test_capture_binds_the_record_to_the_run_in_an_envelope_and_leaves_the_record_intact(self):
        import os
        hub = self.tmp / "hub"
        (hub / "tools/mvp_ingress").mkdir(parents=True)
        (hub / "tools/mvp_env_record").mkdir(parents=True)
        (hub / "tools/mvp_ingress/server.py").write_text("x = 1\n")
        (hub / "tools/mvp_env_record/capture_env_record.py").write_text(
            "import json, sys\nout = sys.argv[sys.argv.index('--out') + 1]\nrec = {'schema': 'mvp-ingress-env-record/1', 'overall': 'PASS', 'record_sha256': 'f' * 64, 'argv': sys.argv[1:]}\n"
            "open(out, 'w').write(json.dumps(rec, sort_keys=True))\nsys.exit(0)\n")
        man = self.tmp / "manifest"
        (man / "examples").mkdir(parents=True)
        (man / "examples/refund_integration_v1_1.manifest.json").write_text("{}")
        self.S.ENV["dirs"]["action_manifest"] = str(man)
        self.S.ENV["heads"] = {"hub": "a" * 40, "runtime": "b" * 40}
        profile = json.loads((ROOT / G.ENV_PROFILE_FILE).read_text())
        ident = {"ingress_uid": 990, "ingress_gid": 990, "client_uid": 991, "client_gid": 991}
        record = self.tmp / "art/environment-record.json"
        with self.env(MVP_RUN_ID="run123", MVP_QUALIFICATION_SHA="9" * 40):
            res = self.I.capture_environment_record(hub, ident, profile, state=self.tmp / "st", sock="/x/ipc/s.sock", pid=4242, dest=self.tmp / "d.db", record_path=record)
        self.assertTrue(res["captured"])
        env = json.loads((record.parent / "environment-record.envelope.json").read_text())
        self.assertEqual((env["run_id"], env["qualification_sha"], env["record_sha256"]), ("run123", "9" * 40, "f" * 64))
        self.assertEqual(env["record_file_sha256"], hashlib.sha256(record.read_bytes()).hexdigest())
        self.assertEqual(env["capture_script_sha256"], hashlib.sha256((hub / "tools/mvp_env_record/capture_env_record.py").read_bytes()).hexdigest())
        argv = json.loads(record.read_text())["argv"]
        self.assertEqual(argv[argv.index("--label") + 1], "hosted-runner acceptance run run123, profile=approved")
        for flag, val in (("--ingress-pid", "4242"), ("--ingress-uid", "990"), ("--client-uid", "991"), ("--journal-mode", "wal"), ("--outsider-uid", "65533")):
            self.assertEqual(argv[argv.index(flag) + 1], val)
        self.assertIn("runtime=" + "b" * 40, argv)
        self.assertTrue(any(a.startswith("manifest_sha256.refund_integration_v1_1.manifest.json=") for a in argv))
        # no run id supplied: the envelope omits it (the gate then says INCOMPLETE), it never invents one
        for k in ("MVP_RUN_ID", "MVP_QUALIFICATION_SHA"):
            os.environ.pop(k, None)
        self.I.capture_environment_record(hub, ident, profile, state=self.tmp / "st", sock="/x/ipc/s.sock", pid=4242, dest=self.tmp / "d.db", record_path=record)
        env = json.loads((record.parent / "environment-record.envelope.json").read_text())
        self.assertNotIn("run_id", env)
        self.assertNotIn("qualification_sha", env)

    def test_capture_script_absent_from_the_hub_checkout_is_reported_not_faked(self):
        hub = self.tmp / "hub2"
        (hub / "tools/mvp_ingress").mkdir(parents=True)
        (hub / "tools/mvp_env_record").mkdir(parents=True)
        profile = json.loads((ROOT / G.ENV_PROFILE_FILE).read_text())
        res = self.I.capture_environment_record(hub, {}, profile, state="s", sock="x", pid=1, dest="d", record_path=self.tmp / "r.json")
        self.assertFalse(res["captured"])
        self.assertFalse((self.tmp / "r.json").exists())

    @unittest.skipUnless(hasattr(__import__("os"), "geteuid") and __import__("os").geteuid() == 0, "needs root to drop privileges")
    def test_owner_side_observation_runs_as_the_dropped_uid_with_umask_077(self):
        import os
        out = self.I._run_as(65534, 65534, lambda: {"uid": os.geteuid(), "gid": os.getegid(), "groups": os.getgroups(), "umask": os.umask(0o077)})
        self.assertEqual(out, {"uid": 65534, "gid": 65534, "groups": [], "umask": 0o077})
        with self.assertRaises(RuntimeError):
            self.I._run_as(65534, 65534, lambda: 1 / 0)

    def test_yama_absent_or_below_one_blocks_the_boundary_test(self):
        for value in ("unavailable: FileNotFoundError", "0", ""):
            with self.subTest(value):
                self.assertIsNotNone(self.I.yama_block_reason(value))
        for value in ("1", "2", "3"):
            self.assertIsNone(self.I.yama_block_reason(value))


class HardeningTests(unittest.TestCase):
    """Preflight of the hub capture script, qualification_revision refusal, interpreter note."""

    PIN = ENV_PROFILE["capture_script"]["sha256"]

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hard-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def hub_script(self, content):
        f = self.tmp / "components/hub" / ENV_PROFILE["capture_script"]["path"]
        f.parent.mkdir(parents=True, exist_ok=True)
        if content is not None:
            f.write_bytes(content)
        return f

    def test_preflight_fails_early_when_the_script_is_absent_a_symlink_or_other_bytes(self):
        self.hub_script(None)
        self.assertEqual(len(G.preflight_hub(ROOT, self.tmp / "components")), 1)
        self.assertEqual(G.main(["preflight-hub", "--components-dir", str(self.tmp / "components"), "--repo-root", str(ROOT)]), 1)
        f = self.hub_script(b"# some other script\n")
        self.assertIn("not the pinned", G.preflight_hub(ROOT, self.tmp / "components")[0])
        f.unlink()
        real = self.tmp / "real.py"
        real.write_bytes(b"x")
        f.symlink_to(real)
        self.assertEqual(len(G.preflight_hub(ROOT, self.tmp / "components")), 1)

    def test_script_left_at_the_old_ingress_path_fails_preflight_and_g11(self):
        old = self.tmp / "components/hub/tools/mvp_ingress/capture_env_record.py"
        root, _ = make_root(self.tmp / "root")
        self.hub_script(FAKE_SCRIPT)
        self.assertEqual(G.preflight_hub(root, self.tmp / "components"), [])
        old.parent.mkdir(parents=True, exist_ok=True)
        old.write_bytes(FAKE_SCRIPT)
        problems = G.preflight_hub(root, self.tmp / "components")
        self.assertEqual(len(problems), 1)
        self.assertIn("inside the ingress package", problems[0])
        self.assertEqual(G.main(["preflight-hub", "--components-dir", str(self.tmp / "components"), "--repo-root", str(root)]), 1)

    def test_preflight_passes_for_the_pinned_bytes(self):
        root, _ = make_root(self.tmp / "root")  # profile pinned to the stand-in script
        self.hub_script(FAKE_SCRIPT)
        self.assertEqual(G.preflight_hub(root, self.tmp / "components"), [])
        self.assertEqual(G.main(["preflight-hub", "--components-dir", str(self.tmp / "components"), "--repo-root", str(root)]), 0)

    def test_workflow_runs_the_preflight_right_after_the_hub_checkout_and_documents_hub_revision(self):
        wf = (ROOT / ".github/workflows/mvp-acceptance.yml").read_text()
        hub_co = wf.index("path: components/hub")
        pre = wf.index("preflight-hub")
        self.assertLess(hub_co, pre)
        self.assertLess(pre, wf.index("actions/setup-python"))
        self.assertEqual(wf[hub_co:pre].count("- uses:"), 0)  # nothing else runs between the checkout and the preflight
        self.assertGreaterEqual(wf.count(self.PIN), 2)  # the input description and the header
        self.assertIn("MUST name a hub sha", wf)
        self.assertIn("0e2b52a0", wf)

    def run_validate_step(self, qual_rev, github_sha):
        import re
        import subprocess
        wf = (ROOT / ".github/workflows/mvp-acceptance.yml").read_text()
        step = wf[wf.index("- name: Validate qualification_revision"):]
        body = step[step.index("run: |\n") + len("run: |\n"):step.index("      - uses:")]
        script = "\n".join(line[10:] for line in body.splitlines())
        return subprocess.run(["bash", "-c", script], env={"QUAL_REV": qual_rev, "GITHUB_SHA": github_sha, "PATH": "/usr/bin:/bin"}, capture_output=True, text=True).returncode

    def test_qualification_revision_must_be_blank_or_the_workflow_commit(self):
        sha, other = "a" * 40, "b" * 40
        self.assertEqual(self.run_validate_step("", sha), 0)
        self.assertEqual(self.run_validate_step(sha, sha), 0)
        self.assertEqual(self.run_validate_step(other, sha), 1)
        self.assertEqual(self.run_validate_step("main", sha), 1)
        self.assertEqual(self.run_validate_step("abc123", sha), 1)

    def test_readme_states_which_interpreters_the_match_checks_apply_to(self):
        text = (ROOT / "process/mvp-acceptance/README.md").read_text()
        self.assertIn("system `/usr/bin/python3 -I`", text)
        self.assertIn("apply to the ingress and the suite only, never to the probe client", text)


class OracleMessageAndIdentityTests(unittest.TestCase):
    """G-02 and G-02b messages follow the battery (not a hard-coded 'v1, v2 and v3'); the identity file mirrors the committed tuple pin."""

    @staticmethod
    def _checks(results):
        gate = G.Gate()
        G.check_oracle(gate, ROOT, BATTERY, results)
        return {c["id"]: c for c in gate.checks}

    def test_version_labels_come_from_the_file_names(self):
        self.assertEqual(G._version_labels(["process/mvp-chain/expectations.proposed.v6.json", "process/mvp-chain/expectations.proposed.v1.json",
                                            "process/mvp-chain/expectations.proposed.v3.json"]), ["v1", "v3", "v6"])
        self.assertEqual(G._version_labels(["x/other.json"]), ["other.json"])

    def test_g02_and_g02b_details_name_the_battery_files(self):
        in_force_file = BATTERY["oracle"]["expectations_in_force"]
        sha = BATTERY["oracle"]["unchanged_files_sha256"][in_force_file]
        checks = self._checks({"expectations_sha256": sha})
        labels = G._version_labels(BATTERY["oracle"]["unchanged_files_sha256"])
        self.assertEqual(checks["G-02"]["status"], "PASS")
        self.assertIn(", ".join(labels), checks["G-02"]["detail"])
        self.assertEqual(checks["G-02b"]["status"], "PASS")
        self.assertIn(f"({G._version_labels([in_force_file])[0]})", checks["G-02b"]["detail"])

    def test_g02b_fails_when_the_suite_used_another_expectations_file(self):
        self.assertEqual(self._checks({"expectations_sha256": "0" * 64})["G-02b"]["status"], "FAIL")
        self.assertEqual(self._checks({})["G-02b"]["status"], "FAIL")

    def test_identity_inputs_equal_the_committed_tuple_pin(self):
        ident = json.loads((ROOT / "process/mvp-acceptance/candidate-identity.inputs.json").read_text())["components"]
        pin = json.loads((ROOT / "process/mvp-chain/tuple-pin.proposed.json").read_text())["components"]
        self.assertEqual({k: v["sha"] for k, v in ident.items()}, {k: v["sha"] for k, v in pin.items()})
        self.assertTrue(all(isinstance(v["sha"], str) and re.fullmatch(r"[0-9a-f]{40}", v["sha"]) for v in pin.values()), "no null or short sha in the pin file")


class ComposedV6BatteryTests(unittest.TestCase):
    """The composed v6 proposal is the oracle in force and the battery, the suite default and the workflow agree (proposal only; Qualification owns the oracle)."""
    V6 = "process/mvp-chain/expectations.proposed.v6.json"
    V7 = "process/mvp-chain/expectations.proposed.v7.json"

    @staticmethod
    def _entry(test_id):
        return next(t for t in BATTERY["tests"] if t["id"] == test_id)

    def test_v7_is_in_force_with_its_own_hash_and_v1_to_v3_and_v6_stay_listed(self):
        oracle = BATTERY["oracle"]
        self.assertEqual(oracle["expectations_in_force"], self.V7)
        self.assertEqual(oracle["unchanged_files_sha256"][self.V7], G.sha256_file(ROOT / self.V7))
        self.assertEqual(oracle["unchanged_files_sha256"][self.V6], G.sha256_file(ROOT / self.V6))
        self.assertEqual(oracle["unchanged_files_sha256"][self.V6], "fe6ecf871d38061c8767e32ae62440c132b357c9b53b10de7412ef145651da4a")
        for v in (1, 2, 3):
            rel = f"process/mvp-chain/expectations.proposed.v{v}.json"
            self.assertEqual(oracle["unchanged_files_sha256"][rel], G.sha256_file(ROOT / rel))
        self.assertIn(self.V7, G.frozen_files(ROOT))
        self.assertIn(self.V6, G.frozen_files(ROOT))

    def test_nc2_06_is_the_oracle_row_entry_of_test_mvp_chain_not_of_the_ambiguity_file(self):
        entry = self._entry("NC2-06")
        self.assertEqual({k: entry[k] for k in ("kind", "invocation", "file", "test", "row")},
                         {"kind": "oracle_row", "invocation": "mvp-chain", "file": "suites/mvp-chain/test_mvp_chain.py", "test": "test_row[NC2-06]", "row": "NC2-06"})
        ids = [t["id"] for t in BATTERY["tests"]]
        self.assertEqual(ids[ids.index("NC2-05") + 1], "NC2-06")
        self.assertEqual([t for t in BATTERY["tests"] if t["kind"] == "oracle_row" and t["file"].endswith("test_ingress_ambiguity.py")], [])

    def test_g03_passes_with_v6_and_is_incomplete_without_nc2_06(self):
        gate = G.Gate()
        G.check_battery_covers_oracle(gate, ROOT, BATTERY)
        self.assertEqual(gate.checks[0]["status"], "PASS", gate.checks[0]["detail"])
        trimmed = copy.deepcopy(BATTERY)
        trimmed["tests"] = [t for t in trimmed["tests"] if t["id"] != "NC2-06"]
        gate = G.Gate()
        G.check_battery_covers_oracle(gate, ROOT, trimmed)
        self.assertEqual(gate.checks[0]["status"], "INCOMPLETE")
        self.assertIn("NC2-06", gate.checks[0]["detail"])

    def test_suite_default_expectations_is_the_oracle_in_force(self):
        text = (ROOT / "suites/mvp-chain/conftest.py").read_text()
        self.assertIn('ROOT / "process" / "mvp-chain" / "expectations.proposed.v7.json"', text)
        self.assertNotIn('expectations.proposed.v3.json")', text)

    def test_supplementary_entries_cover_exactly_the_collected_tests_of_the_two_files(self):
        if importlib.util.find_spec("pytest") is None:  # the unittest-only CI jobs install no pytest; the pytest runs (and gate G-13 in a run) do check it
            self.skipTest("pytest is not installed in this environment: the collection cross-check needs it")
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "suites/mvp-chain/test_kwflow.py",
                              "suites/mvp-chain/test_ingress_ambiguity.py"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=300).stdout
        collected = {l.strip() for l in out.splitlines() if l.startswith("suites/mvp-chain/") and "::" in l}
        listed = {f"{t['file']}::{t['test']}" for t in BATTERY["tests"] if t["kind"].startswith("supplementary_") and t["invocation"] == "mvp-chain"}
        self.assertEqual(collected, listed)
        kinds = {t["file"]: t["kind"] for t in BATTERY["tests"] if t["kind"].startswith("supplementary_") and t["invocation"] == "mvp-chain"}
        self.assertEqual(kinds, {"suites/mvp-chain/test_kwflow.py": "supplementary_nc4_03_predicate",
                                 "suites/mvp-chain/test_ingress_ambiguity.py": "supplementary_nc2_06_negative_control"})
        self.assertEqual(len([t for t in BATTERY["tests"] if t["kind"] == "supplementary_nc4_03_predicate"]), 183)
        self.assertEqual(len([t for t in BATTERY["tests"] if t["kind"] == "supplementary_nc2_06_negative_control"]), 6)

    def test_workflow_collect_and_run_lists_equal_the_battery_paths(self):
        wf = (ROOT / ".github/workflows/mvp-acceptance.yml").read_text()
        want = set(BATTERY["invocations"]["mvp-chain"]["paths"])
        collect = wf[wf.index("--collect-only -q -p no:cacheprovider \\\n            suites/mvp-chain"):]
        collect = collect[:collect.index("tee")]
        run = wf[wf.index("-p exchange_exclusion_plugin \\\n            suites/mvp-chain"):]
        run = run[:run.index("-o junit_suite_name")]
        for label, block in (("collect", collect), ("run", run)):
            self.assertEqual(set(re.findall(r"suites/mvp-chain/[A-Za-z0-9_]+\.py", block)), want, label)

    def test_a_supplementary_test_that_is_skipped_or_missing_is_incomplete(self):
        rows = [{"id": t["row"], "status": "PASS"} for t in BATTERY["tests"] if t["kind"] == "oracle_row"]
        tmp = Path(tempfile.mkdtemp(prefix="supp-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        collected = {t["invocation"]: [] for t in BATTERY["tests"]}
        junit = {tag: [] for tag in collected}
        target = next(t for t in BATTERY["tests"] if t["kind"] == "supplementary_nc4_03_predicate")
        for t in BATTERY["tests"]:
            key = f"{t['file']}::{t['test']}"
            collected[t["invocation"]].append(key)
            if t is target:
                junit[t["invocation"]].append((t["file"], t["test"], "skipped"))
            else:
                junit[t["invocation"]].append((t["file"], t["test"], "passed"))
        for tag, inv in BATTERY["invocations"].items():
            (tmp / inv["collected"]).write_text("\n".join(collected.get(tag, [])) + "\n")
            cases = "".join(f'<testcase classname="{f[:-3].replace("/", ".")}" name="{n}">{"<skipped/>" if st == "skipped" else ""}</testcase>' for f, n, st in junit.get(tag, []))
            (tmp / inv["junit"]).write_text(f'<testsuites><testsuite name="x">{cases}</testsuite></testsuites>')
        gate = G.Gate()
        G.check_battery_execution(gate, tmp, BATTERY, {"rows": rows})
        status = {c["id"]: c for c in gate.checks}
        self.assertEqual(status["G-05"]["status"], "INCOMPLETE", status["G-05"]["detail"])
        self.assertIn(target["id"], status["G-05"]["detail"])

class ImportAnalysisTests(unittest.TestCase):
    """The static import analysis behind the candidate commitment is cached by file CONTENT only; the resolution against a root is never cached."""

    def test_names_are_a_pure_function_of_the_source_and_bad_source_is_none(self):
        src = "import os\nfrom tools import x as y\nfrom . import z\ndef f():\n    import helper\n"
        self.assertEqual(G._imported_names(src), (("os", 0), ("tools", 0), ("tools.x", 0), ("", 1), ("z", 1), ("helper", 0)))
        self.assertEqual(G._imported_names(src), G._imported_names(src))
        self.assertIsNone(G._imported_names("def broken(:\n"))

    def test_same_bytes_resolve_differently_in_two_roots(self):
        tmp = Path(tempfile.mkdtemp(prefix="imports-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        for name, with_helper in (("a", True), ("b", False)):
            (tmp / name / "tools").mkdir(parents=True)
            (tmp / name / "suites").mkdir()
            (tmp / name / "suites" / "t.py").write_text("import helper_mod\n")
            if with_helper:
                (tmp / name / "tools" / "helper_mod.py").write_text("X = 1\n")
        self.assertEqual(G._local_imports(tmp / "a", "suites/t.py"), {"tools/helper_mod.py"})
        self.assertEqual(G._local_imports(tmp / "b", "suites/t.py"), set())
        (tmp / "b" / "suites" / "bad.py").write_text("def broken(:\n")
        self.assertEqual(G._local_imports(tmp / "b", "suites/bad.py"), set())


class RequiredControlsTests(unittest.TestCase):
    """Architect rulings Q2, Q5, Q6: the three required negative controls NC7-01..03, the route-B mediation entries, limitations and inventory-versus-claims text."""
    V7 = json.loads((ROOT / "process/mvp-chain/expectations.proposed.v7.json").read_text())
    V6 = json.loads((ROOT / "process/mvp-chain/expectations.proposed.v6.json").read_text())

    def _verdict(self):
        sys.path.insert(0, str(ROOT / "suites/mvp-chain"))
        import verdict
        return verdict

    @staticmethod
    def _refused():
        return {"status": "denied", "attempted": False, "effect_count": 0}

    def _obs(self):
        refused = self._refused()
        claim_refused = {"claim_ok": False, "effect_count": 0}
        return {"nc_authority_gates": {
            "status": "ran", "control": {"status": "executed", "effect_count": 1},
            "unauthorized": {"forged_claim_id": dict(refused), "not_authorized_decision": {"decision_result": "hold", **claim_refused}},
            "stale_or_mismatched": {"claim_expired": dict(refused), "authority_advanced_after_claim": dict(refused), "envelope_amount_mismatch": dict(refused),
                                    "envelope_grant_revision_mismatch": dict(refused), "resolver_revision_changed_before_claim": dict(claim_refused)},
            "evidence": {"missing": dict(refused), "invalid_state": dict(refused), "expired": dict(refused), "missing_at_claim_issuance": dict(claim_refused)}}}

    def _rows(self):
        return {r["id"]: r for r in self.V7["rows"] if r["id"].startswith("NC7-")}

    def test_v7_is_v6_plus_exactly_the_three_required_controls_and_the_launch_isolation_row(self):
        self.assertEqual(sorted(self._rows()), ["NC7-01", "NC7-02", "NC7-03"])
        self.assertEqual([r for r in self.V7["rows"] if not r["id"].startswith("NC7-") and r["id"] not in ("NC4-04", "NC4-03")], [r for r in self.V6["rows"] if r["id"] != "NC4-03"])
        nc403 = lambda doc: next(r for r in doc["rows"] if r["id"] == "NC4-03")
        self.assertEqual([a["obs"] for a in nc403(self.V7)["all"]], [a["obs"] for a in nc403(self.V6)["all"]])  # same predicates; only the reviewed values (file list, digest) follow the launcher change
        for key in ("schema", "statuses", "semantics", "operators"):
            self.assertEqual(self.V7[key], self.V6[key])
        self.assertEqual(sum(r.get("mandatory", True) for r in self.V7["rows"]), 41)
        self.assertTrue(all(r["mandatory"] is True for r in self._rows().values()))
        self.assertEqual(self.V7["supersedes"]["v6_sha256"], G.sha256_file(ROOT / "process/mvp-chain/expectations.proposed.v6.json"))

    def test_expected_verdicts_are_computed_from_observations(self):
        v = self._verdict()
        for rid, row in self._rows().items():
            self.assertEqual(v.evaluate_row(row, self._obs())["status"], v.PASS, rid)
            self.assertEqual(v.evaluate_row(row, {})["status"], v.NOT_RUN, rid)
            blocked = {"nc_authority_gates": {"status": "blocked", "blocked_reason": "x"}}
            self.assertEqual(v.evaluate_row(row, blocked)["status"], v.BLOCKED, rid)

    def test_each_refusal_predicate_fails_when_an_effect_was_committed_or_the_control_cannot_commit(self):
        v = self._verdict()
        cases = {"NC7-01": ["unauthorized.forged_claim_id", "unauthorized.not_authorized_decision"],
                 "NC7-02": ["stale_or_mismatched.claim_expired", "stale_or_mismatched.authority_advanced_after_claim", "stale_or_mismatched.envelope_amount_mismatch",
                            "stale_or_mismatched.envelope_grant_revision_mismatch", "stale_or_mismatched.resolver_revision_changed_before_claim"],
                 "NC7-03": ["evidence.missing", "evidence.invalid_state", "evidence.expired", "evidence.missing_at_claim_issuance"]}
        for rid, paths in cases.items():
            row = self._rows()[rid]
            for path in paths:
                obs = self._obs()
                node = obs["nc_authority_gates"]
                for part in path.split("."):
                    node = node[part]
                node["effect_count"] = 1
                self.assertEqual(v.evaluate_row(row, obs)["status"], v.FAIL, f"{rid} {path}")
                obs = self._obs()
                node = obs["nc_authority_gates"]
                for part in path.split("."):
                    node = node[part]
                del node["effect_count"]
                self.assertEqual(v.evaluate_row(row, obs)["status"], v.FAIL, f"{rid} {path} missing observation")
            for control in ({"status": "denied", "effect_count": 0}, {"status": "executed", "effect_count": 2}):
                obs = self._obs()
                obs["nc_authority_gates"]["control"] = control
                self.assertEqual(v.evaluate_row(row, obs)["status"], v.FAIL, f"{rid} control {control}")
        obs = self._obs()
        obs["nc_authority_gates"]["unauthorized"]["not_authorized_decision"]["decision_result"] = "authorized"
        self.assertEqual(v.evaluate_row(self._rows()["NC7-01"], obs)["status"], v.FAIL)
        obs = self._obs()
        obs["nc_authority_gates"]["unauthorized"]["forged_claim_id"]["attempted"] = True
        self.assertEqual(v.evaluate_row(self._rows()["NC7-01"], obs)["status"], v.FAIL)

    def test_battery_lists_the_three_rows_as_oracle_rows_after_nc6_04(self):
        ids = [t["id"] for t in BATTERY["tests"]]
        self.assertEqual(ids[ids.index("NC6-04") + 1:ids.index("NC6-04") + 4], ["NC7-01", "NC7-02", "NC7-03"])
        for rid in ("NC7-01", "NC7-02", "NC7-03"):
            t = next(x for x in BATTERY["tests"] if x["id"] == rid)
            self.assertEqual((t["kind"], t["invocation"], t["file"], t["test"], t["row"]), ("oracle_row", "mvp-chain", "suites/mvp-chain/test_mvp_chain.py", f"test_row[{rid}]", rid))

    def test_route_b_mediation_entries_map_only_refusal_tests_and_characterisations_stay_non_mandatory(self):
        med = [t for t in BATTERY["tests"] if t["kind"] == "supplementary_route_b_mediation"]
        self.assertEqual(len(med), 16)
        self.assertTrue(all(t["invocation"] == "d2-route-b" and t["file"] == "suites/mvp-d2-route-b/test_inventory_negatives.py" for t in med))
        self.assertFalse([t for t in med if "REACHABLE" in t["test"]])
        non = [t for t in BATTERY["non_mandatory_tests"] if t["invocation"] == "d2-route-b"]
        self.assertEqual(len(non), 6)
        self.assertEqual(len([t for t in non if "REACHABLE" in t["test"]]), 5)
        inv = BATTERY["invocations"]["d2-route-b"]
        self.assertEqual(inv["paths"], ["suites/mvp-d2-route-b/test_inventory_negatives.py"])
        self.assertFalse(inv["runs_as_root"])
        self.assertIn("suites/mvp-d2-route-b", G.SUITE_DIRS)

    def test_d2_entries_equal_the_collected_tests_of_the_d2_file(self):
        if importlib.util.find_spec("pytest") is None:
            self.skipTest("pytest is not installed in this environment: the collection cross-check needs it")
        if not (os.environ.get("D2_CONTROL_PLANE_DIR") and os.environ.get("D2_RUNTIME_DIR")):
            self.skipTest("D2_CONTROL_PLANE_DIR and D2_RUNTIME_DIR (component checkouts) are needed to import the d2 file")
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "suites/mvp-d2-route-b/test_inventory_negatives.py"],
                             cwd=ROOT, env=env, capture_output=True, text=True, timeout=300).stdout
        collected = {l.strip() for l in out.splitlines() if l.startswith("suites/mvp-d2-route-b/") and "::" in l}
        listed = {f"{t['file']}::{t['test']}" for t in BATTERY["tests"] + BATTERY["non_mandatory_tests"] if t["invocation"] == "d2-route-b"}
        self.assertEqual(collected, listed)

    def test_workflow_runs_and_collects_the_d2_invocation_with_the_tuple_pin(self):
        wf = (ROOT / ".github/workflows/mvp-acceptance.yml").read_text()
        self.assertIn("collected-d2-route-b.txt", wf)
        self.assertIn("junit-d2-route-b.xml", wf)
        self.assertIn("pytest-exit-d2-route-b.txt", wf)
        self.assertGreaterEqual(wf.count('D2_CONTROL_PLANE_PIN="${{ steps.tuple.outputs.control_plane }}"'), 2)
        self.assertIn("D2_RUNTIME_DIR: ${{ github.workspace }}/components/runtime", wf)

    def test_os_kill_is_unqualified_and_inventory_is_not_claims(self):
        lim = self.V7["limitations"]["os_level_process_kill"]
        self.assertTrue(lim.startswith("UNQUALIFIED"))
        self.assertIn("synthetic fault injection", lim)
        self.assertIn("41", self.V7["inventory_vs_claims"]["unique_governance_claims"])
        self.assertIn("not additional claims", self.V7["inventory_vs_claims"]["test_inventory"])
        self.assertIn("claims", (ROOT / "process/mvp-acceptance/README.md").read_text())


class CompositeIdentityAndLaunchTests(GateTests):
    """Round 3/4: composite candidate identity (G-15) and the code-level launch isolation row NC4-04."""
    IDENT = json.loads((ROOT / "process/mvp-acceptance/candidate-identity.inputs.json").read_text())

    def test_declared_composite_values_match_the_real_repository_files(self):
        c = self.IDENT["composite"]
        self.assertEqual(c["hub"]["revision"], self.IDENT["components"]["hub"]["sha"])
        self.assertEqual(c["environment_profile"]["sha256"], G.sha256_file(ROOT / c["environment_profile"]["path"]))
        for rel, digest in c["python"]["lock_files_sha256"].items():
            self.assertEqual(G.sha256_file(ROOT / rel), digest, rel)
        self.assertEqual(c["hub"]["capture_script_sha256"], json.loads((ROOT / G.ENV_PROFILE_FILE).read_text())["hub_record"]["capture_script"]["sha256"])
        self.assertEqual(c["hub"]["launcher_entry_point"], "tools/mvp_ingress/launch.py")
        self.assertEqual(sorted(c["hub"]["git_tree_ids"]), ["tools/mvp_env_record", "tools/mvp_ingress"])

    def test_composite_matches_is_pass(self):
        self.assertEqual(self.verdict()[1]["G-15"], "PASS")

    def test_every_composite_member_mismatch_is_fail_and_missing_is_incomplete(self):
        cases = {"tree id ingress": lambda v: v["hub"]["git_tree_ids"].update({"tools/mvp_ingress": "0" * 40}),
                 "tree id env record": lambda v: v["hub"]["git_tree_ids"].update({"tools/mvp_env_record": "0" * 40}),
                 "launcher": lambda v: v["hub"].update(launcher_entry_point_is_file=False),
                 "capture": lambda v: v["hub"].update(capture_script_sha256="0" * 64),
                 "registry digest": lambda v: v["hub"].update(registry_catalogue_manifest_digest="sha256:" + "0" * 64),
                 "python": lambda v: v["python"].update(version="3.12"),
                 "lock": lambda v: v["python"]["lock_files_sha256"].update({next(iter(v["python"]["lock_files_sha256"])): "0" * 64}),
                 "profile": lambda v: v["environment_profile"].update(sha256="0" * 64),
                 "hub revision": lambda v: v["hub"].update(revision="1" * 40)}
        for name, mut in cases.items():
            with self.subTest(name):
                self.build(composite_mutate=mut)
                self.assertEqual(self.verdict()[1]["G-15"], "FAIL")
        self.build()
        doc = json.loads((self.run_dir / "tuple-resolved.json").read_text())
        del doc["composite_verified"]
        (self.run_dir / "tuple-resolved.json").write_text(json.dumps(doc))
        self.assertEqual(self.verdict()[1]["G-15"], "INCOMPLETE")

    def test_nc4_04_is_a_mandatory_oracle_row_with_launch_predicates_only(self):
        rows = {r["id"]: r for r in RequiredControlsTests.V7["rows"]}
        row = rows["NC4-04"]
        self.assertTrue(row["mandatory"])
        self.assertEqual({a["obs"] for a in row["all"]}, {f"nc_unmediated.launch.{k}" for k in ("argv_flags", "entry_point_is_launch_py", "allow_uid_present", "allow_uid_equals_client", "legacy_module_form_refused")})
        self.assertIn("NOT host isolation", row["title"])
        t = next(x for x in BATTERY["tests"] if x["id"] == "NC4-04")
        self.assertEqual((t["kind"], t["test"], t["row"]), ("oracle_row", "test_row[NC4-04]", "NC4-04"))

    def test_nc4_04_verdicts_from_synthetic_launch_evidence(self):
        sys.path.insert(0, str(ROOT / "suites/mvp-chain"))
        import verdict
        row = {r["id"]: r for r in RequiredControlsTests.V7["rows"]}["NC4-04"]
        good = {"nc_unmediated": {"status": "ran", "launch": {"argv_flags": ["-I", "-B"], "entry_point_is_launch_py": True, "allow_uid_present": True,
                                                              "allow_uid_equals_client": True, "legacy_module_form_refused": True}}}
        self.assertEqual(verdict.evaluate_row(row, good)["status"], verdict.PASS)
        for key, bad in (("argv_flags", ["-B"]), ("argv_flags", ["-I"]), ("entry_point_is_launch_py", False), ("allow_uid_present", False),
                         ("allow_uid_equals_client", False), ("legacy_module_form_refused", False)):
            obs = json.loads(json.dumps(good))
            obs["nc_unmediated"]["launch"][key] = bad
            self.assertEqual(verdict.evaluate_row(row, obs)["status"], verdict.FAIL, (key, bad))
        obs = json.loads(json.dumps(good))
        del obs["nc_unmediated"]["launch"]
        self.assertEqual(verdict.evaluate_row(row, obs)["status"], verdict.FAIL)


if __name__ == "__main__":
    unittest.main()
