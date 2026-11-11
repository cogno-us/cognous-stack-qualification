"""Subprocess probe: authority writer (trust-snapshot sync, which is also the revocation path) in its own OS process.
Hook keys are `<store stage>` or `<store stage>@<n>` (n-th occurrence). Prints one line  V08PROBE <json>.  SPDX-License-Identifier: Apache-2.0"""
import json
import os
import sys
import time
from pathlib import Path

spec = json.load(open(sys.argv[1]))
COMP = Path(spec["comp"])
for p in (COMP / "runtime" / "tests", COMP / "runtime", COMP / "control_plane" / "src"):
    sys.path.insert(0, str(p))
os.environ["OCS_REGISTRY_PIN_DIR"] = str(COMP / "registry")
out = {"label": spec["label"], "pid": os.getpid()}


def log(name, **kw):
    line = json.dumps({"label": spec["label"], "pid": os.getpid(), "name": name, "t": time.monotonic_ns(), **kw}) + "\n"
    fd = os.open(spec["events"], os.O_WRONLY | os.O_APPEND | os.O_CREAT)
    try:
        os.write(fd, line.encode())
    finally:
        os.close(fd)


def wait_file(path, limit=90.0):
    end = time.monotonic() + limit
    while not os.path.exists(path):
        if time.monotonic() > end:
            raise TimeoutError("barrier file never appeared: " + path)
        time.sleep(0.003)


def run_ops(ops):
    for op in ops:
        if op[0] == "event":
            log(op[1])
        elif op[0] == "wait":
            wait_file(op[1])
        elif op[0] == "exit":
            os._exit(9)


try:
    import test_registry_selection_authority as v4
    from engine.local_authority_effect import AtomicAuthorityEffectDestination

    base = Path(spec["base"])
    dest = AtomicAuthorityEffectDestination(base / "dest", clock=lambda: v4.r.NOW)
    store = dest.configure_selection_authority(base / "anchor.json")
    seen = {}

    def stage(name):
        seen[name] = seen.get(name, 0) + 1
        log(f"store:{name}#{seen[name]}")
        run_ops(spec["hooks"].get(f"{name}@{seen[name]}") or spec["hooks"].get(name) or [])

    store._stage = stage
    log("ready")
    if spec.get("go"):
        wait_file(spec["go"])
    log("go")
    results = []
    for version in spec["versions"]:
        log("sync_start", version=version)
        t = v4.trust(version, revoked_selections=frozenset(tuple(x) for x in spec.get("revoked", [])))
        res = dest.sync_selection("snapshot", trust=t)
        log("sync_returned", version=version)
        results.append({"version": version, "activation_sequence": res.activation_sequence, "n_entries": len(res.entry_hashes),
                        "anchor_advanced": res.anchor_advanced})
    out["results"] = results
except BaseException as exc:  # noqa: BLE001
    out["exception"] = f"{type(exc).__name__}: {str(exc)[:300]}"
print("V08PROBE " + json.dumps(out, default=str), flush=True)
