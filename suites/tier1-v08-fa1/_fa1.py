"""V08 F-A1 qualification rig (Registry r08-v2 Amendment 4). Fixture mechanics only; assertions live in the test modules.

Composition (nothing here re-implements a component):
  * the historical V08 chain `suites/tier1-v08/authority/_wf.py` (imported unchanged): a real Control Plane BoundedAuthorizationWorkflow decision, claims issued by
    `provision_local_execution_claim`, and a Runtime governed store activated through the Registry;
  * the Control Plane export `agent_control_plane.authorization_pin_export.assess_authorization_pin` on the PERSISTED decision (never a claim);
  * the REAL trusted installer `host.authorization_pin.TrustedAuthorizationInstaller` (the only writer of the pin store, anchor and fences);
  * a Runtime destination built with the host-configured `authorization_pin` option, which reads the pin read-only.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import contextlib
import copy
import fcntl
import json
import os
import sqlite3
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_HIST = _HERE / "_historical"   # byte-identical vendored copy of the helper at 7b72de9 (digest enforced by conftest)
if str(_HIST) not in sys.path:
    sys.path.insert(0, str(_HIST))

import _wf as w  # noqa: E402  (historical V08 helper, reused unchanged)

import agent_control_plane.authorization_pin_export as cp_export  # noqa: E402
from engine import authorization_pin_format as fmt  # noqa: E402
from engine.authorization_pin import AuthorizationPinConfig, PinReader  # noqa: E402
from engine.local_authority_effect import AtomicAuthorityEffectDestination  # noqa: E402
from host.authorization_pin import InstallerConfig, TrustedAuthorizationInstaller  # noqa: E402

STORE_ID = "fa1-qual-store"
EXPORT_PROFILE = cp_export.PIN_EXPORT_PROFILE
PIN_CAUSE_PREFIX = "pin_"


def verdict_of(*parts) -> str:
    if "BREACH" in parts:
        return "BREACH"
    if all(p == "HELD" for p in parts):
        return "HELD"
    if "BLOCKED" in parts:
        return "BLOCKED"
    return "INCONCLUSIVE"


class Rig:
    """One governed Runtime store, one real Control Plane decision, one real installer and one pin-required destination."""

    def __init__(self, tmp_path, *, payload=None, policy_sets=None, deadline=1.0, installer_deadline=0.4, generation=None, second_operation=False, dest_cls=None):
        tmp_path = Path(tmp_path)
        self.tmp = tmp_path
        self.scope2 = w.aligned_scope(operation="op-other") if second_operation else None
        self.env = w.AEnv(tmp_path / "rt", payload=payload)
        if self.scope2:
            self.env.add_scope(self.scope2)
        self.env.boot()
        self.rec = self.env.record()
        self.stmt = self.env.statement(self.rec)
        self.env.activate_stmt(self.stmt, self.rec)
        self.state = self.env.state()
        self.sets = policy_sets or w.needed_payload()
        self.binding = w.binding_for(self.env, self.state, self.sets)
        self.iss = w.Issued(tmp_path / "cp", self.binding, generation=generation or self.state.policy_generation)
        self.pins = tmp_path / "pins"
        self.pins.mkdir(exist_ok=True)
        self.icfg = InstallerConfig(pin_store_path=self.pins / "pins.sqlite3", fence_dir=self.pins / "fences", anchor_path=self.pins / "pins.anchor.json",
                                    log_path=self.pins / "installer.log", pin_store_id=STORE_ID, exclusive_deadline_seconds=installer_deadline)
        self.installer = TrustedAuthorizationInstaller(self.icfg)
        self.gcfg = AuthorizationPinConfig(pin_store_path=self.icfg.pin_store_path, fence_dir=self.icfg.fence_dir, anchor_path=self.icfg.anchor_path,
                                           pin_store_id=STORE_ID, fence_deadline_seconds=deadline)
        cls = dest_cls or AtomicAuthorityEffectDestination
        self.dest = cls(self.env.root, clock=lambda: self.env.now, authorization_pin=self.gcfg)
        self.dest.configure_selection_authority(self.env.anchor)
        self.n = 0

    # ---- Control Plane export (persisted decision) -> real installer
    def assessment(self, iss=None):
        iss = iss or self.iss
        return cp_export.assess_authorization_pin(iss.workflow, iss.p, iss.decision, now=w.CP_NOW, host_policy_binding=iss.binding)

    def install(self, iss=None):
        return self.installer.apply_assessment(self.assessment(iss))

    def revoke_in_control_plane(self, iss=None):
        iss = iss or self.iss
        iss.resolver.statuses[iss.decision.binding.grant_id].status = "revoked"

    @staticmethod
    def terminal_assessment(decision_id, status="revoked", reason="qualification"):
        return {"profile": EXPORT_PROFILE, "decision_id": decision_id, "state": "terminal", "payload": None, "terminal_status": status, "reason": reason}

    # ---- claims and execution (real functions)
    def claim(self, iss=None, claim_id=None, binding="own"):
        iss = iss or self.iss
        self.n += 1
        cid = claim_id or f"fa1-claim-{self.n}"
        iss.provision(self.dest, claim_id=cid, binding=binding)
        return cid

    def run(self, cid, iss=None, policy=None, dest=None):
        iss = iss or self.iss
        return w.executor(dest or self.dest, policy or w.policy_from(self.sets)).execute(envelope=iss.envelope, claim_id=cid)

    def counts(self):
        return w.counts(self.dest)

    @property
    def decision_id(self):
        return self.iss.decision.decision_id

    def rows(self, decision_id=None):
        return PinReader(self.gcfg).rows_for(decision_id or self.decision_id)

    def typed(self, res):
        return w.refusal_of(res)


def judge(res, counts, code, cls, cause=None, *, alt=()):
    """HELD only on positive evidence: nothing committed, status denied, and the typed triple is the intended one (or an explicitly allowed alternative).
    A cause ending in `*` is a prefix match (e.g. `pin_binding_mismatch:*`)."""
    typed = w.refusal_of(res)
    if counts["effects"] or counts["attempts"] or counts["authority_effect_receipts_v1"] or counts["budget_used"] or res.status == "executed" or res.attempted:
        return "BREACH", typed
    got = (typed or {}).get("code"), (typed or {}).get("refusal_class"), (typed or {}).get("cause")
    for want in [(code, cls, cause), *alt]:
        cause_ok = want[2] is None or (got[2] is not None and (got[2].startswith(want[2][:-1]) if want[2].endswith("*") else got[2] == want[2]))
        if res.status == "denied" and typed and got[0] == want[0] and got[1] == want[1] and cause_ok:
            return "HELD", typed
    return "INCONCLUSIVE", typed


def recompute_claim(raw: dict) -> dict:
    """A colluding supplier recomputes EVERY commitment the claim model verifies after rewriting members."""
    raw = copy.deepcopy(raw)
    raw.pop("claim_commitment", None)
    raw["approval_state_commitment"] = w.cp_commitment(raw["approval_state"])
    raw["policy_state_commitment"] = w.cp_commitment(raw["policy_state"])
    raw["evidence_state_commitment"] = w.cp_commitment(raw["evidence_state"])
    raw["authority_state_commitment"] = w.cp_commitment({
        "grant_id": raw["grant_id"], "grant_revision": raw["grant_revision"], "grant_status": raw["grant_status"],
        "requirement_commitment": raw["requirement_commitment"], "approvals": raw["approval_state"], "policies": raw["policy_state"],
        "evidence": raw["evidence_state"]})
    raw["claim_commitment"] = w.cp_commitment(raw)
    return raw


def fence_free(path: Path) -> bool:
    """True when no shared holder remains on the per-decision fence (probe with a non-blocking exclusive flock on a read-only descriptor)."""
    fd = os.open(path, os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(fd, fcntl.LOCK_UN)
        return True
    except BlockingIOError:
        return False
    finally:
        os.close(fd)


def fence_of(rig: Rig, decision_id=None) -> Path:
    return fmt.fence_path(rig.icfg.fence_dir, decision_id or rig.decision_id)


@contextlib.contextmanager
def holder(path: Path, kind="sh"):
    """A REAL separate process holding a flock on the fence through a read-only descriptor, like an executor mid-effect."""
    import subprocess
    code = ("import fcntl,os,sys;fd=os.open(sys.argv[1],os.O_RDONLY);"
            "fcntl.flock(fd,fcntl.LOCK_SH if sys.argv[2]=='sh' else fcntl.LOCK_EX);print('ready',flush=True);sys.stdin.read()")
    p = subprocess.Popen([sys.executable, "-I", "-c", code, str(path), kind], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    try:
        assert p.stdout.readline().strip() == "ready"
        yield p
    finally:
        with contextlib.suppress(Exception):
            p.stdin.close()
        p.wait(timeout=15)


def sql(path, statement, params=()):
    conn = sqlite3.connect(path, isolation_level=None)
    try:
        return conn.execute(statement, params).fetchall()
    finally:
        conn.close()


def dump(obj):
    return json.loads(json.dumps(obj, default=str))


def unrelated(rig: Rig, n: int = 2):
    """A second, UNRELATED decision derived from the honest one: new decision_id/effect_id (claim re-committed, envelope re-id'd) with its own pin installed
    through the real installer from an assessment whose payload is the honest payload with those two ids. The Control Plane fixture cannot mint a second
    decision with a distinct effect_id, so this decision is synthetic by construction and is recorded as such in the evidence."""
    import dataclasses
    did, eid = f"{rig.decision_id}-unrelated-{n}", f"{rig.iss.decision.effect_id}-unrelated-{n}"
    honest = rig.iss.materialize(claim_id=f"tmpl-{n}")
    raw = w.forged_from(honest, claim_id=f"unrel-{n}", top_changes={"decision_id": did, "effect_id": eid})
    raw = recompute_claim(raw)
    env = rig.iss.envelope
    envelope = type(env)(w.EXECUTION_ENVELOPE_VERSION, did, eid, env.operation)
    payload = {**rig.assessment()["payload"], "decision_id": did, "effect_id": eid}
    assessment = {"profile": EXPORT_PROFILE, "decision_id": did, "state": "active", "payload": payload, "terminal_status": None, "reason": "synthetic unrelated decision"}
    return types_ns(decision_id=did, effect_id=eid, claim=raw, envelope=envelope, assessment=assessment, claim_id=raw["claim_id"])


def types_ns(**kw):
    import types
    return types.SimpleNamespace(**kw)


def consistent_forgery(rig: Rig, claim_id: str, *, op_changes=None, top_changes=None, binding_changes=None):
    """A colluding supplier forges a claim AND the matching envelope consistently (operation_commitment and every state commitment recomputed from the
    altered operation), so the Runtime's existing claim-state validation passes and only the pin can tell. Returns (raw_claim, envelope)."""
    import dataclasses
    from engine.safe_executor import snapshot_envelope
    honest = rig.iss.materialize(claim_id=claim_id)
    env = rig.iss.envelope
    op = dataclasses.replace(env.operation, **(op_changes or {}))
    envelope = type(env)(w.EXECUTION_ENVELOPE_VERSION, env.decision_id, env.effect_id, op)
    raw = honest.model_dump(mode="json", exclude_none=False)
    raw.pop("claim_commitment")
    raw.update(top_changes or {})
    if binding_changes:
        raw["policy_binding"] = {**raw["policy_binding"], **binding_changes}
    raw["operation_commitment"] = AtomicAuthorityEffectDestination._operation_commitment(snapshot_envelope(envelope))
    return recompute_claim(raw), envelope
