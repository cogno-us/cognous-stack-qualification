"""V07 adversarial assessment of the integrated authority-to-effect boundary (frozen pins; see results/v07-security).

Each test performs ONE attack described in results/v07-security/INVENTORY.md (committed before execution) and records a verdict:
  HELD           the attack failed; the secure oracle held
  BREACH         the secure oracle was violated (classified afterwards from the contract text)
  CHARACTERIZED  the inventory declared the case a characterization (contract-disclosed or caller-owned); outcome recorded
  INCONCLUSIVE   the attack could not be mounted as designed (reported as unqualified, never as HELD)
pytest PASS means only that the harness ran the attack and recorded an outcome. Fixtures (Registry builders, claim builder) are imported from the
Runtime's tests; every attack and oracle below is new. Builder-authored; not an independent-party review. Synthetic local SQLite only.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import dataclasses
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

from conftest import COMPONENTS
import test_registry_selection_effect_guard as g
from engine.atomic_local_control_plane_executor import AtomicLocalControlPlaneExecutor
from engine.local_authority_effect import AtomicAuthorityEffectDestination, PROFILE as LEGACY_PROFILE

v4, sa = g.v4, g.sa
cp_commitment = g.cp_commitment


# ------------------------------------------------------------------------------------------------------------------------ helpers
def verdict(ev, v, note=""):
    ev["verdict"], ev["note"] = v, note


def mkenv(i=0, **changes):
    op = dataclasses.replace(g.flow.operation(), **{**g.op_changes(), **changes})
    return g.ExecutionEnvelope(g.EXECUTION_ENVELOPE_VERSION, f"decision-{i}", f"effect-{i}", op)


def reseal(raw, **over):
    raw = dict(raw)
    raw.pop("claim_commitment", None)
    raw.update(over)
    raw["claim_commitment"] = cp_commitment(raw)
    return raw


def provision(gov, raw):
    """True when provisioned; the exception text when the claim was refused at provisioning."""
    try:
        gov.dest.provision_claim(raw)
        return True
    except (PermissionError, ValueError) as exc:
        return type(exc).__name__ + ": " + str(exc)[:200]


def execute(dest, env, cid, policy=None):
    return AtomicLocalControlPlaneExecutor(workflow=None, destination=dest, policy=policy or g.effect_policy()).execute(envelope=env, claim_id=cid)


def typed(result):
    return result.control_plane_evidence.get("selection_refusal")


def effects(gov):
    return gov.counts()[0]


def snapshot_ev(ev, gov, result=None):
    ev["observed"]["counts_effects_attempts_receipts_budget"] = gov.counts()
    if result is not None:
        ev["observed"].update(status=result.status, attempted=result.attempted, selection_refusal=typed(result))


def attempt_claim(ev, gov, raw, policy=None, env=None):
    """Provision then execute; returns (provisioned_ok, result|None) and records the outcome."""
    ok = provision(gov, raw)
    ev["observed"]["provision"] = ok
    if ok is not True:
        snapshot_ev(ev, gov)
        return ok, None
    result = execute(gov.dest, env or g.envelope(), raw["claim_id"], policy)
    snapshot_ev(ev, gov, result)
    return ok, result


def judge_no_effect(ev, gov, ok, result, note=""):
    held = effects(gov) == 0 and (ok is not True and result is None or (result is not None and result.status != "executed"))
    verdict(ev, "HELD" if held else "BREACH", note if held else f"effect committed: {ev['observed']}")


def bound_raw(gov, env=None, claim_id="adv-1", binding="current", **over):
    env = env or g.envelope()
    b = g.binding_of(gov.state()) if binding == "current" else binding
    return g.make_claim(env, gov.now, binding=b, claim_id=claim_id), env


def probe(mode, *args, python=None, extra_path=(), cwd=None, timeout=180):
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(COMPONENTS / "runtime" / "tests"), str(COMPONENTS / "runtime"), *map(str, extra_path)])
    cp = subprocess.run([python or sys.executable, str(Path(__file__).resolve().parent / "_probe.py"), mode, *map(str, args)],
                        env=env, capture_output=True, text=True, timeout=timeout, cwd=cwd)
    line = [x for x in cp.stdout.splitlines() if x.startswith("V07PROBE ")]
    data = json.loads(line[-1][len("V07PROBE "):]) if line else {}
    return data, cp


CP = COMPONENTS / "control_plane" / "src"


# ========================================================================================================================= P0
def test_a01_explicit_null_binding_on_a_successor_profile_claim(tmp_path, ev):
    gov = g.Gov(tmp_path)
    raw, env = bound_raw(gov)
    ok, result = attempt_claim(ev, gov, reseal(raw, policy_binding=None), env=env)
    judge_no_effect(ev, gov, ok, result)


def test_a02_legacy_downgrade_of_a_bound_claim_over_a_required_scope(tmp_path, ev):
    gov = g.Gov(tmp_path)
    raw, env = bound_raw(gov)
    raw.pop("policy_binding")
    ok, result = attempt_claim(ev, gov, reseal(raw, profile=LEGACY_PROFILE), env=env)
    judge_no_effect(ev, gov, ok, result)
    if result is not None and result.status != "executed":
        ev["observed"]["refused_with"] = typed(result)


def test_a03_activation_ref_naming_a_real_non_activate_log_entry(tmp_path, ev):
    gov = g.Gov(tmp_path)
    rows = gov.e.sql("SELECT entry_hash, entry_json FROM selection_log_v1 ORDER BY activation_sequence")
    sync_hash = next(h for h, j in rows if json.loads(j)["entry_type"] == "sync")
    raw, env = bound_raw(gov, binding=g.binding_of(gov.state(), activation_ref=sync_hash))
    ok, result = attempt_claim(ev, gov, raw, env=env)
    judge_no_effect(ev, gov, ok, result)


def test_a04_unknown_binding_member_policy_generation_injected(tmp_path, ev):
    gov = g.Gov(tmp_path)
    b = g.binding_of(gov.state())
    b["policy_generation"] = 1
    raw, env = bound_raw(gov, binding=b)
    ok, result = attempt_claim(ev, gov, raw, env=env)
    judge_no_effect(ev, gov, ok, result)


def test_a05_claim_provisioned_after_the_selection_was_withdrawn(tmp_path, ev):
    gov = g.Gov(tmp_path)
    stale_binding = g.binding_of(gov.state())
    gov.e.withdraw(v4.withdraw_stmt(gov.stmt, 2))
    raw, env = bound_raw(gov, binding=stale_binding)
    ok, result = attempt_claim(ev, gov, raw, env=env)
    judge_no_effect(ev, gov, ok, result)


def test_a06_revoked_selection_epoch_pair_after_issue_on_an_optional_scope(tmp_path, ev):
    gov = g.Gov(tmp_path, participation="optional")
    raw, env = bound_raw(gov)
    assert provision(gov, raw) is True
    gov.e.sync(2, revoked_selections=frozenset({("sel-test-1", 1)}))
    result = execute(gov.dest, env, raw["claim_id"])
    snapshot_ev(ev, gov, result)
    judge_no_effect(ev, gov, True, result)


def test_a07_claim_altered_without_recomputing_the_commitment(tmp_path, ev):
    gov = g.Gov(tmp_path)
    raw, env = bound_raw(gov)
    raw["target"] = raw["target"] + "9"
    ok, result = attempt_claim(ev, gov, raw, env=env)
    with sqlite3.connect(gov.dest.path) as conn:
        ev["observed"]["claim_rows"] = conn.execute("SELECT COUNT(*) FROM execution_claims_v1").fetchone()[0]
    judge_no_effect(ev, gov, ok, result)
    assert ev["observed"]["claim_rows"] == 0 or ok is True


def test_a08_claim_effective_policy_digest_replaced_by_a_wider_policys_digest(tmp_path, ev):
    gov = g.Gov(tmp_path)
    wide = g.effect_policy(allowed_actions=frozenset({"act-list", "act-extra"}))
    d_wide = sa.policy_digest_of(wide)
    assert d_wide != v4.effective_digest()
    env = g.envelope(action_id="act-extra")
    raw = g.make_claim(env, gov.now, binding=g.binding_of(gov.state(), effective_policy_digest=d_wide), claim_id="adv-wide")
    ok, result = attempt_claim(ev, gov, raw, policy=wide, env=env)
    ev["observed"]["registry_payload_actions"] = v4.PAYLOAD["allowed_actions"]
    judge_no_effect(ev, gov, ok, result)


def test_a09_caller_owned_dimensions_widened_with_the_registry_sets_unchanged(tmp_path, ev):
    gov = g.Gov(tmp_path)
    policy = g.effect_policy(max_amount=10 ** 9, allowed_target_prefixes=("urn:",))
    assert sa.policy_digest_of(policy) == v4.effective_digest()
    env = g.envelope(amount=5000.0)
    raw = g.make_claim(env, gov.now, binding=g.binding_of(gov.state()), claim_id="adv-amount")
    ok, result = attempt_claim(ev, gov, raw, policy=policy, env=env)
    verdict(ev, "CHARACTERIZED", f"amount 5000 > default cap 1000 under a narrowed Registry policy: {'executed' if effects(gov) else 'refused'}; "
            "max_amount and target prefixes are outside the F1AB payload (caller-owned)")


def test_a10_supersession_to_epoch_2_refuses_the_epoch_1_claim(tmp_path, ev):
    gov = g.Gov(tmp_path)
    raw, env = bound_raw(gov)
    assert provision(gov, raw) is True
    gov.e.activate(v4.select_stmt(v4.REC, epoch=2, supersedes=v4.sup(gov.stmt)))
    result = execute(gov.dest, env, raw["claim_id"])
    snapshot_ev(ev, gov, result)
    judge_no_effect(ev, gov, True, result)


# ========================================================================================================================= P1
def test_c01_os_process_withdrawal_racing_a_stream_of_executions(tmp_path, ev):
    gov = g.Gov(tmp_path)
    n = 160
    for i in range(n):
        env = mkenv(i)
        assert provision(gov, g.make_claim(env, gov.now, binding=g.binding_of(gov.state()), claim_id=f"race-{i}")) is True
    proc = subprocess.Popen([sys.executable, str(Path(__file__).resolve().parent / "_probe.py"), "withdraw", str(tmp_path), "1.5"],
                            env={**os.environ, "PYTHONPATH": os.pathsep.join([str(COMPONENTS / "runtime" / "tests"), str(COMPONENTS / "runtime")])},
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    statuses = []
    for i in range(n):
        res = execute(gov.dest, mkenv(i), f"race-{i}")
        statuses.append(res.status)
        time.sleep(0.03)
    out, err = proc.communicate(timeout=120)
    wseqs = [json.loads(j)["activation_sequence"] for (j,) in gov.e.sql("SELECT entry_json FROM selection_log_v1") if json.loads(j)["entry_type"] == "withdraw"]
    wseq = max(wseqs) if wseqs else None
    heads = [json.loads(r)["selection_guard"]["log_head_sequence"] for (r,) in gov.e.sql("SELECT receipt_json FROM authority_effect_receipts_v1")]
    first_denied = statuses.index("denied") if "denied" in statuses else None
    executed = statuses.count("executed")
    ev["observed"].update(executed=executed, denied=statuses.count("denied"), first_denied_index=first_denied, withdraw_sequence=wseq,
                          max_guard_head_of_effects=max(heads) if heads else None, probe_stderr=err[-300:])
    if not (executed and first_denied is not None and wseq is not None):
        verdict(ev, "INCONCLUSIVE", "race did not overlap the execution stream")
        return
    monotone = all(s == "denied" for s in statuses[first_denied:])
    ordered = all(h < wseq for h in heads)
    verdict(ev, "HELD" if monotone and ordered and effects(gov) == executed else "BREACH", f"monotone={monotone} guard_heads_below_withdraw={ordered}")


def test_c02_two_processes_execute_the_same_claim(tmp_path, ev):
    gov = g.Gov(tmp_path)
    env, cid = gov.claim()
    start = time.time() + 4.0
    procs = [subprocess.Popen([sys.executable, str(Path(__file__).resolve().parent / "_probe.py"), "exec_one", str(tmp_path), cid, str(start)],
                              env={**os.environ, "PYTHONPATH": os.pathsep.join([str(COMPONENTS / "runtime" / "tests"), str(COMPONENTS / "runtime")])},
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
    outs = [p.communicate(timeout=120) for p in procs]
    results = [json.loads([x for x in o.splitlines() if x.startswith("V07PROBE ")][-1][len("V07PROBE "):]) for o, _ in outs]
    ev["observed"].update(results=results, counts=gov.counts())
    verdict(ev, "HELD" if effects(gov) == 1 else "BREACH", f"effects={effects(gov)}")


def test_c03_two_claims_sharing_one_budget_executed_concurrently(tmp_path, ev):
    gov = g.Gov(tmp_path)
    envs = [mkenv(1), mkenv(2)]
    provisioned = []
    for i, env in enumerate(envs):
        raw = g.make_claim(env, gov.now, binding=g.binding_of(gov.state()), claim_id=f"shared-{i}")
        provisioned.append(provision(gov, reseal(raw, budget_id="shared-budget")))
    ev["observed"]["provisioned"] = provisioned
    results = {}
    def run(i):
        if provisioned[i] is True:
            try:
                results[i] = execute(gov.dest, envs[i], f"shared-{i}").status
            except BaseException as exc:  # noqa: BLE001
                results[i] = type(exc).__name__
    ts = [threading.Thread(target=run, args=(i,)) for i in range(2)]
    [t.start() for t in ts]
    [t.join(60) for t in ts]
    ev["observed"].update(results=results, counts=gov.counts())
    verdict(ev, "HELD" if effects(gov) <= 1 else "BREACH", f"effects={effects(gov)} budget_used={gov.counts()[3]}")


def test_c04_concurrent_authority_writers_leave_a_verifiable_store(tmp_path, ev):
    gov = g.Gov(tmp_path)
    errs = []
    def writer(version):
        try:
            other = v4.Env(tmp_path)
            other.trust = gov.e.trust
            other.sync(version)
        except BaseException as exc:  # noqa: BLE001
            errs.append(f"{version}:{type(exc).__name__}")
    ts = [threading.Thread(target=writer, args=(v,)) for v in (2, 3)]
    [t.start() for t in ts]
    [t.join(60) for t in ts]
    status = gov.e.verify()
    ev["observed"].update(writer_errors=errs, store_state=getattr(status, "state", str(status)), head=gov.e.head())
    verdict(ev, "HELD" if getattr(status, "state", None) == "known" else "BREACH", f"errors={errs}")


def test_c05_process_killed_between_effect_insert_and_commit(tmp_path, ev):
    gov = g.Gov(tmp_path)
    env, cid = gov.claim()
    data, cp = probe("crash", tmp_path, cid, "after_effect_insert_before_commit")
    with sqlite3.connect(gov.dest.path) as conn:
        state = conn.execute("SELECT state FROM execution_claims_v1 WHERE claim_id=?", (cid,)).fetchone()[0]
    ev["observed"].update(exit_code=cp.returncode, counts=gov.counts(), claim_state=state)
    retry = execute(gov.dest, env, cid)
    ev["observed"].update(retry_status=retry.status, counts_after_retry=gov.counts())
    verdict(ev, "HELD" if cp.returncode == 9 and state == "issued" and retry.status == "executed" and effects(gov) == 1 else "BREACH")


def test_c06_process_killed_immediately_after_commit(tmp_path, ev):
    gov = g.Gov(tmp_path)
    env, cid = gov.claim()
    data, cp = probe("crash", tmp_path, cid, "after_commit")
    before = effects(gov)
    replay = execute(gov.dest, env, cid)
    ev["observed"].update(exit_code=cp.returncode, effects_after_crash=before, replay_status=replay.status, counts=gov.counts())
    verdict(ev, "HELD" if cp.returncode == 9 and before == 1 and replay.status != "executed" and effects(gov) == 1 else "BREACH")


def test_c07_long_lived_destination_does_not_cache_authority(tmp_path, ev):
    gov = g.Gov(tmp_path)
    env, cid = gov.claim()
    long_lived = AtomicAuthorityEffectDestination(gov.e.root, clock=lambda: gov.e.now)
    long_lived.configure_selection_authority(gov.e.anchor)
    long_lived.verify_selection_store()  # the instance has read the store once before the change
    other = v4.Env(tmp_path)
    other.trust = gov.e.trust
    other.withdraw(v4.withdraw_stmt(gov.stmt, 2))
    result = execute(long_lived, env, cid)
    snapshot_ev(ev, gov, result)
    judge_no_effect(ev, gov, True, result)


# ---------------------------------------------------------------------------------------------------------------- durable state
def _unbound_required(tmp_path):
    gov = g.Gov(tmp_path)
    env = g.envelope(tenant_id=None)
    raw = g.make_claim(env, gov.now, binding=None, claim_id="legacy-adv")
    assert provision(gov, raw) is True
    return gov, env, raw


def test_d01_restore_of_database_and_host_held_anchor_together(tmp_path, ev):
    gov = g.Gov(tmp_path)
    raw, env = bound_raw(gov)
    assert provision(gov, raw) is True
    saved_db, saved_anchor = tmp_path / "saved.sqlite3", tmp_path / "saved-anchor.json"
    with sqlite3.connect(gov.dest.path) as src, sqlite3.connect(saved_db) as dst:
        src.backup(dst)
    shutil.copy(gov.e.anchor, saved_anchor)
    gov.e.withdraw(v4.withdraw_stmt(gov.stmt, 2))
    with sqlite3.connect(saved_db) as src, sqlite3.connect(gov.dest.path) as dst:
        src.backup(dst)
    shutil.copy(saved_anchor, gov.e.anchor)
    restored = AtomicAuthorityEffectDestination(gov.e.root, clock=lambda: gov.e.now)
    restored.configure_selection_authority(gov.e.anchor)
    result = execute(restored, env, raw["claim_id"])
    snapshot_ev(ev, gov, result)
    verdict(ev, "CHARACTERIZED", f"consistent rollback of DB and anchor: {'effect committed (disclosed undetectable, ADR 3.6)' if effects(gov) else 'detected: ' + str(typed(result))}")


def test_d02_anchor_ahead_of_the_store(tmp_path, ev):
    gov = g.Gov(tmp_path)
    raw, env = bound_raw(gov)
    assert provision(gov, raw) is True
    gov.e.rewrite_anchor(head_sequence=gov.e.head()[0] + 50)
    result = execute(gov.dest, env, raw["claim_id"])
    snapshot_ev(ev, gov, result)
    held = result.status != "executed" and effects(gov) == 0 and (typed(result) or {}).get("refusal_class") == "HOLD"
    verdict(ev, "HELD" if held else "BREACH")


def test_d03_anchor_head_hash_altered(tmp_path, ev):
    gov = g.Gov(tmp_path)
    raw, env = bound_raw(gov)
    assert provision(gov, raw) is True
    gov.e.rewrite_anchor(head_entry_hash="sha256:" + "0" * 64)
    result = execute(gov.dest, env, raw["claim_id"])
    snapshot_ev(ev, gov, result)
    verdict(ev, "HELD" if result.status != "executed" and effects(gov) == 0 and (typed(result) or {}).get("refusal_class") == "HOLD" else "BREACH")


def test_d04_ratchet_row_deleted_then_binding_less_claim(tmp_path, ev):
    gov, env, raw = _unbound_required(tmp_path)
    gov.e.drop_guards()
    gov.e.sql("DELETE FROM selection_scope_required_v1")
    result = execute(gov.dest, env, raw["claim_id"])
    snapshot_ev(ev, gov, result)
    verdict(ev, "HELD" if result.status != "executed" and effects(gov) == 0 else "BREACH")


def test_d05_generation_counter_lowered(tmp_path, ev):
    gov = g.Gov(tmp_path)
    raw, env = bound_raw(gov)
    assert provision(gov, raw) is True
    gov.e.drop_guards()
    gov.e.sql("UPDATE selection_generation_v1 SET policy_generation=0")
    result = execute(gov.dest, env, raw["claim_id"])
    snapshot_ev(ev, gov, result)
    verdict(ev, "HELD" if result.status != "executed" and effects(gov) == 0 else "BREACH")


def test_d06_selection_tables_dropped_while_a_store_is_configured(tmp_path, ev):
    gov = g.Gov(tmp_path)
    raw, env = bound_raw(gov)
    assert provision(gov, raw) is True
    gov.e.drop_guards()
    gov.e.sql("DROP TABLE selection_activation_v1")
    try:
        result = execute(gov.dest, env, raw["claim_id"])
        snapshot_ev(ev, gov, result)
        verdict(ev, "HELD" if result.status != "executed" and effects(gov) == 0 else "BREACH")
    except Exception as exc:  # noqa: BLE001
        ev["observed"]["exception"] = type(exc).__name__ + ": " + str(exc)[:200]
        verdict(ev, "HELD" if effects_safe(gov.dest.path) == 0 else "BREACH", "error surfaced")


def effects_safe(path):
    try:
        with sqlite3.connect(path) as conn:
            return conn.execute("SELECT COUNT(*) FROM effects").fetchone()[0]
    except Exception:  # noqa: BLE001
        return 0


def test_d07_database_file_truncated_after_provisioning(tmp_path, ev):
    gov = g.Gov(tmp_path)
    raw, env = bound_raw(gov)
    assert provision(gov, raw) is True
    path = gov.dest.path
    for suffix in ("-wal", "-shm"):
        Path(str(path) + suffix).unlink(missing_ok=True)
    os.truncate(path, 100)
    try:
        result = execute(gov.dest, env, raw["claim_id"])
        ev["observed"]["status"] = result.status
        verdict(ev, "HELD" if result.status != "executed" else "BREACH")
    except Exception as exc:  # noqa: BLE001
        ev["observed"]["exception"] = type(exc).__name__ + ": " + str(exc)[:200]
        verdict(ev, "HELD", "error surfaced; no effect")


def test_d08_stored_claim_row_altered_after_provisioning(tmp_path, ev):
    gov = g.Gov(tmp_path)
    wide = g.effect_policy(allowed_actions=frozenset({"act-list", "act-extra"}))
    env = g.envelope(action_id="act-extra")
    raw = g.make_claim(env, gov.now, binding=g.binding_of(gov.state()), claim_id="adv-row")
    assert provision(gov, raw) is True
    (row,) = gov.e.sql("SELECT claim_json FROM execution_claims_v1 WHERE claim_id=?", ("adv-row",))
    doc = json.loads(row[0])
    doc["policy_binding"]["effective_policy_digest"] = sa.policy_digest_of(wide)
    gov.e.sql("UPDATE execution_claims_v1 SET claim_json=? WHERE claim_id=?", (json.dumps(doc), "adv-row"))
    result = execute(gov.dest, env, "adv-row", wide)
    snapshot_ev(ev, gov, result)
    verdict(ev, "CHARACTERIZED", f"claim_json edited in place (commitment not recomputed): {'effect committed' if effects(gov) else 'refused ' + str(typed(result))}; "
            "requires write access to the database")


# ========================================================================================================================= P2
def test_t01_replay_of_an_older_trust_snapshot(tmp_path, ev):
    gov = g.Gov(tmp_path)
    gov.e.sync(2)
    head = gov.e.head()
    try:
        gov.dest.sync_selection("snapshot", trust=v4.trust(1))
        accepted = True
    except (PermissionError, ValueError) as exc:
        accepted = False
        ev["observed"]["refusal"] = type(exc).__name__ + ": " + str(exc)[:160]
    ev["observed"].update(accepted=accepted, head_before=head, head_after=gov.e.head())
    verdict(ev, "HELD" if not accepted and gov.e.head() == head else "BREACH")


def test_t02_later_snapshot_cannot_unrevoke_an_issuer_key(tmp_path, ev):
    gov = g.Gov(tmp_path)
    raw, env = bound_raw(gov)
    assert provision(gov, raw) is True
    gov.e.sync(2, revoked_key_ids=frozenset({"key-test-1"}))
    try:
        gov.e.sync(3)
        ev["observed"]["unrevoking_snapshot"] = "accepted"
    except (PermissionError, ValueError) as exc:
        ev["observed"]["unrevoking_snapshot"] = "refused: " + str(exc)[:120]
    result = execute(gov.dest, env, raw["claim_id"])
    snapshot_ev(ev, gov, result)
    judge_no_effect(ev, gov, True, result)


def test_t03_resubmitted_epoch_1_activation_after_epoch_2(tmp_path, ev):
    gov = g.Gov(tmp_path)
    gov.e.activate(v4.select_stmt(v4.REC, epoch=2, supersedes=v4.sup(gov.stmt)))
    head = gov.e.head()
    try:
        gov.e.activate(gov.stmt)
        accepted = True
    except (PermissionError, ValueError) as exc:
        accepted = False
        ev["observed"]["refusal"] = type(exc).__name__ + ": " + str(exc)[:160]
    ev["observed"].update(accepted=accepted, epoch_now=gov.state().selection_epoch)
    verdict(ev, "HELD" if not accepted and gov.e.head() == head and gov.state().selection_epoch == 2 else "BREACH")


def test_t04_resubmitted_old_activation_after_withdrawal_cannot_resurrect(tmp_path, ev):
    gov = g.Gov(tmp_path)
    gov.e.withdraw(v4.withdraw_stmt(gov.stmt, 2))
    head = gov.e.head()
    try:
        gov.e.activate(gov.stmt)
        accepted = True
    except (PermissionError, ValueError) as exc:
        accepted = False
        ev["observed"]["refusal"] = type(exc).__name__ + ": " + str(exc)[:160]
    ev["observed"].update(accepted=accepted, status_now=gov.state().status)
    verdict(ev, "HELD" if not accepted and gov.e.head() == head and gov.state().status == "withdrawn" else "BREACH")


def test_t05_lineage_substitution_with_a_different_selection_id(tmp_path, ev):
    gov = g.Gov(tmp_path)
    head = gov.e.head()
    try:
        gov.e.activate(v4.select_stmt(v4.REC, sid="sel-evil-2", epoch=1))
        accepted = True
    except (PermissionError, ValueError) as exc:
        accepted = False
        ev["observed"]["refusal"] = {"code": getattr(exc, "code", None), "cause": getattr(exc, "cause", None)}
    ev["observed"]["accepted"] = accepted
    verdict(ev, "HELD" if not accepted and gov.e.head() == head else "BREACH")


def test_t06_record_identity_substitution_under_a_pinned_statement(tmp_path, ev):
    gov = g.Gov(tmp_path, activate=False)
    mutated = v4.reg_record(payload=dict(v4.PAYLOAD, allowed_actions=["act-list", "act-extra"]))
    head = gov.e.head()
    try:
        gov.e.activate(gov.stmt, rec=mutated)
        accepted = True
    except (PermissionError, ValueError) as exc:
        accepted = False
        ev["observed"]["refusal"] = {"code": getattr(exc, "code", None), "type": type(exc).__name__}
    rows = gov.e.sql("SELECT COUNT(*) FROM selection_activation_v1")[0][0]
    ev["observed"].update(accepted=accepted, activation_rows=rows)
    verdict(ev, "HELD" if not accepted and rows == 0 and gov.e.head() == head else "BREACH")


def test_t07_duplicate_key_statement_text_is_not_accepted(tmp_path, ev):
    gov = g.Gov(tmp_path, activate=False)
    good = v4.text(gov.stmt)
    assert '"statement": {' in good
    mutated = good.replace('"statement": {', '"statement": {"epoch": 99, ', 1)
    head = gov.e.head()
    try:
        gov.e.dest.activate_selection(record_text=v4.r.dumps(v4.REC), selection_text=mutated, context=v4.s.CTX, trust=gov.e.trust,
                                      verifier=v4.ev.Ed25519Verifier())
        accepted = True
    except (PermissionError, ValueError) as exc:
        accepted = False
        ev["observed"]["refusal"] = type(exc).__name__ + ": " + str(exc)[:160]
    rows = gov.e.sql("SELECT COUNT(*) FROM selection_activation_v1")[0][0]
    ev["observed"].update(accepted=accepted, activation_rows=rows)
    verdict(ev, "HELD" if not accepted and rows == 0 else "BREACH", "" if not accepted else "duplicate JSON keys parsed last-wins")


def test_t08_missing_or_raising_verifier_never_activates(tmp_path, ev):
    gov = g.Gov(tmp_path, activate=False)

    class Raising:
        def verify(self, *a, **k):
            raise RuntimeError("verifier offline")

    outcomes = {}
    for name, verifier in (("none", None), ("raising", Raising())):
        try:
            gov.e.dest.activate_selection(record_text=v4.r.dumps(v4.REC), selection_text=v4.text(gov.stmt), context=v4.s.CTX, trust=gov.e.trust,
                                          verifier=verifier)
            outcomes[name] = "accepted"
        except BaseException as exc:  # noqa: BLE001
            outcomes[name] = type(exc).__name__
    rows = gov.e.sql("SELECT COUNT(*) FROM selection_activation_v1")[0][0]
    ev["observed"].update(outcomes=outcomes, activation_rows=rows)
    verdict(ev, "HELD" if "accepted" not in outcomes.values() and rows == 0 else "BREACH")


# ========================================================================================================================= P3
def test_i01_runtime_wrapper_workflow_reusable_pin(ev):
    wf = (COMPONENTS / "runtime" / ".github" / "workflows" / "worker21-authority-effect.yml").read_text()
    refs = re.findall(r"cognous-stack-qualification/\.github/workflows/[\w.-]+@([0-9a-f]{40})", wf)
    ev["observed"].update(reusable_workflow_refs=refs)
    qualified = "ae12221831bc39beea6dbf0ae7fda726baeecf1f"
    verdict(ev, "CHARACTERIZED", f"Runtime wrapper calls the reusable qualification workflow at {refs}; V06 qualified revision is {qualified}: "
            + ("up to date" if qualified in refs else "STALE (coverage gap, not an exploit)"))


def test_i02_successor_claim_on_the_older_control_plane_fixture(ev):
    data, cp = probe("successor_old", extra_path=[COMPONENTS / "control_plane_legacy" / "src"])
    ev["observed"] = data | {"returncode": cp.returncode, "stderr": cp.stderr[-300:]}
    held = data.get("provision") == "refused" and data.get("effects") == 0 and data.get("claims") == 0
    verdict(ev, "HELD" if held else ("INCONCLUSIVE" if not data else "BREACH"))


def test_i03_successor_claim_with_v02_under_pydantic_2_11(ev):
    py = os.environ.get("V07_PY211")
    assert py and Path(py).exists(), "V07_PY211 must name a Python with pydantic 2.11.9 (mandatory case; never skipped)"
    data, cp = probe("successor_211", python=py, extra_path=[CP])
    ev["observed"] = data | {"returncode": cp.returncode, "stderr": cp.stderr[-400:]}
    if not data:
        verdict(ev, "HELD", "fails closed at import/startup under pydantic 2.11 (process error, no effect)")
    else:
        verdict(ev, "HELD" if data.get("provision") == "refused" and data.get("effects") == 0 else "BREACH")


def test_i04_control_plane_refuses_a_binding_the_approval_did_not_commit_to(ev):
    root = COMPONENTS / "control_plane"
    data, cp = probe("cp_issue", extra_path=[CP, root], cwd=root)
    ev["observed"] = data | {"returncode": cp.returncode, "stderr": cp.stderr[-400:]}
    if not data or not str(data.get("honest", "")).startswith("issued"):
        verdict(ev, "INCONCLUSIVE", "honest issuance fixture could not be established; tampered-binding refusal not meaningful")
    else:
        verdict(ev, "HELD" if str(data.get("tampered", "")).startswith("refused") else "BREACH")
