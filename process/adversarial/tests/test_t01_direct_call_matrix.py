"""T01. Direct-call matrix over every destination class (idea D25, tier 1).

SPDX-License-Identifier: Apache-2.0

Attacker: a holder of a destination object who calls its public write methods directly, without the control plane.
Invariant: on every destination class that claims to enforce authority, no effect row appears without a valid authority row
(effective-grant row with matching digest, or an issued claim against an active grant); a class that holds no authority state
accepts the call by design and is LISTED as 'not applicable', never hidden.
Observed state: the effects table, read through an independent read-only connection.

Does not prove: raw SQL by the database-file holder (out of model: the file holder can write any row); live OpenShell; any
destination class added after runtime 11de097c; the control plane's own JSON destination beyond the one base-class row below.
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from _adv import atomic, effect_ids, flow, snapshot
from conftest import observe

T = "T01"
DNP = "raw SQL by the file holder and classes added after runtime 11de097c are out of model"

# Classes that hold no authority state: they accept a direct call by design (SCN-D09 table); listed, not hidden.
NON_ENFORCING = [
    ("engine.safe_executor", "DurableRefundDestination"),
    ("engine.operation_identity_destination", "OperationIdentityDestination"),
    ("engine.delayed_commit_destination", "DelayedCommitDestination"),
    ("engine.delayed_commit_destination", "DelayedOperationIdentityDestination"),
    ("engine.dedupe_destination", "DedupeTtlOperationDestination"),
]
EFFECTIVE_GRANT = [
    ("engine.effective_grant", "EffectiveGrantDestination"),
    ("engine.operation_identity_destination", "OperationIdentityEffectiveGrantDestination"),
    ("engine.delayed_commit_destination", "DelayedEffectiveGrantDestination"),
    ("engine.delayed_commit_destination", "DelayedOperationIdentityEffectiveGrantDestination"),
]


def _cls(mod, name):
    import importlib
    return getattr(importlib.import_module(mod), name)


def _snap(fl):
    return snapshot(fl.envelope(fl.d1))


@pytest.mark.parametrize("mod,name", NON_ENFORCING, ids=[n for _, n in NON_ENFORCING])
def test_non_enforcing_class_accepts_direct_commit_and_is_listed(cprt, tmp_path, monkeypatch, mod, name):
    """Listed by design: a direct commit with no grant writes one row (this class holds no authority state)."""
    fl = flow(tmp_path, monkeypatch)
    dest = _cls(mod, name)(tmp_path / "d")
    dest.commit(_snap(fl))
    assert effect_ids(dest.path) == [fl.d1.effect_id]
    observe(T, f"{name}: direct commit, no grant", "not applicable",
            does_not_prove="this class is not an authority boundary; the control plane is (SCN-D09)", detail="row written by design")


def test_control_plane_json_destination_accepts_direct_apply_and_is_listed(cprt, tmp_path, monkeypatch):
    """The control plane's own LocalRefundDestination holds no grant state either: listed."""
    import agent_control_plane.bounded as cp
    dest = cp.LocalRefundDestination(tmp_path / "cp-dest.json")
    dest.apply(effect_id="sha256:" + "0" * 64, grant_id="no-such-grant", max_effects=1, target="urn:x", amount=1, unit="USD",
               payload={})
    assert list(dest.snapshot()["effects"]) == ["sha256:" + "0" * 64]
    observe(T, "control plane LocalRefundDestination: direct apply", "not applicable",
            does_not_prove="the control plane workflow is the boundary for this destination", detail="row written by design")


@pytest.mark.parametrize("mod,name", EFFECTIVE_GRANT, ids=[n for _, n in EFFECTIVE_GRANT])
def test_effective_grant_classes_refuse_direct_commit_without_valid_grant(cprt, tmp_path, monkeypatch, mod, name):
    from engine.effective_grant import DERIVATION
    fl = flow(tmp_path, monkeypatch)
    snap = _snap(fl)
    grant = fl.r.contexts[fl.PROFILE]["grant"]
    perms = list(fl.p.requested_permissions)
    outcomes = {}

    def attempt(label, dest, **kw):
        try:
            dest.commit(snap, **kw)
            outcomes[label] = "committed"
        except PermissionError as exc:
            outcomes[label] = str(exc)
        assert effect_ids(dest.path) == [], f"{name}/{label}: an effect row appeared without valid authority"

    # 1 no grant row, no digest
    d = _cls(mod, name)(tmp_path / "no-grant")
    attempt("no_grant_no_digest", d)
    # 2 no grant row, a well-formed digest the caller computed itself
    from engine.effective_grant import effective_grant_digest
    forged = effective_grant_digest(principal=fl.p.principal, grant_id=grant["grant_id"], revision=grant["revision"],
                                    permissions=perms, status="active")
    attempt("no_grant_self_computed_digest", d, expected_effective_grant_digest=forged, effective_grant_derivation_version=DERIVATION)
    # 3 revoked grant, caller presents the digest it read while active
    d = _cls(mod, name)(tmp_path / "revoked")
    active = d.set_effective_grant(principal=fl.p.principal, grant_id=grant["grant_id"], revision=grant["revision"], permissions=perms)
    d.set_effective_grant(principal=fl.p.principal, grant_id=grant["grant_id"], revision=grant["revision"], permissions=perms,
                          status="revoked")
    attempt("revoked_stale_digest", d, expected_effective_grant_digest=active, effective_grant_derivation_version=DERIVATION)
    # 4 revoked grant, caller presents the digest of the revoked row
    revoked = effective_grant_digest(principal=fl.p.principal, grant_id=grant["grant_id"], revision=grant["revision"],
                                     permissions=perms, status="revoked")
    attempt("revoked_current_digest", d, expected_effective_grant_digest=revoked, effective_grant_derivation_version=DERIVATION)
    # 5 wrong principal (the effective-grant row has no tenant column; principal is its subject binding)
    d = _cls(mod, name)(tmp_path / "wrong-principal")
    other = d.set_effective_grant(principal="urn:cognous:principal:other", grant_id=grant["grant_id"], revision=grant["revision"],
                                  permissions=perms)
    attempt("wrong_principal", d, expected_effective_grant_digest=other, effective_grant_derivation_version=DERIVATION)
    # 6 permissions narrowed after the digest was read
    d = _cls(mod, name)(tmp_path / "narrowed")
    d.set_effective_grant(principal=fl.p.principal, grant_id=grant["grant_id"], revision=grant["revision"], permissions=["other"])
    wide = effective_grant_digest(principal=fl.p.principal, grant_id=grant["grant_id"], revision=grant["revision"],
                                  permissions=perms, status="active")
    attempt("narrowed_permissions", d, expected_effective_grant_digest=wide, effective_grant_derivation_version=DERIVATION)
    assert "committed" not in outcomes.values(), outcomes
    # positive control: valid row and digest -> exactly one row
    d = _cls(mod, name)(tmp_path / "valid")
    ok = d.set_effective_grant(principal=fl.p.principal, grant_id=grant["grant_id"], revision=grant["revision"], permissions=perms)
    d.commit(snap, expected_effective_grant_digest=ok, effective_grant_derivation_version=DERIVATION)
    d.commit(snap, expected_effective_grant_digest=ok, effective_grant_derivation_version=DERIVATION)  # replay: dedupe
    assert effect_ids(d.path) == [fl.d1.effect_id]
    observe(T, f"{name}: direct commit without valid grant (6 cases)", "prevented", does_not_prove=DNP + "; the effective-grant "
            "row has no expiry or tenant column, so 'expired' and 'wrong tenant' are not expressible here", detail=outcomes)


def test_atomic_classes_refuse_direct_calls_without_valid_claim(cprt, tmp_path, monkeypatch):
    for key in (False, True):
        name = "OperationIdentityAtomicAuthorityEffectDestination" if key else "AtomicAuthorityEffectDestination"
        work = tmp_path / name
        fl = flow(work, monkeypatch)
        dest, ex = atomic(fl, work, identity_key=key)
        snap = _snap(fl)
        outcomes = {}

        def attempt(label, call):
            try:
                call()
                outcomes[label] = "committed"
            except PermissionError as exc:
                outcomes[label] = str(exc)
            assert effect_ids(dest.path) == [], f"{name}/{label}: an effect row appeared without a valid claim"

        attempt("legacy_commit_method", lambda: dest.commit(snap))
        attempt("no_claim", lambda: dest.execute_claim_atomic("no-such-claim", snap, attempt_id="a-1"))
        claim = ex.provision_claim(proposal=fl.p, decision=fl.d1, now=fl.NOW)
        grant_id = fl.d1.binding.grant_id
        # suspension is reversible; the grant is restored to active before the next case
        dest.set_grant_status(grant_id, status="suspended")
        attempt("suspended_grant", lambda: dest.execute_claim_atomic(claim.claim_id, snap, attempt_id="a-3"))
        dest.set_grant_status(grant_id, status="active")
        saved = dest.clock
        dest.clock = lambda: fl.NOW + timedelta(days=3650)
        attempt("expired_claim_and_grant", lambda: dest.execute_claim_atomic(claim.claim_id, snap, attempt_id="a-4"))
        dest.clock = saved
        import dataclasses
        wrong_tenant = dataclasses.replace(snap, operation=dataclasses.replace(snap.operation, tenant_id="tenant-other"))
        attempt("wrong_tenant_snapshot", lambda: dest.execute_claim_atomic(claim.claim_id, wrong_tenant, attempt_id="a-5"))
        # revocation is final for the revision: the claim is refused, and so is every attempt to put the revision back
        dest.set_grant_status(grant_id, status="revoked")
        attempt("revoked_grant", lambda: dest.execute_claim_atomic(claim.claim_id, snap, attempt_id="a-2"))
        for back in ("suspended", "active"):
            attempt(f"revoked_then_{back}_same_revision", lambda back=back: dest.set_grant_status(grant_id, status=back))
            assert outcomes[f"revoked_then_{back}_same_revision"] != "committed", "a revoked revision was set back (no PermissionError)"
            attempt(f"revoked_claim_after_{back}_attempt", lambda: dest.execute_claim_atomic(claim.claim_id, snap, attempt_id="a-6"))
        assert "committed" not in outcomes.values(), outcomes
        # legitimate path: a successor revision; the claim bound to the revoked revision stays refused
        dest.set_grant_status(grant_id, status="active", revision="successor-revision")
        attempt("revoked_revision_claim_after_successor", lambda: dest.execute_claim_atomic(claim.claim_id, snap, attempt_id="a-7"))
        assert "committed" not in outcomes.values(), outcomes
        # positive control on a fresh store: the issued claim with an active grant commits exactly one row; a second call does not add one
        cwork = tmp_path / (name + "-control")
        cfl = flow(cwork, monkeypatch)
        cdest, cex = atomic(cfl, cwork, identity_key=key)
        cclaim = cex.provision_claim(proposal=cfl.p, decision=cfl.d1, now=cfl.NOW)
        cdest.execute_claim_atomic(cclaim.claim_id, _snap(cfl), attempt_id="a-ok")
        with pytest.raises(PermissionError):
            cdest.execute_claim_atomic(cclaim.claim_id, _snap(cfl), attempt_id="a-again")
        assert effect_ids(cdest.path) == [cfl.d1.effect_id]
        observe(T, f"{name}: direct calls without valid claim (9 cases)", "prevented", does_not_prove=DNP, detail=outcomes)
