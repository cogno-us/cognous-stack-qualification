"""R2 G2-style PERSISTENCE / RESTART negative, row id G2 (evidence kind REAL; BUILDER_TESTED developer test code, NOT independent qualification). Worker B.

PRIVATE PREVIEW QUALIFICATION TUPLE (preview-only, NOT canonical). One bounded case, not a persistence program.

  1. the real Control Plane F4 workflow produces and persists run.json through BoundedRecordStore;
  2. RESTART: a fresh Python interpreter (subprocess) opens a new BoundedRecordStore on the file and returns the bytes it reloads; they equal the bytes the Control Plane wrote;
  3. CONTROL POSITIVE: the unmutated reloaded record is admitted by Replay under the explicit F4 profile (11 layers pass, claim-A markers);
  4. the reloaded bytes are mutated/substituted (critical evidence element) and persisted as a new file; a second fresh interpreter reloads them through BoundedRecordStore
     (the store does not validate carried selection text - that is not its job);
  5. Replay REFUSES with the exact typed code from the Registry verifier (not from the store); no bundle; the original file and its re-admission are unaffected.
"""
import base64
import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import harness as H
import real_cp_record as R

HERE = Path(__file__).resolve().parent
UNV = "registry_evidence_unverified:"

CHILD = r'''
import base64, hashlib, json, sys
sys.path.insert(0, %(here)r)
import harness as H
H.cp_bounded._now = lambda: H.NOW
H.cp_f4._now = lambda: H.NOW
path = sys.argv[1]
store = H.BoundedRecordStore(path, "run-1")          # a brand-new store object in a brand-new interpreter: nothing cached
model = store.load().model_dump(mode="json")          # the Control Plane's own load/validation path
data = open(path, "rb").read()
print(json.dumps({"sha256": hashlib.sha256(data).hexdigest(), "bytes_b64": base64.b64encode(data).decode(), "pid_is_child": True,
                  "decisions": len(model["decisions"])}))
'''


def restart_reload(path: Path) -> dict:
    """Reload `path` in a fresh interpreter through a fresh BoundedRecordStore (the supported reload path). Returns {bytes, sha256, pid}."""
    env = dict(os.environ)
    out = subprocess.run([sys.executable, "-I", "-c", CHILD % {"here": str(HERE)}, str(path)], capture_output=True, text=True, env=env, cwd=str(HERE.parent), timeout=120)
    assert out.returncode == 0, out.stderr[-2000:]
    d = json.loads(out.stdout.strip().splitlines()[-1])
    return {"bytes": base64.b64decode(d["bytes_b64"]), "sha256": d["sha256"], "decisions": d["decisions"]}


@pytest.mark.row("G2", "persistence/restart negative: valid retained record persisted, reloaded by a fresh BoundedRecordStore in a fresh interpreter, critical evidence mutated/substituted in the reloaded bytes -> Replay refuses (control: unmutated reload admitted)", kind="persistence")
def test_g2_persist_restart_mutate_replay_refuses(tmp_path):
    rr = R.produce_real(tmp_path / "cp")
    written = rr.path.read_bytes()
    H.check("run.json persisted by the Control Plane equals the bytes recorded at write time", written == rr.written_bytes)

    # ---- restart #1: fresh interpreter, fresh store ----------------------------------------------------------------------------------------------
    r1 = restart_reload(rr.path)
    H.check("reload in a fresh interpreter through a fresh BoundedRecordStore returns bytes EQUAL to the written bytes (sha256 equal)",
            r1["bytes"] == written and r1["sha256"] == hashlib.sha256(written).hexdigest() and r1["decisions"] == 1)
    reloaded = json.loads(r1["bytes"])
    H.check("reloaded record equals the in-process retrieved record", reloaded == rr.record)

    # ---- CONTROL POSITIVE on the reloaded, unmutated record --------------------------------------------------------------------------------------
    spy = H.Spy()
    bundle, _ = H.import_f4(reloaded, rr.operator, proposal=rr.proposal, verifier=spy)
    H.assert_exact_claim_a_markers(bundle, profile=H.SELECTOR_F4)
    H.check("CONTROL: the unmutated reloaded record is admitted (1 verifier call, 11 layers pass, claim-A markers exact)",
            spy.calls == 1 and set(spy.last["layers"].values()) == {"pass"} and len(spy.last["layers"]) == 11)

    # ---- mutate / substitute critical evidence in the reloaded bytes, persist as a new file, restart #2, Replay ------------------------------------
    donor = R.produce_real(tmp_path / "donor", mat=H.material(40, 30))

    def flip(t):
        env = json.loads(t)
        raw = bytearray(base64.b64decode(env["signatures"][0]["signature"]))
        raw[0] ^= 1
        env["signatures"][0]["signature"] = base64.b64encode(bytes(raw)).decode()
        return json.dumps(env, sort_keys=True)

    def edit(name, fn):
        doc = json.loads(r1["bytes"])
        fn(doc["decisions"][0]["selection_evidence"])
        p = tmp_path / ("mut-" + name)
        p.mkdir()
        (p / "run.json").write_bytes(json.dumps(doc).encode())
        return p / "run.json"

    cases = [
        ("selection_text_substituted", "other genuine selection text substituted in the persisted bytes", lambda e: e.update(selection_text=donor.evidence["selection_text"]), UNV + "record_digest_mismatch"),
        ("record_text_substituted", "other genuine Registry record text substituted in the persisted bytes", lambda e: e.update(record_text=donor.evidence["record_text"]), UNV + "record_digest_mismatch"),
        ("signature_flipped", "one signature byte flipped in the persisted selection text", lambda e: e.update(selection_text=flip(e["selection_text"])), UNV + "signature_invalid"),
        ("selection_evidence_swapped", "whole selection_evidence of another genuine run (different signed bound) swapped in the persisted bytes", lambda e: (e.clear(), e.update(copy.deepcopy(donor.evidence))), "registry_evidence_effective_digest_mismatch"),
    ]
    rows = []
    for name, text, fn, code in cases:
        mpath = edit(name, fn)
        H.check("%s: mutated bytes differ from the genuine persisted bytes" % name, mpath.read_bytes() != written)
        r2 = restart_reload(mpath)          # the store round-trips it (it does not validate carried selection text); a fresh interpreter reloads exactly these bytes
        H.check("%s: fresh store in a fresh interpreter reloads the mutated bytes unchanged (store is not the control)" % name, r2["bytes"] == mpath.read_bytes())
        res = H.refuse_import(json.loads(r2["bytes"]), rr.operator, rr.proposal, code, verifier_calls=1)
        H.check("%s: refusal came from the Registry verifier/Replay gate (verifier reached once), no bundle" % name, res.calls == 1 and res.bundle is None)
        rows.append(dict(case=name, description=text, expected=code, observed=res.code, verifier_calls=res.calls))
    H.note("cases", rows)

    # ---- the genuine persisted file is untouched and still admitted after the failed attempts ---------------------------------------------------------
    H.check("the genuine persisted run.json is byte-identical after all attempts", rr.path.read_bytes() == written)
    r3 = restart_reload(rr.path)
    b3, _ = H.import_f4(json.loads(r3["bytes"]), rr.operator, proposal=rr.proposal, verifier=H.Spy())
    H.check("after the refusals a fresh reload of the genuine file is still admitted (the refusals were caused by the mutation, not by the fixture)", b3 is not None and r3["bytes"] == written)
    H.note("proves", "persistence and restart do not let substituted or edited critical evidence acquire admission; the control is the Registry verifier at Replay admission, the store only round-trips bytes")
