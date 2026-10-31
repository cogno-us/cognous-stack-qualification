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

import pytest

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
    assert out.returncode == 0, out.stderr[-1500:]
    return json.loads(out.stdout.strip().splitlines()[-1])


def sub_a(rec):
    return next(s for s in rec["record"]["subcases"] if s["id"] == "NC4-03a")


# 1-4: developer-optout never yields PASS from the Yama probe, whatever the Yama value; the observation is still recorded
@pytest.mark.parametrize("scope", ["ABSENT", "0", "1", "2", "3"])
def test_optout_yama_never_pass_via_run_host_subcases(scope):
    rec = run("developer-optout", scope)
    assert all(s["status"] != "PASS" for s in rec["record"]["subcases"]), rec  # the NM-138 predicate
    a = sub_a(rec)
    assert a["status"] == "BLOCKED"
    if scope in ("1", "2", "3"):
        assert "developer-optout" in a["reason"] and a["observed"] == {"ptrace_scope": scope}  # supported Yama: capped, fact still recorded
    else:
        assert "ptrace_scope" in a["reason"]  # absent or below threshold: the existing unsupported-Yama BLOCKED reason is unchanged


@pytest.mark.parametrize("scope", ["ABSENT", "0", "1", "2", "3"])
def test_optout_direct_probe_is_blocked_for_every_yama_value(scope):
    d = run("optout-ctx", scope)["direct"]
    assert d["status"] == "BLOCKED" and d["observed"] == {"ptrace_scope": None if scope == "ABSENT" else scope}


# 5: approved profile with supported Yama still PASSes, exactly as before (status, reason text, observed keys)
@pytest.mark.parametrize("scope", ["1", "2", "3"])
def test_approved_supported_yama_still_passes_unchanged(scope):
    d = run("approved-ctx", scope)["direct"]
    assert d == {"status": "PASS", "reason": "kernel.yama.ptrace_scope >= 1", "observed": {"ptrace_scope": scope}}


# 6: approved profile with unsupported Yama stays BLOCKED with the unchanged reason
@pytest.mark.parametrize("scope", ["ABSENT", "0"])
def test_approved_unsupported_yama_stays_blocked(scope):
    d = run("approved-ctx", scope)["direct"]
    assert d["status"] == "BLOCKED" and "the exact profile is unsupported" in d["reason"] and "no weaker environment is substituted" in d["reason"]
    assert d["observed"] == {"ptrace_scope": None if scope == "ABSENT" else scope}


# 7: existing refusal semantics are preserved: an unresolved profile blocks the identity subcases only and judges Yama on its own host fact
def test_unknown_profile_semantics_preserved():
    rec = run("unknown", "1")["record"]
    by = {s["id"]: s for s in rec["subcases"]}
    assert all(by[i]["status"] == "BLOCKED" for i in ("NC4-03b", "NC4-03c", "NC4-03d"))
    assert by["NC4-03a"]["status"] == "PASS" and by["NC4-03a"]["observed"] == {"ptrace_scope": "1"}
    assert run("unknown", "0")["record"]["subcases"][0]["status"] == "BLOCKED"


def test_source_still_has_no_other_uncapped_pass_in_probes():
    """Only NC4-03a returned PASS outside _cap before the fix; after it every PASS return in a probe passes through _cap or the explicit approved-only line."""
    src = (CHAIN / "_nc4_03_host.py").read_text()
    body = src[src.index("def sub_a_yama"):src.index("def sub_b_uid_separation")]
    assert "return PASS," not in body and "_cap(PASS, ctx.get(\"ratified\", True), NOT_RATIFIED)" in body
