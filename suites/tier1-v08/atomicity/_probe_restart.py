"""Subprocess probe (restart): re-open an existing store in a NEW process, exercise the host anchor, then execute claim-1.
Prints one line  V08PROBE <json>.  SPDX-License-Identifier: Apache-2.0"""
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
try:
    import dataclasses
    import test_registry_selection_authority as v4
    import test_registry_selection_effect_guard as g
    import test_atomic_route_valid_flow_identity as flow
    from engine import registry_selection_authority as sa
    from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor
    from engine.local_authority_effect import AtomicAuthorityEffectDestination
    from engine.safe_executor import EXECUTION_ENVELOPE_VERSION, ExecutionEnvelope

    base = Path(spec["base"])
    anchor_path = base / "anchor.json"
    dest = AtomicAuthorityEffectDestination(base / "dest", clock=lambda: v4.r.NOW)
    dest.configure_selection_authority(anchor_path)
    st = dest.verify_selection_store()
    out["verify"] = [st.state, st.cause, st.head_sequence]
    hf = sa.HostAnchorFile(anchor_path)
    a0 = hf.read()
    b0 = anchor_path.read_bytes()
    out["anchor_head_before"] = a0["head_sequence"]
    older = spec["older_anchor"]
    out["advance_older"] = hf.advance(older)
    out["bytes_same_after_older"] = anchor_path.read_bytes() == b0
    conflict = dict(a0, head_entry_hash="sha256:" + "9" * 64)
    try:
        out["advance_conflict"] = hf.advance(conflict)
    except sa.ReplayError as exc:
        out["advance_conflict"] = "ReplayError:" + str(exc)
    out["bytes_same_after_conflict"] = anchor_path.read_bytes() == b0
    op = dataclasses.replace(flow.operation(), **{**g.op_changes(), "effective_max_effects": 1})
    env = ExecutionEnvelope(EXECUTION_ENVELOPE_VERSION, "decision-1", "effect-1", op)
    res = AtomicLocalControlPlaneExecutor(workflow=None, destination=dest, policy=g.effect_policy()).execute(
        envelope=env, claim_id="claim-1", attempt_id="att-restart")
    cpe = res.control_plane_evidence or {}
    out.update(status=res.status, error=res.error, typed=cpe.get("selection_refusal"),
               receipt_head=((cpe.get("authority_receipt") or {}).get("selection_guard") or {}).get("log_head_sequence"))
    out["anchor_head_after"] = hf.read()["head_sequence"]
except BaseException as exc:  # noqa: BLE001
    out["exception"] = f"{type(exc).__name__}: {str(exc)[:300]}"
print("V08PROBE " + json.dumps(out, default=str), flush=True)
