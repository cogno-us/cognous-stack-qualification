"""V06 — end-to-end governed-effect qualification (bounded, synthetic, local).

Chain exercised:  Registry selection (pin 943ab183)  ->  Control Plane claim models and commitment (V02 1bee3696)
                  ->  Runtime durable selection authority (V05 4199a6c7)  ->  atomic effect-time guard  ->  effect or refusal  ->  evidence.

Predeclared oracles (expected outcome stated per case, before execution):
  D*  dependency/missing-support    A*  valid governed effect       B*  withdrawal/revocation
  R*  authority-to-effect race      S*  stale generation / binding  P*  policy narrowing
  L*  legacy bypass                 G*  trust, corruption, evidence atomicity

Reuses the Runtime's own fixtures (Registry builders, `Gov`, claim builder) by import; adds no new execution path, authority store or
policy family. Claims are built from the Control Plane's own models and commitment function and verified by them at provisioning;
issuance through the Control Plane workflow is NOT exercised here (see README known limits).
No network, subprocess-to-service, credential or real-world effect; the destination is synthetic SQLite.
Builder-authored; not independent attestation; not a production security qualification.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path

import pydantic
import pytest

import agent_control_plane.local_authority_effect as cp_effect
from conftest import COMPONENTS, PINS, head_of
import test_registry_selection_effect_guard as g  # Runtime fixtures (imported, not re-implemented)
from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor
from engine.local_authority_effect import AtomicAuthorityEffectDestination

v4 = g.v4
PROBE = Path(__file__).resolve().parent / "_old_pin_probe.py"
EXEC = AtomicLocalControlPlaneExecutor


def run_executor(dest, env, cid, policy=None):
    return EXEC(workflow=None, destination=dest, policy=policy or g.effect_policy()).execute(envelope=env, claim_id=cid)


def note_refusal(ev, result, gov):
    ev["observed"].update(status=result.status, attempted=result.attempted, selection_refusal=result.control_plane_evidence.get("selection_refusal"),
                          counts_effects_attempts_receipts_budget=gov.counts())


def old_pin(mode):
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(COMPONENTS / "runtime" / "tests"), str(COMPONENTS / "runtime"),
                                         str(COMPONENTS / "control_plane_legacy" / "src")])
    cp = subprocess.run([sys.executable, "-I", str(PROBE), mode], env={**env, "PYTHONSAFEPATH": ""}, capture_output=True, text=True, timeout=120)
    line = [x for x in cp.stdout.splitlines() if x.startswith("V06PROBE ")]
    assert line, (cp.returncode, cp.stdout[-800:], cp.stderr[-1200:])
    return json.loads(line[-1][len("V06PROBE "):])


# ============================================================================================ D: dependencies and missing support
def test_d01_exact_component_pins_and_successor_capable_environment(ev):
    """Expected: every imported component comes from its accepted pin; V02 successor constant present; pydantic >= 2.12."""
    ev["expected"] = "components at accepted pins; successor profile symbol present; pydantic>=2.12"
    heads = {k: head_of(COMPONENTS / k) for k in PINS}
    assert heads == PINS
    assert Path(cp_effect.__file__).resolve().is_relative_to((COMPONENTS / "control_plane").resolve())
    assert Path(g.sa.__file__).resolve().is_relative_to((COMPONENTS / "runtime").resolve())
    assert Path(v4.PIN_DIR).resolve() == (COMPONENTS / "registry").resolve()
    assert hasattr(cp_effect, "LOCAL_AUTHORITY_EFFECT_PROFILE_V2")
    assert tuple(int(x) for x in pydantic.VERSION.split(".")[:2]) >= (2, 12)
    ev["observed"].update(pins=heads, pydantic=pydantic.VERSION, cp_module=cp_effect.__file__)


def test_d02_legacy_compatibility_claim_executes_on_the_older_control_plane_pin(ev):
    """Expected: LEGACY COMPATIBILITY (not successor qualification): a legacy claim executes against the real older Control Plane."""
    ev["expected"] = "older CP has no successor symbol; legacy claim provisioned and executed; one effect"
    out = old_pin("legacy_executes")
    ev["observed"] = out
    assert out["has_successor_symbol"] is False and out["provision"] == "accepted" and out["status"] == "executed" and out["effects"] == 1
    assert str(COMPONENTS / "control_plane_legacy") in out["cp_file"]


def test_d03_successor_claim_is_refused_not_downgraded_on_the_older_control_plane_pin(ev):
    """Expected: the missing-support regression, against the real older Control Plane: the successor profile is refused, nothing stored."""
    ev["expected"] = "PermissionError/ValidationError at provisioning; zero claims; zero effects; no downgrade to the legacy profile"
    out = old_pin("successor_refused")
    ev["observed"] = out
    assert out["has_successor_symbol"] is False and out["provision"] == "refused" and out["error_type"] in ("PermissionError", "ValidationError")
    assert out["claims"] == 0 and out["effects"] == 0


def test_d04_successor_profile_claim_without_a_binding_is_refused_on_v02(tmp_path, ev):
    """Expected (successor qualification against V02): the successor profile with no policy binding never reaches an effect."""
    ev["expected"] = "refused at provisioning or by the guard; no effect"
    gov = g.Gov(tmp_path)
    env = g.envelope()
    raw = g.make_claim(env, gov.now, binding=g.binding_of(gov.state()), claim_id="nobinding-1")
    raw.pop("policy_binding")
    raw.pop("claim_commitment")
    raw["claim_commitment"] = g.cp_commitment(raw)
    with pytest.raises((PermissionError, ValueError)) as info:  # ValueError: pydantic ValidationError from the V02 claim model
        gov.dest.provision_claim(raw)
    ev["observed"].update(error=str(info.value)[:200], counts=gov.counts())
    assert gov.counts() == (0, 0, 0, 0)


# ============================================================================================ A: valid governed effect
def test_a01_valid_bound_claim_commits_the_synthetic_effect(tmp_path, ev):
    ev["expected"] = "status executed; exactly one effect"
    gov = g.Gov(tmp_path)
    env, cid, result = gov.run()
    ev["observed"].update(status=result.status, counts=gov.counts())
    assert result.status == "executed" and gov.counts()[0] == 1


def test_a02_the_atomic_receipt_retains_the_guard_evidence_and_equals_the_returned_one(tmp_path, ev):
    ev["expected"] = "retained receipt == returned receipt; selection_guard present with log head"
    gov = g.Gov(tmp_path)
    env, cid, result = gov.run()
    returned = result.control_plane_evidence["authority_receipt"]
    retained = json.loads(gov.receipt())
    ev["observed"].update(receipt=retained)
    assert retained == returned and retained["selection_guard"]["result"] == "binding_verified"
    assert retained["selection_guard"]["log_head_hash"] and retained["selection_guard"]["independent_attestation"] is False


def test_a03_the_receipt_binds_the_activation_generation_and_trust_snapshot(tmp_path, ev):
    ev["expected"] = "guard evidence names the active activation_ref, policy_generation and snapshot version"
    gov = g.Gov(tmp_path)
    st = gov.state()
    guard = gov.run()[2].control_plane_evidence["authority_receipt"]["selection_guard"]
    ev["observed"].update(guard=guard)
    assert guard["activation_ref"] == st.activation_ref and guard["policy_generation"] == st.policy_generation
    assert guard["selection_epoch"] == st.selection_epoch and guard["effective_policy_digest"] == v4.effective_digest()


def test_a04_optional_participation_selection_executes(tmp_path, ev):
    ev["expected"] = "executed; participation optional recorded"
    gov = g.Gov(tmp_path, participation="optional")
    result = gov.run()[2]
    ev["observed"].update(status=result.status, participation=result.control_plane_evidence["authority_receipt"]["selection_guard"]["participation"])
    assert result.status == "executed" and gov.counts()[0] == 1


# ============================================================================================ B: withdrawal / revocation
def test_b01_withdrawal_before_the_effect_refuses_without_an_effect(tmp_path, ev):
    ev["expected"] = "REFUSE selection_withdrawn; zero effects/attempts/receipts"
    gov = g.Gov(tmp_path)
    env, cid = gov.claim()
    gov.e.withdraw(v4.withdraw_stmt(gov.stmt, 2))
    result = run_executor(gov.dest, env, cid)
    note_refusal(ev, result, gov)
    g.refused(result, "selection_withdrawn", "REFUSE")
    assert gov.counts() == (0, 0, 0, 0)


def test_b02_selection_revocation_before_the_effect_refuses(tmp_path, ev):
    ev["expected"] = "REFUSE selection_revoked; zero effects"
    gov = g.Gov(tmp_path)
    env, cid = gov.claim()
    gov.e.sync(2, revoked_selections=frozenset({("sel-test-1", 1)}))
    result = run_executor(gov.dest, env, cid)
    note_refusal(ev, result, gov)
    g.refused(result, "selection_revoked", "REFUSE")
    assert gov.counts() == (0, 0, 0, 0)


def test_b03_issuer_key_revocation_before_the_effect_refuses(tmp_path, ev):
    ev["expected"] = "REFUSE issuer_key_revoked; zero effects"
    gov = g.Gov(tmp_path)
    env, cid = gov.claim()
    gov.e.sync(2, revoked_key_ids=frozenset({"key-test-1"}))
    result = run_executor(gov.dest, env, cid)
    note_refusal(ev, result, gov)
    g.refused(result, "issuer_key_revoked", "REFUSE")
    assert gov.counts() == (0, 0, 0, 0)


def test_b04_after_a_committed_effect_withdrawal_stops_every_subsequent_effect(tmp_path, ev):
    ev["expected"] = "first effect stands (not undone); a second claim after withdrawal refuses; effects stay at 1"
    gov = g.Gov(tmp_path)
    binding = g.binding_of(gov.state())
    first = gov.run(binding)[2]
    gov.e.withdraw(v4.withdraw_stmt(gov.stmt, 2))
    env2, cid2 = gov.claim(binding=binding, claim_id="claim-after-withdrawal")
    second = run_executor(gov.dest, env2, cid2)
    note_refusal(ev, second, gov)
    assert first.status == "executed" and gov.counts()[0] == 1
    g.refused(second, "selection_withdrawn", "REFUSE")
    assert gov.counts()[0] == 1


# ============================================================================================ R: authority-to-effect race
def _racer(g_, timeline, action):  # action(other_env, gov)
    """A second connection to the same durable store that performs one authority transition (it needs the BEGIN IMMEDIATE lock)."""
    other = v4.Env(g_.tmp)
    other.trust, other.now = g_.e.trust, g_.e.now
    def go():
        timeline.append(("transition_started", time.monotonic()))
        action(other, g_)
        timeline.append(("transition_committed", time.monotonic()))
    return threading.Thread(target=go)


def _race(tmp_path, ev, stage_to_race, action):
    gov = g.Gov(tmp_path)
    env, cid = gov.claim()
    timeline: list = []
    state = {}

    class Racing(AtomicAuthorityEffectDestination):
        def _transaction_stage(self, stage):
            timeline.append((stage, time.monotonic()))
            if stage == stage_to_race:
                t = _racer(gov, timeline, action)
                state["thread"] = t
                t.start()
                time.sleep(0.5)  # the lock is held by this transaction: the transition must still be waiting
                state["blocked_while_locked"] = t.is_alive()
            return None

    racing = Racing(gov.e.root, clock=lambda: gov.e.now)
    racing.configure_selection_authority(gov.e.anchor)
    result = run_executor(racing, env, cid)
    state["thread"].join(timeout=30)
    names = [n for n, _ in sorted(timeline, key=lambda x: x[1])]
    ev["observed"].update(status=result.status, authority_transition_ordering=names, blocked_while_lock_held=state["blocked_while_locked"],
                          counts=gov.counts(), final_selection_status=gov.state().status)
    return gov, result, names, state


def test_r01_a_revocation_racing_the_guard_cannot_commit_before_the_effect(tmp_path, ev):
    ev["expected"] = "transition blocks while guard+insert hold the lock; effect commits first; revocation lands after after_commit"
    revoking = v4.trust(2, revoked_selections=frozenset({("sel-test-1", 1)}))
    gov, result, names, state = _race(tmp_path, ev, "after_selection_guard", lambda other, _gov: other.dest.sync_selection("snapshot", trust=revoking))
    assert state["blocked_while_locked"] is True and result.status == "executed" and gov.counts()[0] == 1
    assert names.index("after_commit") < names.index("transition_committed")
    assert names.index("after_selection_guard") < names.index("after_effect_insert_before_commit") < names.index("after_commit")
    assert gov.state().status == "revoked"


def test_r02_a_withdrawal_racing_between_insert_and_commit_cannot_interleave(tmp_path, ev):
    ev["expected"] = "withdrawal waits for the lock held across insert->commit; ordering: after_commit before transition_committed"
    gov, result, names, state = _race(tmp_path, ev, "after_effect_insert_before_commit",
                                      lambda other, gv: other.withdraw(v4.withdraw_stmt(gv.stmt, 2)))
    assert state["blocked_while_locked"] is True and result.status == "executed" and gov.counts()[0] == 1
    assert names.index("after_commit") < names.index("transition_committed")
    assert gov.state().status == "withdrawn"


@pytest.mark.parametrize("how", ["withdraw", "revoke"])
def test_r03_r04_a_transition_committed_before_begin_refuses_with_no_effect(tmp_path, ev, how):
    ev["expected"] = "REFUSE (withdrawn/revoked) at the lock-time check; zero effects"
    gov = g.Gov(tmp_path)
    env, cid = gov.claim()

    class Pre(AtomicAuthorityEffectDestination):
        def _transaction_stage(self, stage):
            if stage == "before_begin":
                if how == "withdraw":
                    gov.e.withdraw(v4.withdraw_stmt(gov.stmt, 2))
                else:
                    gov.e.sync(2, revoked_selections=frozenset({("sel-test-1", 1)}))

    pre = Pre(gov.e.root, clock=lambda: gov.e.now)
    pre.configure_selection_authority(gov.e.anchor)
    result = run_executor(pre, env, cid)
    note_refusal(ev, result, gov)
    g.refused(result, "selection_withdrawn" if how == "withdraw" else "selection_revoked")
    assert gov.counts() == (0, 0, 0, 0)


# ============================================================================================ S: stale generation / binding
def _reactivate(gov):
    gov.e.withdraw(v4.withdraw_stmt(gov.stmt, 2))
    gov.e.activate(v4.select_stmt(v4.REC, epoch=3, supersedes=v4.sup(v4.withdraw_stmt(gov.stmt, 2))))


def test_s01_a_claim_tied_to_an_earlier_activation_generation_refuses_at_effect_time(tmp_path, ev):
    ev["expected"] = "REFUSE_STALE selection_epoch_stale, cause stale_policy_generation; zero effects"
    gov = g.Gov(tmp_path)
    env, cid = gov.claim()  # bound to the first activation
    _reactivate(gov)
    result = run_executor(gov.dest, env, cid)
    note_refusal(ev, result, gov)
    typed = g.refused(result, "selection_epoch_stale", "REFUSE_STALE")
    assert typed["cause"] == "stale_policy_generation" and gov.counts() == (0, 0, 0, 0)


def test_s02_a_foreign_activation_ref_refuses(tmp_path, ev):
    ev["expected"] = "REFUSE policy_identity_mismatch"
    gov = g.Gov(tmp_path)
    result = gov.run(g.binding_of(gov.state(), activation_ref="sha256:" + "a" * 64))[2]
    note_refusal(ev, result, gov)
    g.refused(result, "policy_identity_mismatch", "REFUSE")


def test_s03_a_substituted_record_identity_refuses(tmp_path, ev):
    ev["expected"] = "REFUSE record_identity_mismatch"
    gov = g.Gov(tmp_path)
    result = gov.run(g.binding_of(gov.state(), record_digest="sha256:" + "b" * 64))[2]
    note_refusal(ev, result, gov)
    g.refused(result, "record_identity_mismatch", "REFUSE")


def test_s04_a_substituted_selection_digest_refuses(tmp_path, ev):
    ev["expected"] = "REFUSE policy_identity_mismatch; zero effects"
    gov = g.Gov(tmp_path)
    result = gov.run(g.binding_of(gov.state(), selection_digest="sha256:" + "c" * 64))[2]
    note_refusal(ev, result, gov)
    g.refused(result, "policy_identity_mismatch", "REFUSE")
    assert gov.counts() == (0, 0, 0, 0)


# ============================================================================================ P: policy narrowing
def test_p01_a_permitted_action_inside_the_effective_policy_executes(tmp_path, ev):
    ev["expected"] = "act-list is in the Registry policy: executed"
    gov = g.Gov(tmp_path)
    result = gov.run(action_id="act-list")[2]
    ev["observed"].update(status=result.status, counts=gov.counts())
    assert result.status == "executed" and gov.counts()[0] == 1


def test_p02_an_action_outside_the_effective_policy_is_denied(tmp_path, ev):
    ev["expected"] = "act-extra is not in the Registry policy: denied (policy_denial); zero effects"
    gov = g.Gov(tmp_path)
    result = gov.run(action_id="act-extra")[2]
    ev["observed"].update(status=result.status, failure_class=result.control_plane_evidence.get("failure_class"), counts=gov.counts())
    assert result.status == "denied" and gov.counts() == (0, 0, 0, 0)


def test_p03_a_caller_policy_broader_than_the_registry_policy_cannot_widen_authority(tmp_path, ev):
    ev["expected"] = "REFUSE policy_identity_mismatch: the caller's wider policy is not the effective policy"
    gov = g.Gov(tmp_path)
    broader = g.effect_policy(allowed_actions=frozenset({"act-list", "act-extra"}))
    result = gov.run(policy=broader)[2]
    note_refusal(ev, result, gov)
    g.refused(result, "policy_identity_mismatch", "REFUSE")
    assert gov.counts() == (0, 0, 0, 0)


def test_p04_a_caller_policy_narrower_than_the_registry_policy_still_wins(tmp_path, ev):
    ev["expected"] = "the registry allows act-list but the caller does not: denied (the registry never expands the caller)"
    gov = g.Gov(tmp_path)
    narrower = g.effect_policy(allowed_actions=frozenset({"act-other"}))
    result = gov.run(policy=narrower, action_id="act-list")[2]
    ev["observed"].update(status=result.status, failure_class=result.control_plane_evidence.get("failure_class"), counts=gov.counts())
    assert result.status == "denied" and result.control_plane_evidence["failure_class"] == "policy_denial" and gov.counts() == (0, 0, 0, 0)


# ============================================================================================ L: legacy bypass
def test_l01_a_legacy_claim_cannot_bypass_a_required_governed_scope(tmp_path, ev):
    ev["expected"] = "REFUSE selection_missing; zero effects"
    gov = g.Gov(tmp_path)
    result = gov.run(binding=None)[2]
    note_refusal(ev, result, gov)
    g.refused(result, "selection_missing", "REFUSE")
    assert gov.counts() == (0, 0, 0, 0)


def test_l02_a_legacy_claim_cannot_bypass_an_active_optional_selection(tmp_path, ev):
    ev["expected"] = "REFUSE selection_missing"
    gov = g.Gov(tmp_path, participation="optional")
    result = gov.run(binding=None)[2]
    note_refusal(ev, result, gov)
    g.refused(result, "selection_missing", "REFUSE")


def test_l03_the_explicitly_permitted_never_activated_legacy_path_is_preserved(tmp_path, ev):
    ev["expected"] = "executed with applied=False, fallback caller_policy, reason never_activated"
    gov = g.Gov(tmp_path, activate=False)
    result = gov.run(binding=None)[2]
    guard = result.control_plane_evidence["authority_receipt"]["selection_guard"]
    ev["observed"].update(status=result.status, guard=guard)
    assert result.status == "executed" and guard["applied"] is False and guard["fallback"] == "caller_policy"
    assert guard["fallback_reason"] == "never_activated"


# ============================================================================================ G: trust, corruption, evidence atomicity
def test_g01_an_expired_current_trust_snapshot_is_a_hold(tmp_path, ev):
    ev["expected"] = "HOLD trust_snapshot_expired; zero effects"
    gov = g.Gov(tmp_path, snapshot_until="2026-10-25T18:00:00Z")
    env, cid = gov.claim()
    gov.e.now = gov.e.now.replace(hour=20)
    result = run_executor(gov.dest, env, cid)
    note_refusal(ev, result, gov)
    g.refused(result, "trust_snapshot_expired", "HOLD")
    assert gov.counts() == (0, 0, 0, 0)


def test_g02_a_corrupted_durable_authority_row_is_a_hold(tmp_path, ev):
    ev["expected"] = "HOLD store_unknown; zero effects"
    gov = g.Gov(tmp_path)
    env, cid = gov.claim()
    gov.e.sql("UPDATE selection_activation_v1 SET valid_until='2099-01-01T00:00:00Z'")
    result = run_executor(gov.dest, env, cid)
    note_refusal(ev, result, gov)
    g.refused(result, "store_unknown", "HOLD")
    assert gov.counts() == (0, 0, 0, 0)


def test_g03_a_governed_claim_with_no_configured_authority_store_is_a_hold(tmp_path, ev):
    ev["expected"] = "HOLD store_unknown (missing required verifier/store): no permissive fallback"
    env = g.envelope()
    dest = AtomicAuthorityEffectDestination(tmp_path / "plain", clock=lambda: v4.r.NOW)
    donor = g.Gov(tmp_path / "other")
    dest.provision_claim(g.make_claim(env, v4.r.NOW, binding=g.binding_of(donor.state()), claim_id="no-store-1"))
    result = run_executor(dest, env, "no-store-1")
    ev["observed"].update(status=result.status, selection_refusal=result.control_plane_evidence.get("selection_refusal"))
    g.refused(result, "store_unknown", "HOLD")


def test_g04_a_critical_evidence_write_failure_prevents_the_effect(tmp_path, ev):
    ev["expected"] = "guard-evidence write raises: status != executed; zero effects/receipts; claim stays issued"
    gov = g.Gov(tmp_path)

    class Failing(AtomicAuthorityEffectDestination):
        def _selection_receipt_evidence(self, evidence):
            raise OSError("evidence store unavailable")

    bad = Failing(gov.e.root, clock=lambda: gov.e.now)
    bad.configure_selection_authority(gov.e.anchor)
    env, cid = gov.claim()
    result = run_executor(bad, env, cid)
    with sqlite3.connect(gov.dest.path) as conn:
        state = conn.execute("SELECT state FROM execution_claims_v1 WHERE claim_id=?", (cid,)).fetchone()[0]
    ev["observed"].update(status=result.status, counts=gov.counts(), claim_state=state)
    assert result.status != "executed" and gov.counts() == (0, 0, 0, 0) and state == "issued"


def test_g05_a_failure_between_effect_insert_and_commit_leaves_no_effect(tmp_path, ev):
    ev["expected"] = "failure at after_effect_insert_before_commit rolls the whole transaction back: zero effects/receipts"
    gov = g.Gov(tmp_path)

    class Failing(AtomicAuthorityEffectDestination):
        def _transaction_stage(self, stage):
            if stage == "after_effect_insert_before_commit":
                raise OSError("disk full")

    bad = Failing(gov.e.root, clock=lambda: gov.e.now)
    bad.configure_selection_authority(gov.e.anchor)
    env, cid = gov.claim()
    result = run_executor(bad, env, cid)
    ev["observed"].update(status=result.status, counts=gov.counts())
    assert result.status != "executed" and gov.counts() == (0, 0, 0, 0)


def test_g06_a_restored_older_authority_database_is_a_hold(tmp_path, ev):
    ev["expected"] = "HOLD store_unknown: the anchor records a later head than the restored database"
    gov = g.Gov(tmp_path, activate=False)
    old = tmp_path / "old.sqlite3"
    with sqlite3.connect(gov.dest.path) as src, sqlite3.connect(old) as dst:
        src.backup(dst)
    gov.e.activate(gov.stmt)
    binding = g.binding_of(gov.state())
    with sqlite3.connect(old) as src, sqlite3.connect(gov.dest.path) as dst:
        src.backup(dst)
    restored = AtomicAuthorityEffectDestination(gov.e.root, clock=lambda: gov.e.now)
    restored.configure_selection_authority(gov.e.anchor)
    env = g.envelope()
    restored.provision_claim(g.make_claim(env, gov.now, binding=binding, claim_id="restored-1"))
    result = run_executor(restored, env, "restored-1")
    ev["observed"].update(status=result.status, selection_refusal=result.control_plane_evidence.get("selection_refusal"))
    g.refused(result, "store_unknown", "HOLD")
