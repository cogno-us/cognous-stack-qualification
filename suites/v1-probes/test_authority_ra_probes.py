"""ADD-AUTH-RA probes: Runtime Authority addendum (15 Oct 2026) K1-K5 behaviours that the Control Plane's own
tests/test_runtime_authority.py does not exercise (see process/v1-validation/v1-2026-10-16-a/acceptance-map-03.json).

Run against the checkout named by PROBE_CONTROL_PLANE_DIR (cogno-us/cognous-control-plane at the frozen pin; Linux only, the record
store requires flock). The probes reuse the pin's own synthetic fixtures (tests.test_runtime_authority.setup_flow) and drive the real
BoundedAuthorizationWorkflow, BoundedRecordStore and RuntimeAuthorityProfile. A failing probe is a finding about the pinned component.
Names contain 'probe_addauthra_'. K6 (PRP paired evaluation) is a separate track and is not probed here.
"""
import json
import threading
from collections import Counter
from datetime import timedelta

import pytest

from conftest import pin_dir


@pytest.fixture(autouse=True)
def _pin(monkeypatch):
    pin_dir("PROBE_CONTROL_PLANE_DIR")
    import agent_control_plane.bounded as bounded
    from tests.test_runtime_authority import NOW
    monkeypatch.setattr(bounded, "_now", lambda: NOW)


def fx():
    import tests.test_runtime_authority as t
    return t


def make(tmp_path, **kw):
    t = fx()
    return t.setup_flow(tmp_path, **kw)


def _reasons_registry():
    """The reason registry of the checkout under test: 0.2 (the 158-code superset a current control plane emits). It is read directly;
    there is no fallback to 0.1 (a checkout without the 0.2 file fails this probe)."""
    import os
    from pathlib import Path
    path = Path(os.environ["PROBE_CONTROL_PLANE_DIR"]) / "schemas" / "runtime_authority_reasons_0_2.json"
    return json.loads(path.read_text(encoding="utf-8"))


def events(f):
    return [e.model_dump(mode="json") for e in f.records.load().check_events]


READ_METHODS = ("authority_context", "grant_status", "identity_status", "issuer_mandate", "approval_status",
                "policy_status", "conflict_status", "evidence_status", "role_mapping")


# ---------------------------------------------------------------- K1: durable check journal
def test_probe_addauthra_opened_event_is_durable_before_the_first_resolver_read(tmp_path):
    p, r, f, c = make(tmp_path)
    seen = []
    for name in READ_METHODS:
        original = getattr(r, name)

        def wrapped(*a, _o=original, _n=name, **k):
            rows = events(f)
            seen.append((_n, [x["phase"] for x in rows], [x["check_id"] for x in rows]))
            return _o(*a, **k)
        setattr(r, name, wrapped)
    f.decide(p, now=fx().NOW)
    assert seen, "resolver was never read"
    first = seen[0]
    assert first[1][0] == "opened" and "completed" not in first[1], f"first resolver read ({first[0]}) saw journal {first[1]}"
    assert len(set(first[2])) == 1
    # no resolver read ever precedes the durable opening of its own check
    assert all(s[1][0] == "opened" for s in seen)


def test_probe_addauthra_opened_event_binds_check_stage_proposal_class_and_service_time(tmp_path):
    p, r, f, c = make(tmp_path)
    f.decide(p, now=fx().NOW)
    opened = events(f)[0]
    assert opened["phase"] == "opened" and opened["check_id"] and opened["stage"] == "decision"
    assert opened["proposal_commitment"].startswith("sha256:")
    assert opened["recorded_at"] and opened["owner"]
    assert opened["action_class"]["class_id"] == "synthetic-irreversible" and opened["action_class"]["irreversible"] is True


def test_probe_addauthra_effect_stage_opened_event_binds_the_stable_effect_id(tmp_path):
    p, r, f, c = make(tmp_path)
    d = f.decide(p, now=fx().NOW)
    f.execute(p, d, adapter_id=p.adapter_id, now=fx().NOW)
    stages = {e["stage"]: e for e in events(f) if e["phase"] == "opened"}
    assert stages["decision"]["effect_id"] is None  # not yet allocated at the first decision check
    assert stages["effect"]["effect_id"] == d.effect_id and stages["effect"]["decision_id"] == d.decision_id


def test_probe_addauthra_opened_event_binds_the_component_version(tmp_path):
    """Addendum K1: CheckOpened binds 'component version'. Strict reading: the opening record names the control-plane component
    version (not merely the reason-vocabulary version) so a record can be tied to the software that wrote it."""
    p, r, f, c = make(tmp_path)
    f.decide(p, now=fx().NOW)
    opened = events(f)[0]
    keys = {k for k in opened if "version" in k and k != "reason_vocabulary_version"}
    keys |= {k for k in opened if "component" in k}
    assert keys, f"CheckOpened carries no component/software version field; keys={sorted(opened)}"


def test_probe_addauthra_resolution_result_records_observation_time_and_age(tmp_path):
    """Addendum K1: each completed read records 'observation time and age'. Strict reading: an explicit age value is stored."""
    p, r, f, c = make(tmp_path)
    d = f.decide(p, now=fx().NOW)
    grant = next(i for i in d.resolution_inputs if i.input_type == "grant")
    assert grant.observed.get("observed_at") and grant.observed.get("revision") and grant.record_commitment and grant.expected
    row = next(e for e in events(f) if e["phase"] == "input" and e["input"]["input_type"] == "grant")["input"]
    stored = json.dumps([row, f.records.load().resolution_checks[0].model_dump(mode="json")["inputs"]])
    assert '"age' in stored or "_age" in stored, "no explicit age is stored with the resolution result (only observed_at and evaluated_at)"


def test_probe_addauthra_closure_is_append_only_and_never_rewrites_the_opening_record(tmp_path):
    p, r, f, c = make(tmp_path)
    snapshots = []
    original = r.grant_status

    def spy(ref):
        snapshots.append(events(f)[0])
        return original(ref)
    r.grant_status = spy
    f.decide(p, now=fx().NOW)
    rows = events(f)
    assert snapshots and rows[0] == snapshots[0], "the opening row changed after it was first persisted"
    check = rows[0]["check_id"]
    mine = [e["phase"] for e in rows if e["check_id"] == check]
    assert mine[0] == "opened" and mine[-1] == "completed" and mine.count("opened") == 1 and mine.count("completed") == 1
    assert len(rows) > len(snapshots) and all(e["check_id"] == check for e in rows)
    from agent_control_plane.bounded import CheckEvent
    again = CheckEvent.model_validate(rows[-1] | {"phase": "interrupted"})
    with pytest.raises(ValueError):
        f.records.append_check_event(again)  # a closed check cannot be closed a second time


@pytest.mark.parametrize("mutation,reason,absent", [
    ("suspended", "grant_suspended", "grant_revoked"),
    ("unknown", "grant_unknown", "grant_revoked"),
    ("stale", "grant_status_stale_or_future", "grant_revoked"),
    ("exception", "status_unreadable", "grant_revoked"),
])
def test_probe_addauthra_resolver_failures_are_typed_and_never_become_a_verified_revocation(tmp_path, mutation, reason, absent):
    t = fx()
    p, r, f, c = make(tmp_path)
    status = next(iter(r.statuses.values()))
    if mutation in ("suspended", "unknown"):
        status.status = mutation
    elif mutation == "stale":
        status.observed_at = (t.NOW - timedelta(hours=1)).isoformat()
    else:
        def broken(ref):
            raise TimeoutError("synthetic outage")
        r.grant_status = broken
    d = f.decide(p, now=t.NOW)
    assert d.result == "hold" and reason in d.reasons and absent not in d.reasons, d.reasons
    assert not any(i.observed.get("status") == "revoked" for i in d.resolution_inputs)
    assert f.destination.snapshot()["effects"] == {}


def test_probe_addauthra_expired_grant_is_a_distinct_typed_reason(tmp_path):
    t = fx()
    p, r, f, c = make(tmp_path)
    d = f.decide(p, now=t.NOW + timedelta(days=3650))
    assert d.result == "hold" and "grant_outside_validity" in d.reasons and "grant_revoked" not in d.reasons


def test_probe_addauthra_refusal_persistence_failure_blocks_dispatch_and_claims_no_durable_refusal(tmp_path):
    t = fx()
    p, r, f, c = make(tmp_path)
    d = f.decide(p, now=t.NOW)
    next(iter(r.statuses.values())).status = "revoked"

    def fail(row):
        raise OSError("synthetic refusal-write failure")
    f.records.append_refusal = fail
    with pytest.raises(OSError):
        f.execute(p, d, adapter_id=p.adapter_id, now=t.NOW)
    rec = f.records.load()
    assert f.destination.snapshot()["effects"] == {} and not rec.attempts and not rec.refusals


def test_probe_addauthra_concurrent_refused_executions_each_block_and_none_dispatches(tmp_path):
    t = fx()
    p, r, f, c = make(tmp_path)
    d = f.decide(p, now=t.NOW)
    next(iter(r.statuses.values())).status = "revoked"
    outcome = []

    def run():
        try:
            f.execute(p, d, adapter_id=p.adapter_id, now=t.NOW)
            outcome.append("dispatched")
        except PermissionError:
            outcome.append("refused")
    threads = [threading.Thread(target=run) for _ in range(8)]
    [x.start() for x in threads]
    [x.join() for x in threads]
    rec = f.records.load()
    assert outcome == ["refused"] * 8 and len(rec.refusals) == 8 and not rec.attempts
    assert f.destination.snapshot()["effects"] == {}
    opened = Counter(e.check_id for e in rec.check_events if e.phase == "opened")
    closed = Counter(e.check_id for e in rec.check_events if e.phase in ("completed", "interrupted"))
    assert opened == closed and set(opened.values()) == {1}, "every concurrent check must have exactly one opening and one closure"


def test_probe_addauthra_concurrent_decisions_keep_independent_journals(tmp_path):
    t = fx()
    p, r, f, c = make(tmp_path)
    results = []
    threads = [threading.Thread(target=lambda: results.append(f.decide(p, now=t.NOW).result)) for _ in range(6)]
    [x.start() for x in threads]
    [x.join() for x in threads]
    rec = f.records.load()
    per_check = {}
    for e in rec.check_events:
        per_check.setdefault(e.check_id, []).append(e.phase)
    assert results == ["authorized"] * 6 and len(per_check) == 6
    assert all(v[0] == "opened" and v[-1] == "completed" and v.count("opened") == v.count("completed") == 1 for v in per_check.values())
    assert len({tuple(sorted(e.owner.items())) for e in rec.check_events if e.phase == "opened"}) == 6


def test_probe_addauthra_competing_recovery_workers_close_each_abandoned_check_exactly_once(tmp_path):
    t = fx()
    p, r, f, c = make(tmp_path)
    from agent_control_plane.bounded import BoundedRecordStore, CheckEvent, commitment
    for i in range(3):
        f.records.append_check_event(CheckEvent(check_id=f"orphan{i}", phase="opened", stage="effect", recorded_at=t.NOW.isoformat(),
                                                owner={"pid": "1", "token": "dead"}, proposal_commitment=commitment({})))
    counts = []
    threads = [threading.Thread(target=lambda: counts.append(BoundedRecordStore(f.records.path, "run-1").recover_interrupted_checks()))
               for _ in range(6)]
    [x.start() for x in threads]
    [x.join() for x in threads]
    rows = f.records.load().check_events
    assert sum(counts) == 3
    assert Counter((e.check_id, e.phase) for e in rows if e.phase == "interrupted") == {(f"orphan{i}", "interrupted"): 1 for i in range(3)}
    rec = f.records.load()
    assert not rec.attempts and not rec.observations and not rec.reconciliations  # recovery never infers an external outcome


def test_probe_addauthra_reversible_tolerance_needs_unexpired_grant_and_matching_revision_and_scope(tmp_path):
    t = fx()
    late = t.NOW + timedelta(days=3650)
    p, r, f, c = make(tmp_path, reversible=True)
    cached = next(iter(r.statuses.values())).model_copy(deep=True)
    cached.observed_at = (late - timedelta(seconds=1)).isoformat()
    r.grant_status = lambda ref: None
    r.cached_grant_status = lambda ref: cached
    d = f.decide(p, now=late)
    assert d.result == "hold" and "grant_outside_validity" in d.reasons  # a fresh cached positive cannot revive an expired grant
    p, r, f, c = make(tmp_path / "rev", reversible=True)
    cached = next(iter(r.statuses.values())).model_copy(deep=True)
    cached.revision = "2"
    r.grant_status = lambda ref: None
    r.cached_grant_status = lambda ref: cached
    d = f.decide(p, now=t.NOW)
    assert d.result == "hold" and "grant_revision_stale" in d.reasons
    p, r, f, c = make(tmp_path / "scope", reversible=True)
    cached = next(iter(r.statuses.values())).model_copy(deep=True)
    cached.institution_id = "urn:cognous:institution:other"
    r.grant_status = lambda ref: None
    r.cached_grant_status = lambda ref: cached
    d = f.decide(p, now=t.NOW)
    assert d.result == "hold" and f.destination.snapshot()["effects"] == {}


def test_probe_addauthra_a_satisfied_reopen_condition_cannot_dispatch_the_prior_decision(tmp_path):
    t = fx()
    p, r, f, c = make(tmp_path)
    original = r.grant_status
    r.grant_status = lambda ref: None
    held_decision = f.decide(p, now=t.NOW)
    assert held_decision.reopen_conditions == [{"kind": "readable_authority_status"}]
    r.grant_status = original  # the reopen condition is now satisfied
    with pytest.raises(PermissionError):
        f.execute(p, held_decision, adapter_id=p.adapter_id, now=t.NOW)
    assert f.destination.snapshot()["effects"] == {} and not f.records.load().attempts
    fresh = f.decide(p, now=t.NOW)  # reconsideration reruns every binding and issues a new decision
    assert fresh.result == "authorized" and fresh.decision_id != held_decision.decision_id
    # a revoked case reopens only through a successor grant revision, and the old decision is not revived either
    p, r, f, c = make(tmp_path / "revoked")
    status = next(iter(r.statuses.values()))
    status.status = "revoked"
    revoked = f.decide(p, now=t.NOW)
    assert revoked.reopen_conditions[0]["kind"] == "successor_grant_revision"
    status.status = "active"
    with pytest.raises(PermissionError):
        f.execute(p, revoked, adapter_id=p.adapter_id, now=t.NOW)


def test_probe_addauthra_concurrent_duplicate_dispatch_commits_one_effect_and_lost_acknowledgement_is_not_retried_blind(tmp_path):
    t = fx()
    p, r, f, c = make(tmp_path / "dup")
    d = f.decide(p, now=t.NOW)
    done = []

    def run():
        try:
            done.append(f.execute(p, d, adapter_id=p.adapter_id, now=t.NOW)[0].status)
        except PermissionError as exc:
            done.append("refused:" + str(exc))
    threads = [threading.Thread(target=run) for _ in range(8)]
    [x.start() for x in threads]
    [x.join() for x in threads]
    assert list(f.destination.snapshot()["effects"]) == [d.effect_id], done
    p, r, f, c = make(tmp_path / "lost")
    d = f.decide(p, now=t.NOW)
    first, _ = f.execute(p, d, adapter_id=p.adapter_id, now=t.NOW, lose_ack=True)
    assert first.status == "unknown"
    again, observed = f.execute(p, d, adapter_id=p.adapter_id, now=t.NOW)
    assert list(f.destination.snapshot()["effects"]) == [d.effect_id]
    assert again.acknowledgement == {"reconciled_existing": True} and observed.state == "applied"


# ---------------------------------------------------------------- K2: evidence criteria and producer authenticity
def _evidence(r):
    return next(iter(r.evidence.values()))


def _resign(e, key=None):
    t = fx()
    from agent_control_plane.bounded import _canonical_bytes
    e.validation_record["signature"] = (key or t.KEY).sign(_canonical_bytes(e.validation_record["statement"])).hex()


def _reasons(f, p):
    d = f.decide(p, now=fx().NOW)
    assert d.result == "hold" and f.destination.snapshot()["effects"] == {} and not f.records.load().attempts
    return d.reasons


def test_probe_addauthra_planner_cannot_nominate_its_own_key_as_the_validator(tmp_path):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    t = fx()
    attacker = Ed25519PrivateKey.generate()
    # 1. a record claiming the trusted producer id but signed by the planner's key
    p, r, f, c = make(tmp_path / "a")
    _resign(_evidence(r), attacker)
    assert _reasons(f, p) == ["evidence_signature_invalid"]
    # 2. the planner embeds its public key in the envelope or the signed statement
    for where in ("envelope", "statement"):
        p, r, f, c = make(tmp_path / where)
        e = _evidence(r)
        pub = attacker.public_key().public_bytes_raw().hex()
        (e.validation_record if where == "envelope" else e.validation_record["statement"])["public_key"] = pub
        _resign(e, attacker)
        assert _reasons(f, p) == ["evidence_record_invalid"]
    # 3. the planner names itself (and its key) as the producer in the criterion or in the profile section of the context
    p, r, f, c = make(tmp_path / "c")
    spec = r.contexts[t.PROFILE]["runtime_authority"]
    next(iter(spec["evidence_criteria"].values()))["producer_id"] = "planner"
    e = _evidence(r)
    e.validation_record["statement"]["producer_id"] = "planner"
    _resign(e, attacker)
    reasons = _reasons(f, p)
    assert "evidence_producer_untrusted" in reasons and "runtime_authority_approval_mismatch" in reasons
    p, r, f, c = make(tmp_path / "d")
    r.contexts[t.PROFILE]["runtime_authority"]["producer_keys"] = {"synthetic-validator": attacker.public_key().public_bytes_raw().hex()}
    _resign(_evidence(r), attacker)
    reasons = _reasons(f, p)
    assert "runtime_authority_field_unsupported" in reasons and "evidence_signature_invalid" in reasons


def test_probe_addauthra_evidence_is_authenticated_before_its_criterion_is_evaluated(tmp_path):
    """Admission, signature and subject binding are verified first: a record that also fails the criterion reports only the earlier,
    authentication-level reason, never evidence_criterion_unmet."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    t = fx()
    p, r, f, c = make(tmp_path / "sig", kind="minimum_count")
    t.sign_evidence(_evidence(r), count=5)
    _resign(_evidence(r), Ed25519PrivateKey.generate())
    assert _reasons(f, p) == ["evidence_signature_invalid"]
    p, r, f, c = make(tmp_path / "prod", kind="minimum_count")
    e = _evidence(r)
    t.sign_evidence(e, count=5)
    e.validation_record["statement"]["producer_id"] = "agent"
    _resign(e)
    assert _reasons(f, p) == ["evidence_producer_untrusted"]
    p, r, f, c = make(tmp_path / "subj", kind="minimum_count")
    t.sign_evidence(_evidence(r), count=5, tenant_id="other-tenant")
    assert _reasons(f, p) == ["evidence_subject_mismatch"]


def test_probe_addauthra_substituted_manifest_and_malformed_producer_values_hold(tmp_path):
    t = fx()
    p, r, f, c = make(tmp_path / "manifest")
    e = _evidence(r)
    e.validation_record["statement"]["subject_digest"] = "sha256:" + "0" * 64  # correctly signed statement about a different set
    _resign(e)
    assert _reasons(f, p) == ["evidence_subject_mismatch"]
    p, r, f, c = make(tmp_path / "type", kind="minimum_count")
    t.sign_evidence(_evidence(r), count="40")  # wrong type
    assert _reasons(f, p) == ["evidence_criterion_unmet"]
    p, r, f, c = make(tmp_path / "missing")
    e = _evidence(r)
    del e.validation_record["statement"]["values"]["validated_members"]  # missing required validator output
    _resign(e)
    assert _reasons(f, p) == ["evidence_criterion_unmet"]
    p, r, f, c = make(tmp_path / "extra")
    e = _evidence(r)
    e.validation_record["statement"]["unexpected"] = 1
    _resign(e)
    assert _reasons(f, p) == ["evidence_record_invalid"]


def test_probe_addauthra_expired_or_not_current_evidence_holds_even_when_signed_and_complete(tmp_path):
    t = fx()
    p, r, f, c = make(tmp_path / "old")
    e = _evidence(r)
    e.observed_at = (t.NOW - timedelta(hours=2)).isoformat()
    t.sign_evidence(e)
    assert "required_evidence_stale_or_future" in _reasons(f, p)
    p, r, f, c = make(tmp_path / "state")
    _evidence(r).state = "stale"
    assert "required_evidence_not_current" in _reasons(f, p)


def test_probe_addauthra_criterion_change_after_approval_cannot_broaden_the_approved_gate(tmp_path):
    t = fx()
    p, r, f, c = make(tmp_path / "weaker", kind="minimum_count")
    next(iter(r.contexts[t.PROFILE]["runtime_authority"]["evidence_criteria"].values()))["minimum_count"] = 0
    assert "runtime_authority_approval_mismatch" in _reasons(f, p)
    p, r, f, c = make(tmp_path / "dropped")
    r.contexts[t.PROFILE]["runtime_authority"]["evidence_criteria"] = {}
    reasons = _reasons(f, p)
    assert "evidence_criterion_unsupported" in reasons and "runtime_authority_approval_mismatch" in reasons


def test_probe_addauthra_evidence_refusal_records_the_criterion_reference(tmp_path):
    """Addendum K2 refusal and reporting: 'Record the reason vocabulary version and criterion reference.' Strict reading: the hold
    record carries a reference (version/digest/id) to the approval-owned criterion that was applied, beyond the aggregate approval
    commitment."""
    t = fx()
    p, r, f, c = make(tmp_path)
    t.sign_evidence(_evidence(r), members=t.MEMBERS[:30])
    d = f.decide(p, now=t.NOW)
    assert d.reasons == ["evidence_criterion_unmet"] and d.reason_vocabulary_version == "runtime-authority-reasons/0.1"
    blob = json.dumps(d.model_dump(mode="json"))
    assert "criterion" in blob.replace("evidence_criterion_unmet", ""), "no criterion reference (version/digest/id) is recorded with the hold"


# ---------------------------------------------------------------- K3: required input set (control-plane half)
def test_probe_addauthra_planner_supplied_input_set_digest_cannot_establish_completeness(tmp_path):
    t = fx()
    p, r, f, c = make(tmp_path / "digest")
    spec = r.contexts[t.PROFILE]["runtime_authority"]
    spec["required_inputs"] = spec["required_inputs"][:-1]  # planner shrinks the set and recomputes a matching digest
    from agent_control_plane.bounded import commitment
    spec["required_inputs_digest"] = commitment(spec["required_inputs"])
    assert "runtime_authority_approval_mismatch" in _reasons(f, p)  # the authoritative approval binding no longer matches
    p, r, f, c = make(tmp_path / "plain")
    r.contexts[t.PROFILE]["runtime_authority"]["required_inputs_digest"] = "sha256:" + "0" * 64
    assert "required_input_set_invalid" in _reasons(f, p)


# ---------------------------------------------------------------- K4: purpose-bound grants
def test_probe_addauthra_planner_cannot_replace_or_cross_tenant_the_purpose_binding(tmp_path):
    t = fx()
    p, r, f, c = make(tmp_path / "swap", purpose=True)
    r.contexts[t.PROFILE]["grant"]["purpose_ref"] = {"system": "synthetic-cases", "record_id": "case-2", "epoch": "epoch-1"}
    reasons = _reasons(f, p)
    assert "runtime_authority_approval_mismatch" in reasons and "purpose_binding_invalid" in reasons
    p, r, f, c = make(tmp_path / "tenant", purpose=True)
    r.purpose.tenant_id = "other-tenant"
    assert "purpose_binding_invalid" in _reasons(f, p)
    p, r, f, c = make(tmp_path / "domain", purpose=True)
    r.purpose.authority_domain = "other-domain"
    assert "purpose_binding_invalid" in _reasons(f, p)


def test_probe_addauthra_purpose_snapshot_and_epoch_are_preserved_in_the_record(tmp_path):
    t = fx()
    p, r, f, c = make(tmp_path, purpose=True)
    d = f.decide(p, now=t.NOW)
    row = next(i for i in d.resolution_inputs if i.input_type == "purpose")
    assert row.observed == {"state": "open", "observed_at": t.NOW.isoformat(), "epoch": "epoch-1", "epoch_capability": "authoritative"}
    assert row.record_commitment and not row.missing


def test_probe_addauthra_reversible_class_tolerance_cannot_override_a_known_purpose_closure_or_outage(tmp_path):
    t = fx()
    p, r, f, c = make(tmp_path / "closed", purpose=True, reversible=True)
    r.purpose.state = "closed"
    assert "purpose_closed" in _reasons(f, p)
    p, r, f, c = make(tmp_path / "epoch", purpose=True, reversible=True)
    r.purpose.epoch = "epoch-2"
    assert "purpose_epoch_changed" in _reasons(f, p)
    p, r, f, c = make(tmp_path / "outage", purpose=True, reversible=True)

    def unavailable(ref):
        raise TimeoutError("synthetic outage")
    r.purpose_status = unavailable
    assert "purpose_unreadable" in _reasons(f, p)  # no purpose-outage grace is available to a reversible class either
    p, r, f, c = make(tmp_path / "stale", purpose=True, reversible=True)
    r.purpose.observed_at = (t.NOW - timedelta(hours=1)).isoformat()
    assert "purpose_unreadable" in _reasons(f, p)


def test_probe_addauthra_legacy_grant_without_purpose_or_expiry_is_held_not_defaulted(tmp_path):
    t = fx()
    p, r, f, c = make(tmp_path)
    grant = r.contexts[t.PROFILE]["grant"]
    del grant["expires_at"]
    t.bind_approval(r, c)
    assert "grant_expiry_required" in _reasons(f, p)
    assert "expires_at" not in r.contexts[t.PROFILE]["grant"] and "purpose_ref" not in r.contexts[t.PROFILE]["grant"]  # nothing synthesised


# ---------------------------------------------------------------- K5: versioned refusal vocabulary
def test_probe_addauthra_hold_and_refusal_rows_carry_the_vocabulary_version_and_legacy_rows_stay_unknown(tmp_path):
    t = fx()
    from agent_control_plane.reason_vocabulary import refusal_trends
    p, r, f, c = make(tmp_path)
    next(iter(r.statuses.values())).status = "suspended"
    d = f.decide(p, now=t.NOW)
    assert d.reasons == ["grant_suspended"] and d.reason_vocabulary_version == "runtime-authority-reasons/0.1"
    rows = [{"reason_vocabulary_version": "v1", "reasons": ["a"]}, {"reason_vocabulary_version": "v2", "reasons": ["a"]},
            {"reasons": ["a"]}, {"reason_vocabulary_version": "", "reasons": ["a"]}]
    report = refusal_trends([], rows, previous_exposure=0, current_exposure=4)
    assert report["unversioned_rows"] == 2
    series = {(x["version"], x["code"]): x["count"] for x in report["series"]}
    assert series == {("v1", "a"): 1, ("v2", "a"): 1, ("unknown", "a"): 2}, "legacy rows must stay 'unknown', never a guessed version"


def test_probe_addauthra_registry_declares_operands_for_every_recomputable_code_and_none_for_typed_only(tmp_path):
    from pathlib import Path
    import os
    registry = _reasons_registry()
    kinds = Counter(v["reason_kind"] for v in registry["codes"].values())
    assert set(kinds) <= {"recomputable", "typed_only"} and kinds["recomputable"] >= 1
    for code, spec in registry["codes"].items():
        if spec["reason_kind"] == "recomputable":
            assert spec.get("operands") and all(isinstance(k, str) and isinstance(v, str) for k, v in spec["operands"].items()), code
        else:
            assert not spec.get("operands"), f"typed_only code {code} must not invent operands"
        assert spec.get("description"), code


# ---------------------------------------------------------------- additional K1-K5 probes (trust boundary, ordering, vocabulary)
def test_probe_addauthra_unauthenticated_resolver_cannot_authorize_or_derive_a_revocation(tmp_path):
    t = fx()
    p, r, f, c = make(tmp_path)
    cfg = c.model_copy(update={"allow_synthetic_resolver": False})  # a host that does not accept a synthetic resolver
    f.runtime_authority_profile = cfg
    t.bind_approval(r, cfg)
    next(iter(r.statuses.values())).status = "revoked"
    d = f.decide(p, now=t.NOW)
    assert d.result == "hold" and d.reasons == ["resolver_not_authenticated"], d.reasons
    assert not d.resolution_inputs and f.destination.snapshot()["effects"] == {}  # nothing was read, so nothing could be 'verified'


def test_probe_addauthra_catalogue_digest_is_bound_to_each_decision_and_changes_with_the_catalogue(tmp_path):
    t = fx()
    from agent_control_plane.bounded import commitment
    p, r, f, c = make(tmp_path / "one")
    d1 = f.decide(p, now=t.NOW)
    assert d1.binding.runtime_authority["catalogue_digest"] == commitment(c.model_dump(mode="json"))
    p, r, f, c = make(tmp_path / "two", reversible=True)
    d2 = f.decide(p, now=t.NOW)
    assert d2.binding.runtime_authority["catalogue_digest"] != d1.binding.runtime_authority["catalogue_digest"]


def test_probe_addauthra_key_rotation_or_change_of_the_admitted_key_set_requires_approval_renewal(tmp_path):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    t = fx()
    from agent_control_plane.runtime_authority import RuntimeAuthorityProfile
    p, r, f, c = make(tmp_path)
    rotated = RuntimeAuthorityProfile(catalogue_version=c.catalogue_version, actions=c.actions, allow_synthetic_resolver=True,
                                      producer_keys={"synthetic-validator": Ed25519PrivateKey.generate().public_key().public_bytes_raw().hex()})
    f.runtime_authority_profile = rotated
    d = f.decide(p, now=t.NOW)
    assert d.result == "hold" and "runtime_authority_approval_mismatch" in d.reasons
    assert f.destination.snapshot()["effects"] == {}


@pytest.mark.parametrize("mutation", [{"kind": "python_expression"}, {"kind": "manual_assessment"}, {"expression": "validated_count > 3"},
                                      {"version": "evidence-criterion/9"}])
def test_probe_addauthra_criterion_language_is_closed_no_expressions_no_unknown_kinds_or_versions(tmp_path, mutation):
    t = fx()
    p, r, f, c = make(tmp_path, kind="minimum_count")
    next(iter(r.contexts[t.PROFILE]["runtime_authority"]["evidence_criteria"].values())).update(mutation)
    t.bind_approval(r, c)  # re-approved, so the hold below is the criterion language's own refusal, not an approval mismatch
    assert _reasons(f, p) == ["evidence_criterion_unsupported"]


def test_probe_addauthra_a_profile_requiring_atomic_enforcement_rejects_an_adapter_without_it(tmp_path):
    t = fx()
    p, r, f, c = make(tmp_path)
    spec = r.contexts[t.PROFILE]["runtime_authority"]
    spec["expected_effective_grant_digest"] = "sha256:" + "a" * 64
    spec["effective_grant_derivation_version"] = "effective-grant/0.1"
    t.bind_approval(r, c)
    d = f.decide(p, now=t.NOW)
    assert d.result == "authorized"
    with pytest.raises(PermissionError, match="atomic_authority_capability_unavailable"):
        f.execute(p, d, adapter_id=p.adapter_id, now=t.NOW)
    assert f.destination.snapshot()["effects"] == {} and not f.records.load().attempts
    spec["effective_grant_derivation_version"] = "effective-grant/9"  # an unknown derivation version holds
    t.bind_approval(r, c)
    assert "effective_grant_binding_invalid" in _reasons(f, p)


def test_probe_addauthra_purpose_closure_between_decision_and_effect_refuses_at_the_effect_boundary(tmp_path):
    t = fx()
    p, r, f, c = make(tmp_path, purpose=True)
    d = f.decide(p, now=t.NOW)
    assert d.result == "authorized"
    r.purpose.state = "closed"
    with pytest.raises(PermissionError):
        f.execute(p, d, adapter_id=p.adapter_id, now=t.NOW)
    rec = f.records.load()
    assert rec.refusals[-1].reasons == ["purpose_closed"] and not rec.attempts and f.destination.snapshot()["effects"] == {}
    assert any(i.input_type == "purpose" for i in rec.refusals[-1].resolution_inputs)


def test_probe_addauthra_purpose_bound_positive_control_changes_the_destination_and_is_verified_independently(tmp_path):
    t = fx()
    p, r, f, c = make(tmp_path, purpose=True)
    d = f.decide(p, now=t.NOW)
    attempt, observation = f.execute(p, d, adapter_id=p.adapter_id, now=t.NOW)
    state = f.destination.snapshot()["effects"]  # read from the destination itself, not from the acknowledgement
    assert list(state) == [d.effect_id] and state[d.effect_id]["state"] == "applied" and state[d.effect_id]["grant_id"] == d.binding.grant_id
    assert attempt.status == "acknowledged" and observation.state == "applied"


def test_probe_addauthra_every_vocabulary_change_kind_is_recorded_append_only_and_invalid_transitions_are_refused(tmp_path):
    t = fx()
    from agent_control_plane.bounded import commitment
    from agent_control_plane.reason_vocabulary import VocabularyChange
    p, r, f, c = make(tmp_path)
    d = f.decide(p, now=t.NOW)
    next(iter(r.statuses.values())).status = "revoked"
    with pytest.raises(PermissionError):
        f.execute(p, d, adapter_id=p.adapter_id, now=t.NOW)
    old_rows = [x.model_dump() for x in f.records.load().refusals]
    plan = [("addition", [], ["x"]), ("retirement", ["x"], []), ("rename", ["x"], ["y"]), ("split", ["y"], ["y1", "y2"])]
    for i, (kind, before, after) in enumerate(plan):
        f.records.append_vocabulary_change(VocabularyChange(
            change_id=f"c{i}", previous_version=f"v{i}", version=f"v{i + 1}", registry_digest=commitment({"i": i}), kind=kind,
            previous_codes=before, codes=after, acknowledged_by="synthetic-owner", acknowledged_at=t.NOW.isoformat()))
    rec = f.records.load()
    assert [x.kind for x in rec.vocabulary_changes] == [k for k, _, _ in plan]
    assert [x.model_dump() for x in rec.refusals] == old_rows  # history is never reinterpreted
    for bad in ({"previous_version": "v9", "version": "v9", "kind": "addition", "codes": ["z"], "previous_codes": []},
                {"previous_version": "v9", "version": "v10", "kind": "split", "codes": ["z"], "previous_codes": ["q"]},
                {"change_id": "c0", "previous_version": "v9", "version": "v10", "kind": "addition", "codes": ["z"], "previous_codes": []}):
        with pytest.raises(ValueError):
            f.records.append_vocabulary_change(VocabularyChange(**({"change_id": "bad", "registry_digest": "d", "acknowledged_by": "o",
                                                                    "acknowledged_at": t.NOW.isoformat()} | bad)))
    with pytest.raises(ValueError):
        VocabularyChange(change_id="n", previous_version="a", version="b", registry_digest="d", kind="addition", previous_codes=[],
                         codes=[], acknowledged_by="", acknowledged_at=t.NOW.isoformat())  # acknowledgement metadata is mandatory


# ---- strict-reading probes: places where the addendum's literal wording asks for more than the pinned component records or orders
def test_probe_addauthra_registry_declares_applicable_reopen_predicates(tmp_path):
    """Addendum K5: 'The governed registry defines each code, meaning, reason_kind, operand schema and applicable reopen predicates.'"""
    import os
    from pathlib import Path
    registry = _reasons_registry()
    for code in ("status_unreadable", "grant_revoked"):  # the two codes for which the gate emits a reopen_condition
        assert any("reopen" in key for key in registry["codes"][code]), f"{code}: registry entry {sorted(registry['codes'][code])} has no reopen predicate"


def test_probe_addauthra_refusal_trend_report_names_unmapped_codes(tmp_path):
    """Addendum K5: the window report covers 'each code's count over total refusals, record completeness and unmapped codes'."""
    from agent_control_plane.reason_vocabulary import refusal_trends
    report = refusal_trends([{"reason_vocabulary_version": "v1", "reasons": ["known"]}] * 5,
                            [{"reason_vocabulary_version": "v1", "reasons": ["known"]}, {"reason_vocabulary_version": "v1", "reasons": ["not_in_registry"]}],
                            previous_exposure=10, current_exposure=10)
    assert any("unmapped" in key or "unknown_code" in key for key in report), f"report keys: {sorted(report)}"


def test_probe_addauthra_freshness_is_verified_before_the_criterion_is_evaluated(tmp_path):
    """Addendum K2: 'Verify producer admission, signature, scope, subject binding and freshness before evaluating the criterion.'
    Stale evidence whose values also miss the criterion must be refused for staleness alone (the criterion is never evaluated)."""
    t = fx()
    p, r, f, c = make(tmp_path, kind="minimum_count")
    e = _evidence(r)
    e.observed_at = (t.NOW - timedelta(hours=2)).isoformat()
    t.sign_evidence(e, count=5)
    reasons = _reasons(f, p)
    assert "required_evidence_stale_or_future" in reasons and "evidence_criterion_unmet" not in reasons, reasons
