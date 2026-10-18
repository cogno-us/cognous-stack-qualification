"""N2 probes: rule-revision/0.1 (opt-in) at the Control Plane. Engineering addendum 101726_B, item N2 (L2, M2, M4).

Run against the checkout named by PROBE_CONTROL_PLANE_DIR (Linux only). Each probe follows the shape of the N4 refusal-test
template (suites/_refusal_template.py, legs a-e), using its Provenance and RefusalTemplateFailure types:
  (a) negative assertion   the bad state is refused/unknown/flagged;
  (b) refusal row          the refusal is retained as a row (decision row, refusal-row list or flag row), not only an exception;
  (c) positive control     the same flow with the defect removed passes, so the refusal is not a harness artefact;
  (d) mutation check       with the control disabled the negative assertion FAILS (a surviving mutation raises leg d);
  (e) provenance label     PROVENANCE below is validated for every probe.
The template's RouteAAdapter is not used: N2 refusals are decision-time holds and pure report functions inside the control
plane alone, with no destination ledger. The legs are asserted directly against the pinned control plane.

What this proves: the pinned component resolves an unadopted rule digest to `unknown` and flags the listed conditions.
What it does not prove: tamper evidence. A holder of the record-store key can rewrite rows; this is visibility to an honest
reader. Trust moves to the configured revision signer.
A pin that lacks `agent_control_plane.rule_revision` FAILS these probes (the primitive is absent); that is a finding, not a skip.
"""
import sys
from datetime import timedelta
from pathlib import Path

import pytest

from conftest import pin_dir

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import _refusal_template as T  # noqa: E402

# Leg (e): "expected today" is a code reading of the N2 control-plane change (not a run); registry counts are tracker #42's code check.
PROVENANCE = T.Provenance('code-reading', 'cogno-us/cognous-control-plane PR n2/rule-revision: rule_revision.py (resolve_rule, '
                          'append_rule_revision), reason_vocabulary.py (refusal_trends, measured_arity, recomputability_flags); '
                          'synthetic fixtures, no production claim; registry counts per cognous-control-plane#42')
REVISER, SIGNER = "synthetic-principal:reviser", "synthetic-principal:signer"


@pytest.fixture(autouse=True)
def _pin(monkeypatch):
    PROVENANCE.validate()
    pin_dir("PROBE_CONTROL_PLANE_DIR")
    import agent_control_plane.bounded as bounded
    from tests.test_runtime_authority import NOW
    monkeypatch.setattr(bounded, "_now", lambda: NOW)
    try:
        import agent_control_plane.rule_revision  # noqa: F401
    except ImportError:
        pytest.fail("pinned control plane has no agent_control_plane.rule_revision (rule-revision/0.1 absent)")


def mods():
    import agent_control_plane.reason_vocabulary as rv
    import agent_control_plane.rule_revision as rr
    import tests.test_bounded_authorization as ba
    import tests.test_runtime_authority as ra
    return rv, rr, ba, ra


def digest(label):
    from agent_control_plane.bounded import commitment
    return commitment({"synthetic-policy-content": label})


def revision(rid, to, frm=None, *, signer=SIGNER, ref=None, kind="policy", supersedes=None, **kw):
    rv, rr, ba, ra = mods()
    return rr.RuleRevision(revision_id=rid, rule_kind=kind, rule_ref=ref or ba.POLICY_REF, from_digest=frm, to_digest=to,
                           reviser=REVISER, signer=signer, authority_ref="synthetic-authority:1", reason="synthetic",
                           supersedes=supersedes, recorded_at=ra.NOW.isoformat(), **kw)


def flow(tmp_path, content="v1"):
    rv, rr, ba, ra = mods()
    p, r, f, c = ra.setup_flow(tmp_path)
    f.rule_revision_profile = rr.RuleRevisionProfile(signers=[SIGNER])
    r.policies[ba.POLICY_REF].digest = digest(content)
    return p, r, f


def adopt(f, rid="r1", content="v1", **kw):
    mods()[1].append_rule_revision(f.records, f.rule_revision_profile, revision(rid, digest(content), **kw))


def disable(mp, name, value):
    """Mutation: disable one control in the pinned component (undone when the context exits)."""
    import agent_control_plane.bounded as bounded
    import agent_control_plane.reason_vocabulary as rv
    mp.setattr(bounded if hasattr(bounded, name) else rv, name, value)


def always_adopted(profile, revisions, rule_ref, observed):
    return {"rule_ref": rule_ref, "state": "adopted", "observed_digest": observed, "adopted_digest": observed,
            "verified_through": "digest_matches_signed_revision", "findings": []}


def must_fail_when_disabled(negative, tmp_path, monkeypatch, name, value):
    with pytest.MonkeyPatch.context() as mp:
        disable(mp, name, value)
        try:
            negative(tmp_path / "mutated")
        except AssertionError:
            return
    raise T.RefusalTemplateFailure('d', f'mutation survived: with {name} disabled the negative assertion still passed')


# ---------------------------------------------------------------------------------------------------------------- M2 / L2
def test_probe_n2_unsigned_policy_revision_treated_unknown(tmp_path, monkeypatch):
    rv, rr, ba, ra = mods()

    def negative(tp):
        p, r, f = flow(tp)
        adopt(f, signer=None)
        d = f.decide(p, now=ra.NOW)
        assert d.result == "hold" and "policy_status_unknown" in d.reasons, d.reasons
        return f, d
    f, d = negative(tmp_path / "neg")
    assert d.rule_identity["unknown"] == [ba.POLICY_REF]  # refusal row: the decision row names the unknown rule and the level reached
    assert d.rule_identity["rules"][ba.POLICY_REF]["verified_through"] == "revision_row_present"
    assert f.records.load().decisions[-1].rule_identity == d.rule_identity and not f.records.load().attempts
    p, r, f2 = flow(tmp_path / "pos")  # positive control: same flow, signed row
    adopt(f2)
    assert f2.decide(p, now=ra.NOW).result == "authorized"
    must_fail_when_disabled(negative, tmp_path, monkeypatch, "resolve_rule", always_adopted)


def test_probe_n2_self_signed_policy_revision_refused(tmp_path, monkeypatch):
    rv, rr, ba, ra = mods()

    def negative(tp):
        p, r, f = flow(tp)
        refused = None
        try:
            rr.append_rule_revision(f.records, f.rule_revision_profile, revision("r1", digest("v1"), signer=REVISER))
        except rr.RuleRevisionRefused as e:
            refused = e
        assert refused is not None and "self_signed_revision_row" in refused.reasons, "self-signed revision was not refused"
        return f
    f = negative(tmp_path / "neg")
    doc = f.records.load()
    assert doc.rule_revisions == [] and doc.rule_revision_refusals[0].reasons == ["self_signed_revision_row"]  # refusal row
    p, r, f2 = flow(tmp_path / "pos")
    adopt(f2)  # positive control: an independent configured signer is accepted
    assert [x.signer for x in f2.records.load().rule_revisions] == [SIGNER]

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(rr, "revision_defects", lambda profile, row: [])  # mutation: no signer checks
        try:
            negative(tmp_path / "mutated")
        except AssertionError:
            return
    raise T.RefusalTemplateFailure('d', 'mutation survived: with revision_defects disabled the self-signed row was still refused')


def test_probe_n2_signed_revision_reissued_grant_passes(tmp_path, monkeypatch):
    rv, rr, ba, ra = mods()
    p, r, f = flow(tmp_path)
    adopt(f)
    d = f.decide(p, now=ra.NOW)
    assert d.result == "authorized", d.reasons
    ident = d.rule_identity["rules"][ba.POLICY_REF]
    assert ident["digest"] == digest("v1") and ident["verified_through"] == "digest_matches_signed_revision"
    # reissue against a new policy revision: unsigned -> unknown (negative), signed -> passes (positive control)
    r.policies[ba.POLICY_REF].digest = digest("v2")
    held = f.decide(p, now=ra.NOW)
    assert held.result == "hold" and "policy_status_unknown" in held.reasons
    adopt(f, "r2", "v2", frm=digest("v1"))
    assert f.decide(p, now=ra.NOW).result == "authorized"
    # mutation: an unsigned row must not pass; make the unsigned row count and the negative above would be wrong
    p2, r2, f2 = flow(tmp_path / "m")
    adopt(f2, signer=None)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(rr, "revision_defects", lambda profile, row: [])
        assert f2.decide(p2, now=ra.NOW).result == "authorized"  # control off: the unsigned row passes, so the control is load-bearing


def test_probe_n2_policy_edited_in_place_detected_by_digest(tmp_path, monkeypatch):
    rv, rr, ba, ra = mods()

    def negative(tp):
        p, r, f = flow(tp)
        adopt(f)
        assert f.decide(p, now=ra.NOW).result == "authorized"
        r.policies[ba.POLICY_REF].digest = digest("v1-edited")  # version label unchanged
        d = f.decide(p, now=ra.NOW)
        assert d.result == "hold" and "policy_status_unknown" in d.reasons and "policy_version_changed" not in d.reasons, d.reasons
        return d
    d = negative(tmp_path / "neg")
    ident = d.rule_identity["rules"][ba.POLICY_REF]  # refusal row retains the digests, not only the version
    assert ident["digest"] == digest("v1-edited") and "digest_mismatch_with_adopted" in ident["findings"]
    p, r, f = flow(tmp_path / "pos")
    adopt(f)
    assert f.decide(p, now=ra.NOW).rule_identity["rules"][ba.POLICY_REF]["state"] == "adopted"  # positive control
    must_fail_when_disabled(negative, tmp_path, monkeypatch, "resolve_rule", always_adopted)


def test_probe_n2_policy_edit_without_revision_row_resolves_unknown_and_flags_digest_mismatch(tmp_path, monkeypatch):
    """Composed: M2 (no signed revision -> unknown) and L2 (digest mismatch flagged) on one edit."""
    rv, rr, ba, ra = mods()

    def negative(tp):
        p, r, f = flow(tp)
        adopt(f)
        r.policies[ba.POLICY_REF].digest = digest("edited")
        d = f.decide(p, now=ra.NOW)
        assert d.result == "hold" and "policy_status_unknown" in d.reasons, d.reasons
        ident = d.rule_identity["rules"][ba.POLICY_REF]
        assert ident["state"] == "unknown" and "digest_mismatch_with_adopted" in ident["findings"], ident
        return f, p, r
    f, p, r = negative(tmp_path / "neg")
    assert f.records.load().decisions[-1].rule_identity["unknown"] == [ba.POLICY_REF]  # refusal row
    adopt(f, "r2", "edited", frm=digest("v1"))  # positive control: append a signed row for the new digest
    assert f.decide(p, now=ra.NOW).result == "authorized"
    must_fail_when_disabled(negative, tmp_path, monkeypatch, "resolve_rule", always_adopted)


# ---------------------------------------------------------------------------------------------------------------- L2 trends
def adoption_change(rv, at):
    return rv.VocabularyChange(change_id="c1", previous_version="v1", version="v2", registry_digest=digest("registry"), kind="split",
                               previous_codes=["old"], codes=["new_a", "new_b"], acknowledged_by=SIGNER, acknowledged_at=at)


def test_probe_n2_row_version_predates_adoption_flagged(tmp_path, monkeypatch):
    rv, rr, ba, ra = mods()
    early, late = (ra.NOW - timedelta(days=1)).isoformat(), ra.NOW.isoformat()

    def negative(_tp):
        rep = rv.refusal_trends([], [{"reason_vocabulary_version": "v2", "reasons": ["new_a"], "recorded_at": early}],
                                previous_exposure=0, current_exposure=1, vocabulary_changes=[adoption_change(rv, late)])
        assert rep.get("flagged_row_count") == 1 and rep["rows_predating_adoption"][0]["version"] == "v2", rep
        return rep
    rep = negative(None)
    assert rep["rows_predating_adoption"][0]["adoption_time"] == late  # the flag row names both times
    ok = rv.refusal_trends([], [{"reason_vocabulary_version": "v2", "reasons": ["new_a"], "recorded_at": late}],
                           previous_exposure=0, current_exposure=1, vocabulary_changes=[adoption_change(rv, late)])
    assert ok["flagged_row_count"] == 0  # positive control: a row at or after adoption is not flagged
    must_fail_when_disabled(negative, tmp_path, monkeypatch, "_annotate_adoption", lambda *a, **k: None)


def test_probe_n2_pre_split_counts_tainted(tmp_path, monkeypatch):
    rv, rr, ba, ra = mods()
    at = ra.NOW.isoformat()
    prior = [{"reason_vocabulary_version": "v1", "reasons": ["old"], "recorded_at": (ra.NOW - timedelta(days=1)).isoformat()}] * 5

    def negative(_tp):
        rep = rv.refusal_trends(prior, [], previous_exposure=10, current_exposure=10, vocabulary_changes=[adoption_change(rv, at)])
        series = {(s["version"], s["code"]): s for s in rep["series"]}
        assert series[("v1", "old")].get("tainted_for_trend") is True, series
        return series
    series = negative(None)
    assert series[("v1", "old")]["taint_reasons"] == ["pre_split_count"]
    plain = rv.refusal_trends(prior, [], previous_exposure=10, current_exposure=10)  # positive control: no split recorded
    assert all("tainted_for_trend" not in s for s in plain["series"])
    other = rv.refusal_trends(prior, [], previous_exposure=10, current_exposure=10,
                              vocabulary_changes=[rv.VocabularyChange(change_id="c2", previous_version="v1", version="v2",
                                                                      registry_digest=digest("r"), kind="addition", previous_codes=["old"],
                                                                      codes=["old", "x"], acknowledged_by=SIGNER, acknowledged_at=at)])
    assert not other["series"][0]["tainted_for_trend"]  # only a split taints
    must_fail_when_disabled(negative, tmp_path, monkeypatch, "_annotate_adoption", lambda *a, **k: None)


# ---------------------------------------------------------------------------------------------------------------- L2 arity / recomputability
def _arity_row(ra, code, types):
    return {"reasons": [code], "recorded_at": ra.NOW.isoformat(),
            "resolution_inputs": [{"input_type": t, "input_id": t, "missing": True} for t in types]}


def test_probe_n2_reused_code_raises_measured_arity(tmp_path, monkeypatch):
    rv, rr, ba, ra = mods()
    code = "policy_stale_or_changed"
    rows = [_arity_row(ra, code, ["policy"]), _arity_row(ra, code, ["grant", "policy"])]

    def negative(_tp):
        m = rv.measured_arity(rows, as_of=ra.NOW.isoformat(), period_seconds=60)
        flags = rv.arity_flags({code: 1}, m)  # declared at signing: one operand shape
        assert m["codes"][code]["measured"] == 2 and flags and flags[0]["flag"] == "measured_exceeds_declared", (m, flags)
        return m, flags
    m, flags = negative(None)
    assert m["as_of"] == ra.NOW.isoformat() and flags[0]["declared"] == 1 and flags[0]["measured"] == 2  # both values retained
    m1 = rv.measured_arity(rows[:1], as_of=ra.NOW.isoformat(), period_seconds=60)
    assert rv.arity_flags({code: 1}, m1) == []  # positive control: one shape matches the declaration
    must_fail_when_disabled(negative, tmp_path, monkeypatch, "arity_flags", lambda declared, measured: [])


def test_probe_n2_declared_recomputable_without_operands_is_derivation_unavailable(tmp_path, monkeypatch):
    rv, rr, ba, ra = mods()
    import json
    from pathlib import Path
    import agent_control_plane
    registry = json.loads((Path(agent_control_plane.__file__).resolve().parents[2] / "schemas" / "runtime_authority_reasons_0_2.json").read_text())
    kinds = [v["reason_kind"] for v in registry["codes"].values()]
    # tracker #42 code check: exactly one recomputable code. Registry 0.2 is the 158-code superset (0.1 stays the original 121; 157 at control plane 3755c71a, 158 from the terminal-revocation code added at 6b8fb627)
    assert kinds.count("recomputable") == 1 and kinds.count("typed_only") == len(kinds) - 1 and len(kinds) == 158
    bare = {"reasons": ["grant_revoked"], "resolution_inputs": []}

    def negative(_tp):
        flags = rv.recomputability_flags([bare], registry["codes"])
        assert flags and flags[0]["flag"] == "derivation_unavailable" and flags[0]["derived"] == "underivable", flags  # N2b
        return flags
    flags = negative(None)
    assert flags[0]["declared"] == "recomputable" and flags[0]["code"] == "grant_revoked"  # declared stays as the expectation
    full = {"reasons": ["grant_revoked"], "resolution_inputs": [
        {"input_type": "grant", "input_id": "g", "observed": {"status": "revoked"}, "record_commitment": digest("g")}]}
    assert rv.recomputability_flags([full], registry["codes"]) == []  # positive control: operands present, declared == derived
    mismatch = {"reasons": ["grant_revoked"], "resolution_inputs": [  # operands present and they show the declared kind cannot hold
        {"input_type": "grant", "input_id": "g", "observed": {"status": "active"}, "expected": {"status": "active"},
         "record_commitment": digest("g")}]}
    over = rv.recomputability_flags([mismatch], registry["codes"])
    assert over and over[0]["flag"] == "declared_overclaim" and over[0]["derived"] == "typed_only", over  # N2b: overclaim stays reachable
    must_fail_when_disabled(negative, tmp_path, monkeypatch, "derive_recomputability", lambda row: "recomputable")
