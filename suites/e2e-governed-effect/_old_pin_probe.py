"""Run under the INTENTIONALLY OLDER Control Plane pin (no successor profile). Prints one JSON line.

modes: legacy_executes | successor_refused
SPDX-License-Identifier: Apache-2.0
"""
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

mode = sys.argv[1]
import agent_control_plane.local_authority_effect as cp  # noqa: E402

import test_registry_selection_effect_guard as g  # noqa: E402  (Runtime fixtures)
from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor  # noqa: E402
from engine.local_authority_effect import AtomicAuthorityEffectDestination, SUCCESSOR_PROFILE_NAME  # noqa: E402
from agent_control_plane.bounded import commitment  # noqa: E402

out = {"has_successor_symbol": hasattr(cp, "LOCAL_AUTHORITY_EFFECT_PROFILE_V2"), "cp_file": cp.__file__}
now = g.v4.r.NOW
env = g.envelope(tenant_id=None)
with tempfile.TemporaryDirectory() as tmp:
    dest = AtomicAuthorityEffectDestination(Path(tmp) / "d", clock=lambda: now)
    raw = g.make_claim(env, now, binding=None, claim_id="old-pin-1")
    if mode == "successor_refused":
        raw.pop("claim_commitment")
        raw["profile"] = SUCCESSOR_PROFILE_NAME
        raw["claim_commitment"] = commitment(raw)
    try:
        dest.provision_claim(raw)
        out["provision"] = "accepted"
    except Exception as exc:  # noqa: BLE001
        out["provision"] = "refused"
        out["error_type"] = type(exc).__name__
        out["error"] = str(exc)[:300]
    if out["provision"] == "accepted":
        res = AtomicLocalControlPlaneExecutor(workflow=None, destination=dest, policy=g.effect_policy()).execute(envelope=env, claim_id="old-pin-1")
        out["status"] = res.status
    with sqlite3.connect(dest.path) as conn:
        out["effects"] = conn.execute("SELECT COUNT(*) FROM effects").fetchone()[0]
        out["claims"] = conn.execute("SELECT COUNT(*) FROM execution_claims_v1").fetchone()[0]
print("V06PROBE " + json.dumps(out, sort_keys=True))
