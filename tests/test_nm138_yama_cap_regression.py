"""NM-138 regression: the developer-optout ceiling for NC4-03a (sub_a_yama) with mocked Yama observations.

SPDX-License-Identifier: Apache-2.0

OCS-MVP-NM138-REPAIR. Deterministic and host-independent: the Yama value is supplied by replacing ``_ingress._read`` inside a child interpreter (no kernel setting
is read or changed). Each case runs the REAL ``_nc4_03_host.sub_a_yama`` / ``run_host_subcases`` code of suites/mvp-chain in an isolated child process so that the
suite's generic module names (verdict, _state, _ingress) never enter this test session. Not part of the frozen mandatory battery (mandatory membership is unchanged);
NM-138 itself (suites/mvp-chain/test_nc4_03_host_subcases.py::test_developer_optout_can_never_be_pass) stays mandatory and untouched. Non-authorizing.
"""
import json
import os
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHAIN = ROOT / "suites" / "mvp-chain"

DRIVER = r"""
import json, os, sys
sys.dont_write_bytecode = True
chain, mode, scope = sys.argv[1], sys.argv[2], sys.argv[3]
suites = os.path.dirname(chain)
sys.path[:0] = [chain, suites, os.path.join(suites, "operation-identity"), os.path.join(os.path.dirname(suites), "tools")]
import _ingress, _nc4_03_host as H
real = _ingress._read
_ingress._read = lambda p: (None if scope == "ABSENT" else scope) if p == "/proc/sys/kernel/yama/ptrace_scope" else real(p)
if mode == "unknown":
    os.environ["MVP_INGRESS_PROFILE"] = "bogus"
elif mode == "developer-optout":
    os.environ["MVP_INGRESS_PROFILE"] = "developer-optout"
else:
    os.environ.pop("MVP_INGRESS_PROFILE", None)
direct = {}
if mode in ("optout-ctx", "approved-ctx"):
    s, why, obs = H.sub_a_yama({"ratified": mode == "approved-ctx"})
    direct = {"status": s, "reason": why, "observed": obs}
rec = H.run_host_subcases(None) if mode in ("developer-optout", "unknown") else None
print(json.dumps({"direct": direct, "record": rec}, default=str))
"""


def run(mode, scope):
    out = subprocess.run([sys.executable, "-I", "-B", "-c", DRIVER, str(CHAIN), mode, scope], capture_output=True, text=True, timeout=120, cwd=str(ROOT))
    if out.returncode != 0:
        raise AssertionError(out.stderr[-1500:])
    return json.loads(out.stdout.strip().splitlines()[-1])


def sub_a(rec):
    return next(s for s in rec["record"]["subcases"] if s["id"] == "NC4-03a")


def obs(scope):
    return {"ptrace_scope": None if scope == "ABSENT" else scope}


class Nm138YamaCap(unittest.TestCase):
    # 1-4: developer-optout never yields PASS from the Yama probe, whatever the Yama value; the observation is still recorded
    def test_optout_yama_never_pass_via_run_host_subcases(self):
        for scope in ("ABSENT", "0", "1", "2", "3"):
            with self.subTest(scope=scope):
                rec = run("developer-optout", scope)
                self.assertTrue(all(s["status"] != "PASS" for s in rec["record"]["subcases"]), rec)  # the NM-138 predicate
                a = sub_a(rec)
                self.assertEqual(a["status"], "BLOCKED")
                if scope in ("1", "2", "3"):
                    self.assertIn("developer-optout", a["reason"])  # supported Yama: capped, fact still recorded
                    self.assertEqual(a["observed"], {"ptrace_scope": scope})
                else:
                    self.assertIn("ptrace_scope", a["reason"])  # absent or below threshold: the existing unsupported-Yama BLOCKED reason is unchanged

    def test_optout_direct_probe_is_blocked_for_every_yama_value(self):
        for scope in ("ABSENT", "0", "1", "2", "3"):
            with self.subTest(scope=scope):
                d = run("optout-ctx", scope)["direct"]
                self.assertEqual(d["status"], "BLOCKED")
                self.assertEqual(d["observed"], obs(scope))

    # 5: approved profile with supported Yama still PASSes, exactly as before (status, reason text, observed keys)
    def test_approved_supported_yama_still_passes_unchanged(self):
        for scope in ("1", "2", "3"):
            with self.subTest(scope=scope):
                self.assertEqual(run("approved-ctx", scope)["direct"], {"status": "PASS", "reason": "kernel.yama.ptrace_scope >= 1", "observed": {"ptrace_scope": scope}})

    # 6: approved profile with unsupported Yama stays BLOCKED with the unchanged reason
    def test_approved_unsupported_yama_stays_blocked(self):
        for scope in ("ABSENT", "0"):
            with self.subTest(scope=scope):
                d = run("approved-ctx", scope)["direct"]
                self.assertEqual(d["status"], "BLOCKED")
                self.assertIn("the exact profile is unsupported", d["reason"])
                self.assertIn("no weaker environment is substituted", d["reason"])
                self.assertEqual(d["observed"], obs(scope))

    # 7: existing refusal semantics are preserved and an unresolved profile fails closed: identity subcases BLOCKED, the Yama fact still recorded, never PASS
    def test_unknown_profile_fails_closed_and_keeps_refusal_semantics(self):
        for scope in ("ABSENT", "0", "1", "3"):
            with self.subTest(scope=scope):
                rec = run("unknown", scope)["record"]
                by = {s["id"]: s for s in rec["subcases"]}
                self.assertTrue(all(by[i]["status"] == "BLOCKED" for i in ("NC4-03b", "NC4-03c", "NC4-03d")), by)
                self.assertEqual(by["NC4-03a"]["status"], "BLOCKED")
                self.assertEqual(by["NC4-03a"]["observed"], obs(scope))
                self.assertTrue(all(s["status"] != "PASS" for s in rec["subcases"]))

    def test_source_guard_no_uncapped_pass_in_sub_a(self):
        src = (CHAIN / "_nc4_03_host.py").read_text()
        body = src[src.index("def sub_a_yama"):src.index("def sub_b_uid_separation")]
        self.assertNotIn("return PASS,", body)
        self.assertIn('_cap(PASS, ctx.get("ratified", False), NOT_RATIFIED)', body)


if __name__ == "__main__":
    unittest.main()
