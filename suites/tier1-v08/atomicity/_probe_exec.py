"""Subprocess probe: one executor attempt (AtomicLocalControlPlaneExecutor.execute) in its own OS process.
Prints exactly one line  V08PROBE <json>.  Hooks are interpreted at `_transaction_stage` seams. SPDX-License-Identifier: Apache-2.0"""
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
        elif op[0] == "raise":
            raise OSError(op[1])


try:
    import test_registry_selection_authority as v4
    import test_registry_selection_effect_guard as g
    import test_atomic_route_valid_flow_identity as flow
    import dataclasses
    from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor
    from engine.local_authority_effect import AtomicAuthorityEffectDestination
    from engine.safe_executor import EXECUTION_ENVELOPE_VERSION, ExecutionEnvelope

    class D(AtomicAuthorityEffectDestination):
        def _transaction_stage(self, stage):
            log("stage:" + stage)
            run_ops(spec["hooks"].get(stage, []))

    base = Path(spec["base"])
    i = spec["index"]
    op = dataclasses.replace(flow.operation(), **{**g.op_changes(), "effective_max_effects": spec["max_effects"]})
    env = ExecutionEnvelope(EXECUTION_ENVELOPE_VERSION, f"decision-{i}", f"effect-{i}", op)
    dest = D(base / "dest", clock=lambda: v4.r.NOW)
    dest.configure_selection_authority(base / "anchor.json")
    log("ready")
    if spec.get("go"):
        wait_file(spec["go"])
    log("go")
    res = AtomicLocalControlPlaneExecutor(workflow=None, destination=dest, policy=g.effect_policy()).execute(
        envelope=env, claim_id=f"claim-{i}", attempt_id=spec["attempt_id"])
    cpe = res.control_plane_evidence or {}
    rec = cpe.get("authority_receipt") or {}
    out.update(status=res.status, error=res.error, observed_state=res.observed_state, newly_executed=res.newly_executed, attempted=res.attempted,
               typed=cpe.get("selection_refusal"), failure_class=cpe.get("failure_class"),
               receipt_head=(rec.get("selection_guard") or {}).get("log_head_sequence"), attempt_id=spec["attempt_id"])
except BaseException as exc:  # noqa: BLE001
    out["exception"] = f"{type(exc).__name__}: {str(exc)[:300]}"
log("returned")
print("V08PROBE " + json.dumps(out, default=str), flush=True)
