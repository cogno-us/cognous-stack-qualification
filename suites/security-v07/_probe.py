"""Subprocess probes for the V07 assessment (separate OS processes: races, crashes, older/other dependency environments).
Prints exactly one line:  V07PROBE <json>.   SPDX-License-Identifier: Apache-2.0
"""
import json
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

mode = sys.argv[1]
out = {"mode": mode, "pid": os.getpid()}


def emit():
    print("V07PROBE " + json.dumps(out, sort_keys=True, default=str))


def dest_for(tmp, stage_hook=None):
    import test_registry_selection_authority as v4
    from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor  # noqa: F401
    from engine.local_authority_effect import AtomicAuthorityEffectDestination
    cls = AtomicAuthorityEffectDestination
    if stage_hook:
        class Hooked(AtomicAuthorityEffectDestination):
            def _transaction_stage(self, stage):
                stage_hook(stage)
        cls = Hooked
    dest = cls(Path(tmp) / "dest", clock=lambda: v4.r.NOW)
    dest.configure_selection_authority(Path(tmp) / "anchor.json")
    return dest


if mode == "withdraw":
    import test_registry_selection_authority as v4
    e = v4.Env(sys.argv[2])
    e.trust = v4.trust(1)
    time.sleep(float(sys.argv[3]))
    e.withdraw(v4.withdraw_stmt(v4.select_stmt(v4.REC), 2))
    out["withdrawn_at"] = time.time()
    out["head"] = e.head()
elif mode in ("exec_one", "crash"):
    import test_registry_selection_effect_guard as g
    from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor
    tmp, cid = sys.argv[2], sys.argv[3]
    hook = None
    if mode == "crash":
        stage = sys.argv[4]
        hook = lambda s: os._exit(9) if s == stage else None  # noqa: E731
    dest = dest_for(tmp, hook)
    if mode == "exec_one":
        while time.time() < float(sys.argv[4]):
            time.sleep(0.005)
    try:
        res = AtomicLocalControlPlaneExecutor(workflow=None, destination=dest, policy=g.effect_policy()).execute(envelope=g.envelope(), claim_id=cid)
        out["status"] = res.status
        out["typed"] = res.control_plane_evidence.get("selection_refusal")
    except BaseException as exc:  # noqa: BLE001
        out["error"] = type(exc).__name__ + ": " + str(exc)[:200]
elif mode in ("successor_old", "successor_211"):
    # a successor-profile claim presented where the Control Plane cannot express it (older pin / pydantic 2.11.9 with V02)
    import test_atomic_route_valid_flow_identity as flow
    from agent_control_plane.bounded import commitment
    from engine.local_authority_effect import AtomicAuthorityEffectDestination, SUCCESSOR_PROFILE_NAME
    out["pydantic"] = __import__("pydantic").VERSION
    env = flow.envelope()
    raw = flow.make_claim(env)
    if not isinstance(raw, dict):
        raw = json.loads(raw.model_dump_json())
    raw.pop("claim_commitment", None)
    raw["profile"] = SUCCESSOR_PROFILE_NAME
    raw["policy_binding"] = {"binding_profile": "ocs-policy-binding/1"}
    raw["claim_commitment"] = commitment(raw)
    with tempfile.TemporaryDirectory() as tmp:
        dest = AtomicAuthorityEffectDestination(Path(tmp) / "d", clock=lambda: __import__("datetime").datetime(2026, 10, 1, tzinfo=__import__("datetime").timezone.utc))
        try:
            dest.provision_claim(raw)
            out["provision"] = "accepted"
        except BaseException as exc:  # noqa: BLE001
            out["provision"] = "refused"
            out["error_type"] = type(exc).__name__
            out["error"] = str(exc)[:240]
        with sqlite3.connect(dest.path) as conn:
            out["effects"] = conn.execute("SELECT COUNT(*) FROM effects").fetchone()[0]
            out["claims"] = conn.execute("SELECT COUNT(*) FROM execution_claims_v1").fetchone()[0]
elif mode == "cp_issue":
    # Control Plane V02 issuance: a binding whose digest the approval did not commit to must be refused
    import tempfile as _t
    from agent_control_plane.local_authority_effect import materialize_local_execution_claim
    from tests.v02_support import CONSUMER, OPERATION, TENANT_NOW, canonical_binding, sha, tenant_flow
    binding = canonical_binding()
    with _t.TemporaryDirectory() as tmp:
        p, r, f, d, cfg = tenant_flow(Path(tmp), binding)
        try:
            ok = materialize_local_execution_claim(f, p, d, now=TENANT_NOW, policy_binding=binding, expected_consumer_id=CONSUMER, expected_operation=OPERATION)
            out["honest"] = "issued" if ok.policy_binding else "issued_without_binding"
        except BaseException as exc:  # noqa: BLE001
            out["honest"] = "refused: " + str(exc)[:160]
        bad = dict(binding, effective_policy_digest=sha("f"))
        try:
            materialize_local_execution_claim(f, p, d, now=TENANT_NOW, policy_binding=bad, expected_consumer_id=CONSUMER, expected_operation=OPERATION)
            out["tampered"] = "issued"
        except BaseException as exc:  # noqa: BLE001
            out["tampered"] = "refused: " + type(exc).__name__ + " " + str(exc)[:160]
emit()
