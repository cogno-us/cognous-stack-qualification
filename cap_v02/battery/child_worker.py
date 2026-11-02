"""A REAL separate Python process of the CAP v0.1 G2 battery. It shares NOTHING with the test process except the files on disk (configuration, pinned snapshot, state store, lock).

usage: python -I child_worker.py '<json spec>'      (CAP_SRC_DIR points at the pinned checkouts)
ops: admit (one PinnedSelectionSource call over real material), read (read_state), hold (hold the store's flock), bootstrap (bootstrap_state).
Failure injection (only in the child, never in the unit): crash=before_replace (os._exit between the temp write and os.replace), crash_on_link=N (os._exit on the Nth os.link),
fail_write (os.replace raises OSError). `go_file`: wait until that path exists (a start barrier so that N children contend at the same instant).
Prints ONE final JSON line.
"""
import dataclasses
import fcntl
import json
import os
import sys
import time
from pathlib import Path

spec = json.loads(sys.argv[1])
SRC = Path(os.environ["CAP_SRC_DIR"]).resolve()
for entry in reversed([SRC / "control_plane", SRC / "control_plane" / "src", SRC / "replay" / "src", SRC / "registry", SRC / "registry" / "baseline" / "execution-runtime"]):
    sys.path.insert(0, str(entry))

import agent_control_plane.registry_authority_profile as AP  # noqa: E402
import agent_control_plane.registry_authority_state as ST  # noqa: E402
from agent_control_plane.registry_f4_age_governance import SelectionMaterial  # noqa: E402
from registry_adapters import ed25519_verifier as ev  # noqa: E402

DONE = {"pid": os.getpid()}


def emit(**kw):
    DONE.update(kw)
    print(json.dumps(DONE, sort_keys=True), flush=True)


if spec.get("go_file"):
    deadline = time.monotonic() + 60
    while not os.path.exists(spec["go_file"]):
        if time.monotonic() > deadline:
            emit(ok=False, code="child_barrier_timeout")
            sys.exit(3)
        time.sleep(0.002)

if spec.get("crash") == "before_replace":
    def _crash(*a, **k):
        os._exit(97)
    os.replace = _crash
if spec.get("fail_write"):
    def _fail(*a, **k):
        raise OSError(28, "injected: no space left on device")
    os.replace = _fail
if spec.get("crash_on_link"):
    _real_link, _n = os.link, {"n": 0}

    def _link(*a, **k):
        _n["n"] += 1
        if _n["n"] >= spec["crash_on_link"]:
            os._exit(98)
        return _real_link(*a, **k)
    os.link = _link


def profile():
    p = AP.load_authority_profile(spec["config"], expected_mode="synthetic", expected_config_digest=spec["digest"])
    if spec.get("as_of"):
        p = dataclasses.replace(p, as_of=spec["as_of"])
    return p


try:
    op = spec["op"]
    if op == "admit":
        p = profile()
        trust, _fp = AP.load_pinned_trust(p)
        host = lambda: SelectionMaterial(spec["record"], spec["selection"], trust)  # noqa: E731
        w = AP.PinnedSelectionSource(p, host, ev.Ed25519Verifier(), expected_mode="synthetic", expected_config_digest=spec["digest"])
        try:
            w()
            emit(ok=True, code=None)
        except AP.AuthorityProfileRefusal as e:
            emit(ok=False, code=e.code, registry_code=e.refusal.registry_code, detail=str(e.detail)[:200])
    elif op == "modules":
        import registry_conformance.highwater as _hw
        import registry_successor.v2_verified_selection as _vs
        import nacl
        emit(ok=True, files={m.__name__: m.__file__ for m in (AP, ST, _hw, _vs, ev, nacl)}, pynacl=nacl.__version__)
    elif op == "read":
        emit(ok=True, envelope=ST.read_state(profile()))
    elif op == "hold":
        p = profile()
        fd = os.open(p.state_path + ".lock", os.O_RDWR | os.O_CREAT, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX)
        emit(ok=True, locked=True)
        time.sleep(spec.get("seconds", 5))
    elif op == "bootstrap":
        p = profile()
        from datetime import datetime, timezone
        now = datetime.strptime(spec["now"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        try:
            env = ST.bootstrap_state(p, spec["bootstrap"], now)
            emit(ok=True, generation=env["generation"])
        except AP.AuthorityProfileRefusal as e:
            emit(ok=False, code=e.code, detail=str(e.detail)[:200])
    else:
        emit(ok=False, code="child_unknown_op")
except SystemExit:
    raise
except BaseException as e:  # noqa: BLE001
    emit(ok=False, code="child_exception", detail=f"{type(e).__name__}: {e}"[:300])
