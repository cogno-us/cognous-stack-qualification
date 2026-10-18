"""N4 composed scenarios: opt-in merge-record/0.1 across control plane and runtime (addendum 101726_B, N1 rule 2, L3, M4).

SPDX-License-Identifier: Apache-2.0

Every scenario follows the N4 refusal-test template (suites/_refusal_template.py, legs a-e) or, where the scenario is a record or a
ledger property rather than an effect-time refusal, the same five legs written out in the test (marked "legs" in the docstring).

Route: control plane BoundedAuthorizationWorkflow -> runtime PinnedControlPlaneExecutor -> the runtime's opt-in destinations.
Synthetic fixtures only; no network effects; the compensation obligation is a record and nothing is compensated.

What these prove: with the opt-in profile, two operations later ruled to be one are folded by a record over operation ids only; a
second effect for the merged operation is suppressed before dispatch; a merge after two effects landed emits a record-only
compensation obligation listing the effect id of every applied attempt; a merge by an unfunded authority holds; a merge is only as
good as the equivalence rule digest, which must be adopted by a signed, independent ``merge_equivalence_rule`` revision; a rule
change appends rows and never edits one. What they do not prove: tamper evidence (a holder of the record-store key can rewrite
rows), that two operations really are one (the equivalence rule is a named, signed input, not a judgement made here), that a
compensation is ever carried out, or cross-host fencing.

Provenance of "expected today" values (leg e), per test. The ``*_today`` tests were RUN against pristine control plane main 3f6a766
and runtime main 6bfb77ee (the default path: no merge concept, so two operations produce two effects and nothing can fold them). The
profile tests describe new opt-in behaviour: there is no "expected today" value, and they FAIL on those mains by design (the
profile is absent). The code-reading label on the profile expectations names the files that implement them.
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import _refusal_template as T  # noqa: E402
from _oi_flow import OPERATION, Flow  # noqa: E402

PRINCIPAL = "urn:cognous:principal:refund-service"
MERGER, UNFUNDED = "urn:cognous:principal:merger", "urn:cognous:principal:nobody"
REQUESTER, SIGNER, POLICY_SIGNER = ("urn:cognous:principal:rule-requester", "urn:cognous:principal:rule-signer",
                                    "urn:cognous:principal:policy-signer")
RULE = "urn:cognous:merge-rule:same-refund-case"
D1, D2 = "sha256:" + "1" * 64, "sha256:" + "2" * 64
B = "op-order-100/refund-2"
NEW_BEHAVIOUR = "opt-in merge-record/0.1 (new): no expected-today value; fails on the pinned mains by design"
PROVENANCE_PROFILE = T.Provenance("code-reading", "control plane merge.py + bounded.py (record_merge, _effect_gate_n4, _join_attempt, "
                                  "dispatch key) and runtime engine/operation_identity_destination.py; " + NEW_BEHAVIOUR)
PROVENANCE_TODAY = T.Provenance("run", "control plane main 3f6a766 and runtime main 6bfb77ee, pristine checkouts, this suite's *_today tests "
                                "(Flow with the operation-identity profile, no merge profile)")


# ----------------------------------------------------------------------------------------------------------- the flow
def merge_profile(funded):
    def update(flow):
        from agent_control_plane.merge import MergeProfile
        return {"merge": MergeProfile(funded_authorities=list(funded))}
    return update


def adopt(flow, digest=D1, *, rid="adopt-merge-rule", frm=None):
    from agent_control_plane.rule_revision import RuleRevision, append_rule_revision
    append_rule_revision(flow.f.records, flow.f.rule_revision_profile, RuleRevision(
        revision_id=rid, rule_kind="merge_equivalence_rule", rule_ref=RULE, from_digest=frm, to_digest=digest, reviser=REQUESTER,
        signer=SIGNER, authority_ref="urn:cognous:authority:rule-1", reason="synthetic", recorded_at=flow.NOW.isoformat()))


def setup_rules(flow, *, rule=True):
    """Configure the N2 signer set, adopt the fixture policy so decisions pass, adopt the merge equivalence rule (digest D1)."""
    from agent_control_plane.rule_revision import RuleRevision, RuleRevisionProfile, append_rule_revision
    from tests.test_bounded_authorization import POLICY_REF
    digest = flow.cp.commitment({"policy": "v1"})
    flow.r.policies[POLICY_REF].digest = digest
    flow.f.rule_revision_profile = RuleRevisionProfile(signers=[SIGNER, POLICY_SIGNER])
    append_rule_revision(flow.f.records, flow.f.rule_revision_profile, RuleRevision(
        revision_id="adopt-policy", rule_kind="policy", rule_ref=POLICY_REF, from_digest=None, to_digest=digest, reviser=REQUESTER,
        signer=POLICY_SIGNER, authority_ref="synthetic-authority:1", reason="synthetic", recorded_at=flow.NOW.isoformat()))
    if rule:
        adopt(flow)


def build(work, mp, *, funded=(MERGER,), rule=True):
    flow = Flow(work, mp, identity=True, cfg_update=merge_profile(funded), setup=lambda f: setup_rules(f, rule=rule))
    flow.add_operation(B, "case-2")
    return flow


def merge(flow, *, by=MERGER, digest=D1, folded=(B,), survivor=OPERATION):
    return flow.f.record_merge(survivor_operation_id=survivor, folded_operation_ids=list(folded), equivalence_rule_ref=RULE,
                               equivalence_rule_digest=digest, merged_by=by, authority_ref="urn:cognous:authority:merge-1",
                               reason="same refund, filed twice", now=flow.NOW)


def document(flow):
    return json.loads(flow.f.records.path.read_text(encoding="utf-8"))


def run_both(flow):
    """A and B each applied under their own operation id (the case the merge is for)."""
    a = flow.run(flow.d1)
    flow.decide_operation(B)
    b = flow.run_operation(B)
    assert a.status == b.status == "executed", (a.status, b.status)


def record(record_property, name, adapter_result=None, report=None, text=None):
    record_property("principal", PRINCIPAL)
    record_property(name, T.report_json(adapter_result, report) if adapter_result is not None else text)


# ------------------------------------------------------------------------------------------------ refusal adapter
class MergeAdapter(T.Adapter):
    """A applied; B decided; the merge is the change; running B is the call. The refusal row is a projection of the real refusal
    row plus the real merge row (the input-version strings are built from real values; nothing is invented)."""

    def build(self, work, mp):
        flow = build(work, mp)
        assert flow.run(flow.d1).status == "executed"
        flow.decide_operation(B)
        return flow

    def apply_change(self, flow):
        flow.merge_row = merge(flow)
        assert flow.merge_row.outcome == "merged", flow.merge_row.reasons

    def execute(self, flow):
        return flow.run_operation(B)

    def effect_id(self, flow):
        return flow.decisions[B].effect_id

    def ledger_effect_ids(self, flow):
        return flow.ledger_effect_ids()

    def refusal_rows(self, flow):
        rows = []
        for r in flow.record().refusals:
            row = r.model_dump(mode="json")
            row = {k: row[k] for k in ("refusal_id", "effect_id", "stage", "reasons")}
            m = flow.merge_row
            row["changed_inputs"] = [{"input_type": "operation", "input_id": B, "expected_version": "merged_into=none",
                                      "observed_version": f"merged_into={m.survivor_operation_id};merge_id={m.merge_id};outcome={m.outcome}"}]
            rows.append(row)
        return rows

    def disable_refusal_writer(self, flow):
        flow.f.records.append_refusal = lambda value: None  # only the evidence row is lost; the gate still refuses

    def policy_versions_observed_at_enforcement(self, flow, stage):
        return {}


def run_template(adapter, spec, tmp_path, record_property):
    result = T.run_refusal_scenario(adapter, spec, tmp_path, pytest.MonkeyPatch)
    assert result.legs_passed == T.LEGS
    holders = [{"holder_id": B, "kind": "operation"}, {"holder_id": "urn:cognous:issuance:1", "kind": "mandate"}]
    report = T.classify_holders(holders, [result.refusal_row])
    record(record_property, "n4_" + spec.name, result, report)
    return result, report


# ------------------------------------------------------------------------------------ merge_before_effect_suppresses_second
SUPPRESSED = T.RefusalSpec(
    name="merge_before_effect_suppresses_second",
    reasons=("operation_merged_effect_exists",),
    changed_inputs=(T.ChangedInput("operation", B),),
    provenance=PROVENANCE_PROFILE)


def test_merge_before_effect_suppresses_second(tmp_path, record_property):
    """Legs a-e via the template. A applied; B is authorized and unexecuted; the two are merged; running B is refused before
    dispatch and the destination never sees its effect id. The control (same call, no merge) lands B's effect."""
    result, report = run_template(MergeAdapter(), SUPPRESSED, tmp_path / "template", record_property)
    assert [h["holder_id"] for h in report["witnessed_refusals"]] == [B]
    assert [h["classification"] for h in report["unenumerated_authority_needing_containment"]] == [T.CLASSIFICATION_UNKNOWN]
    mp = pytest.MonkeyPatch()
    try:
        adapter = MergeAdapter()
        flow = adapter.build(tmp_path / "extra", mp)
        adapter.apply_change(flow)
        a_effect = flow.d1.effect_id
        assert adapter.execute(flow).status == "denied"
        assert flow.ledger_effect_ids() == [a_effect], "one effect at the destination: A's"
        assert {x.effect_id for x in flow.latest_attempts()} == {a_effect}, "no attempt was made for B"
        row = flow.merge_row
        assert (row.survivor_operation_id, row.folded_operation_ids) == (OPERATION, [B])
        assert "compensation_obligations" not in document(flow), "one effect landed: nothing to compensate"
    finally:
        mp.undo()


def test_merge_suppresses_whichever_operation_applies_second(tmp_path):
    """The merged operation has one effect budget: B (folded) applies first, then A (survivor) is the one suppressed. B dispatched
    under the survivor's id, so a destination that stores our id would refuse a racing A as well."""
    mp = pytest.MonkeyPatch()
    try:
        flow = build(tmp_path, mp)
        flow.decide_operation(B)
        assert merge(flow).outcome == "merged"
        assert flow.run_operation(B).status == "executed"
        assert flow.dest.operation_effect((flow.d1.binding.principal, "customer-refunds", OPERATION)) == flow.decisions[B].effect_id
        assert flow.run_operation(OPERATION).status == "denied"
        assert flow.ledger_effect_ids() == [flow.decisions[B].effect_id]
        joins = {j.operation_id: j for j in flow.record().attempt_joins}
        assert joins[B].merged_into == OPERATION and OPERATION not in joins, "merged_into names an operation id, set on the folded one"
    finally:
        mp.undo()


def test_two_operations_two_effects_and_no_way_to_fold_them_today(tmp_path):
    """Expected today (ran, default path): two operations produce two effects; there is no merge record to fold them."""
    PROVENANCE_TODAY.validate()
    mp = pytest.MonkeyPatch()
    try:
        flow = Flow(tmp_path, mp, identity=True)
        flow.add_operation(B, "case-2")
        a = flow.run(flow.d1)
        flow.decide_operation(B)
        b = flow.run_operation(B)
        assert a.status == b.status == "executed" and len(flow.ledger_effect_ids()) == 2
        with pytest.raises((AttributeError, PermissionError)):
            merge(flow)
        assert not {"merge_records", "compensation_obligations"} & set(document(flow))
    finally:
        mp.undo()


# --------------------------------------------------------- merge_after_both_applied_emits_compensation_obligation
def check_obligation(flow, ledger_before):
    """Leg (b) of the obligation scenarios: the obligation names the merge and every applied attempt's effect id (read back from
    the destination ledger independently), the merge changed nothing at the destination, and nothing was executed."""
    record_ = flow.record()
    (row,) = [m for m in record_.merge_records]
    assert row.outcome == "merged" and row.compensation_obligation_id, "no obligation named by the merge record"
    (obligation,) = record_.compensation_obligations
    assert obligation.obligation_id == row.compensation_obligation_id and obligation.merge_id == row.merge_id
    assert sorted(obligation.effect_ids) == sorted(flow.ledger_effect_ids()) == sorted(ledger_before)
    assert obligation.status == "recorded" and obligation.execution == "not_executed"
    assert flow.ledger_effect_ids() == ledger_before, "record only: nothing was compensated, reversed or sent"
    return obligation


def test_merge_after_both_applied_emits_compensation_obligation(tmp_path, record_property):
    """Legs written out. (a) negative: the merge writes nothing at the destination and adds no attempt; (b) the obligation lists the
    effect id of every applied attempt, equal to the independent ledger read; (c) control: a merge before the second effect landed
    emits no obligation (one effect); (d) mutation: with the obligation writer disabled leg (b) fails; (e) provenance."""
    PROVENANCE_PROFILE.validate()
    mp = pytest.MonkeyPatch()
    try:
        flow = build(tmp_path / "real", mp)
        run_both(flow)
        before, attempts = flow.ledger_effect_ids(), len(flow.record().attempts)
        assert len(before) == 2
        assert merge(flow).outcome == "merged"
        assert len(flow.record().attempts) == attempts                                  # (a)
        obligation = check_obligation(flow, before)                                      # (b)
        assert obligation.effect_ids_by_operation == {OPERATION: [flow.d1.effect_id], B: [flow.decisions[B].effect_id]}
        assert obligation.survivor_operation_id == OPERATION and obligation.operation_ids == sorted([OPERATION, B])
        record(record_property, "n4_merge_after_both_applied", text=json.dumps(obligation.model_dump(mode="json"), indent=2, sort_keys=True))

        control = build(tmp_path / "control", mp)                                        # (c)
        assert control.run(control.d1).status == "executed"
        control.decide_operation(B)
        assert merge(control).outcome == "merged" and control.run_operation(B).status == "denied"
        assert "compensation_obligations" not in document(control) and len(control.ledger_effect_ids()) == 1

        import agent_control_plane.merge as merge_module                                 # (d)
        mutant = build(tmp_path / "mutant", mp)
        run_both(mutant)
        original = merge_module.resolve_merge
        mp.setattr(merge_module, "resolve_merge", lambda *a, **k: (lambda r: (r[0].model_copy(update={"compensation_obligation_id": None}), None))(original(*a, **k)))
        merge(mutant)
        with pytest.raises(AssertionError):
            check_obligation(mutant, mutant.ledger_effect_ids())
    finally:
        mp.undo()


# ----------------------------------------------------------------------------------- merge_by_unfunded_authority_holds
def check_held(flow):
    """Leg (b): the unfunded merge is a recorded hold with no effect: B is not folded and its effect lands."""
    row = merge(flow, by=UNFUNDED)
    assert row.outcome == "held" and row.reasons == ["merge_authority_unfunded"], (row.outcome, row.reasons)
    assert document(flow)["merge_records"][-1]["merged_by"] == UNFUNDED
    assert flow.run_operation(B).status == "executed", "a held merge changed nothing: B's effect is not suppressed"
    assert len(flow.ledger_effect_ids()) == 2


def test_merge_by_unfunded_authority_holds(tmp_path, record_property):
    """Legs written out. (a) negative: the held merge folds nothing (no merged_into, no suppression); (b) it is recorded as a
    hold naming the unfunded authority; (c) control: the same merge by a funded authority suppresses B; (d) mutation: with the
    funded set widened to include the authority (the check disabled) leg (b) fails; (e) provenance."""
    PROVENANCE_PROFILE.validate()
    mp = pytest.MonkeyPatch()
    try:
        flow = MergeAdapter().build(tmp_path / "real", mp)
        check_held(flow)
        record(record_property, "n4_merge_by_unfunded_authority", text=json.dumps(document(flow)["merge_records"][-1], indent=2, sort_keys=True))
        control = MergeAdapter().build(tmp_path / "control", mp)
        assert merge(control, by=MERGER).outcome == "merged" and control.run_operation(B).status == "denied"
        mutant = (lambda f: f)(build(tmp_path / "mutant", mp, funded=(MERGER, UNFUNDED)))
        assert mutant.run(mutant.d1).status == "executed"
        mutant.decide_operation(B)
        with pytest.raises(AssertionError):
            check_held(mutant)
    finally:
        mp.undo()


# ------------------------------------------------------------------------------------ merge_record_names_rule_digest
def test_merge_record_names_rule_digest(tmp_path, record_property):
    """Legs written out. (a) negative: a merge naming a digest nobody adopted (``unknown``) or an unsigned/self-signed row folds
    nothing; (b) the record names the digest it relied on and how far verification went; (c) control: the adopted digest folds;
    (d) mutation: with rule resolution always answering adopted, the unadopted digest folds and the check fails; (e) provenance."""
    PROVENANCE_PROFILE.validate()
    mp = pytest.MonkeyPatch()
    try:
        flow = build(tmp_path / "real", mp)
        flow.decide_operation(B)
        unknown = merge(flow, digest=D2)                                                 # (a)
        assert unknown.outcome == "unknown" and unknown.reasons == ["merge_rule_unknown"] and unknown.equivalence_rule_digest == D2
        assert "digest_mismatch_with_adopted" in unknown.rule_findings and unknown.rule_state == "unknown"
        assert flow.run_operation(OPERATION).status == "executed" and flow.run_operation(B).status == "executed", "an unknown merge has no effect: both landed"
        # an unsigned row and a self-signed row never adopt a rule
        bare = build(tmp_path / "bare", mp, rule=False)
        bare.decide_operation(B)
        from agent_control_plane.rule_revision import RuleRevision, RuleRevisionRefused, append_rule_revision
        append_rule_revision(bare.f.records, bare.f.rule_revision_profile, RuleRevision(
            revision_id="unsigned", rule_kind="merge_equivalence_rule", rule_ref=RULE, from_digest=None, to_digest=D1, reviser=REQUESTER,
            signer=None, reason="synthetic", recorded_at=bare.NOW.isoformat()))
        with pytest.raises(RuleRevisionRefused):
            append_rule_revision(bare.f.records, bare.f.rule_revision_profile, RuleRevision(
                revision_id="self", rule_kind="merge_equivalence_rule", rule_ref=RULE, from_digest=None, to_digest=D1, reviser=SIGNER,
                signer=SIGNER, reason="synthetic", recorded_at=bare.NOW.isoformat()))
        assert merge(bare, digest=D1).outcome == "unknown" and "no_signed_revision" in document(bare)["merge_records"][-1]["rule_findings"]
        control = build(tmp_path / "control", mp)                                        # (b), (c)
        control.decide_operation(B)
        good = merge(control, digest=D1)
        assert good.outcome == "merged" and good.equivalence_rule_digest == D1 and good.rule_state == "adopted"
        assert good.rule_verified_through == "digest_matches_signed_revision" and document(control)["merge_records"][0]["equivalence_rule_digest"] == D1
        record(record_property, "n4_merge_record_names_rule_digest", text=json.dumps(document(control)["merge_records"][0], indent=2, sort_keys=True))
        import agent_control_plane.merge as merge_module                                 # (d)
        mutant = build(tmp_path / "mutant", mp)
        mutant.decide_operation(B)
        mp.setattr(merge_module, "resolve_rule", lambda *a, **k: {"state": "adopted", "verified_through": "digest_matches_signed_revision", "findings": []})
        folded = merge(mutant, digest=D2)
        assert folded.outcome == "merged", "the mutant lets an unadopted digest fold"
        with pytest.raises(AssertionError):
            assert folded.outcome == "unknown", "leg (b): a digest nobody adopted must not fold"
    finally:
        mp.undo()


# ------------------------------------------------------------------------------------------ rule_change_appends_not_edits
def check_append_only(flow, before_doc, before_rows):
    after = document(flow)
    assert after["rule_revisions"][:len(before_rows)] == before_rows, "an earlier revision row was edited"
    assert json.dumps(after["merge_records"][0], sort_keys=True) == json.dumps(before_doc, sort_keys=True), "an earlier merge row was edited"


def test_rule_change_appends_not_edits(tmp_path, record_property):
    """Legs written out. (a) negative: after a rule change the earlier merge row and every earlier revision row are byte-identical;
    (b) the change is one appended row, and the old digest no longer folds anything; (c) control: the new digest folds;
    (d) mutation: an in-place edit of the earlier merge row is caught by the same check; (e) provenance."""
    PROVENANCE_PROFILE.validate()
    mp = pytest.MonkeyPatch()
    try:
        flow = build(tmp_path / "real", mp)
        flow.decide_operation(B)
        third = flow.add_operation("op-order-100/refund-3", "case-3")
        flow.decide_operation("op-order-100/refund-3")
        assert merge(flow, digest=D1).outcome == "merged"
        merge_row = document(flow)["merge_records"][0]
        rows = document(flow)["rule_revisions"]
        adopt(flow, D2, rid="rule-v2", frm=D1)                                           # the rule changes: one appended row
        check_append_only(flow, merge_row, rows)                                         # (a)
        assert len(document(flow)["rule_revisions"]) == len(rows) + 1 and document(flow)["rule_revisions"][-1]["from_digest"] == D1
        stale = merge(flow, digest=D1, folded=("op-order-100/refund-3",))                # (b)
        assert stale.outcome == "unknown" and "digest_mismatch_with_adopted" in stale.rule_findings
        assert merge(flow, digest=D2, folded=("op-order-100/refund-3",)).outcome == "merged"   # (c)
        check_append_only(flow, merge_row, rows)
        record(record_property, "n4_rule_change_appends", text=json.dumps({"merge_rows": len(document(flow)["merge_records"]),
                                                                          "revision_rows": len(document(flow)["rule_revisions"])}))
        edited = document(flow)                                                          # (d)
        edited["merge_records"][0]["equivalence_rule_digest"] = D2
        flow.f.records.path.write_text(json.dumps(edited, indent=2), encoding="utf-8")
        with pytest.raises(AssertionError):
            check_append_only(flow, merge_row, rows)
    finally:
        mp.undo()


# --------------------------------------------------------------------- merge_after_renewal_names_operation_not_attempt
def test_merge_after_renewal_names_operation_not_attempt(tmp_path, record_property):
    """Composed (N1 rule 2 + L3). A is renewed: r1 is inside the destination (acknowledgement lost, not durable), the grant is
    renewed, r2 commits, r1 lands late and is refused. B applies. The two operations are merged.

    Pass: the merge record references operation ids only (no attempt id and no effect id anywhere in it); the compensation
    obligation lists the effect id of every applied attempt (r2 of A, and B's), equal to the independent ledger read. r1's effect
    id, which never applied, is not listed. Legs written out: (a) the ledger holds exactly two effects before and after the merge;
    (b) as above; (c) control: the same merge without the renewal lists the same two operations' effects; (d) mutation: a merge
    record that carried attempt ids would fail the check; (e) provenance."""
    PROVENANCE_PROFILE.validate()
    mp = pytest.MonkeyPatch()
    try:
        flow = build(tmp_path / "real", mp)
        flow.dest.defer_next_commit()
        r1 = flow.run(flow.d1)                      # r1: unknown, not durable
        assert r1.status == "unknown"
        d2, r2 = flow.renew_and_commit_r2()          # grant renewed; r2 commits
        assert r2.status == "executed"
        with pytest.raises(PermissionError, match="operation_already_committed"):
            flow.dest.land()                         # r1 lands late: refused in the destination's own transaction
        flow.decide_operation(B)
        assert flow.run_operation(B).status == "executed"
        before = flow.ledger_effect_ids()
        assert sorted(before) == sorted([d2.effect_id, flow.decisions[B].effect_id]) and flow.d1.effect_id not in before   # (a)
        row = merge(flow)
        assert row.outcome == "merged"

        def only_operation_ids(merge_row, attempt_ids, effect_ids):
            text = json.dumps(merge_row.model_dump(mode="json"))
            assert not any(x in text for x in attempt_ids), "the merge record names an attempt id"
            assert not any(x in text for x in effect_ids), "the merge record names an effect id"
            assert [merge_row.survivor_operation_id, *merge_row.folded_operation_ids] == [OPERATION, B]
        attempt_ids = {a.attempt_id for a in flow.record().attempts}
        effect_ids = {d2.effect_id, flow.d1.effect_id, flow.decisions[B].effect_id}
        assert len(attempt_ids) == 3, "r1 and r2 of A, and B"
        only_operation_ids(row, attempt_ids, effect_ids)                                 # (b)
        (obligation,) = flow.record().compensation_obligations
        assert sorted(obligation.effect_ids) == sorted(flow.ledger_effect_ids()) == sorted(before)
        assert flow.d1.effect_id not in obligation.effect_ids and obligation.effect_ids_by_operation[OPERATION] == [d2.effect_id]
        assert set(obligation.operation_ids) == {OPERATION, B}
        joins = [j for j in flow.record().attempt_joins if j.operation_id == OPERATION]
        assert {j.grant_revision for j in joins} == {"1", "2"}, "A's attempts span the renewal and join the one operation id"
        record(record_property, "n4_merge_after_renewal", text=json.dumps({"merge": row.model_dump(mode="json"),
                                                                           "obligation": obligation.model_dump(mode="json")}, indent=2, sort_keys=True))
        control = build(tmp_path / "control", mp)                                        # (c)
        run_both(control)
        merge(control)
        assert len(control.record().compensation_obligations[0].effect_ids) == 2
        leaky = row.model_copy(update={"reason": "folded " + next(iter(attempt_ids))})   # (d)
        with pytest.raises(AssertionError):
            only_operation_ids(leaky, attempt_ids, effect_ids)
    finally:
        mp.undo()
