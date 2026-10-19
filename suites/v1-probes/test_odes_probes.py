"""ER-09-2 probes for ODES: structural failure, verifier rejection and local reliance are distinct outcomes.

Packages are built by hand from the pinned conformance vector so each probe breaks exactly one thing, and digests are
recomputed with the pin's own `sha256` so a structural defect is not also an integrity defect. Run against the checkout
named by PROBE_ODES_DIR.
"""
import copy
import json
from pathlib import Path

import pytest

from conftest import pin_dir

NOW = "2026-10-16T00:00:00Z"


def odes():
    pin_dir("PROBE_ODES_DIR")
    import odes.common as common
    import odes.recipient_validator as rv
    return common, rv


def vector():
    p = Path(pin_dir("PROBE_ODES_DIR")) / "conformance" / "test-vectors" / "valid-minimal.example.json"
    return json.loads(p.read_text(encoding="utf-8"))


def seal(package):
    """Recompute both digests so that content integrity is self-consistent."""
    common, _ = odes()
    core = {"record": package["record"], "profile": package["profile"]}
    package["integrity"] = {"kind": "content-digest", "algorithm": "SHA-256",
                            "canonicalization_profile": common.CANONICALIZATION_PROFILE, "value": common.sha256(core)}
    package["package_digest"] = common.sha256({k: package.get(k) for k in ("record", "profile", "integrity", "provenance")})
    return package


def make_package(mutate_record=None):
    common, _ = odes()
    rec = vector()
    rec["verification"]["conformance_profile"] = common.PROFILE_ID
    if mutate_record:
        mutate_record(rec)
    # created_by and created_at are envelope members the recipient validator requires at current ODES; they are outside the
    # package digest and ignored by the frozen pin's validator, so adding them keeps the helper valid at both revisions.
    pkg = {"package_type": common.PACKAGE_TYPE, "package_version": common.PACKAGE_VERSION,
           "created_by": "v1-probes/odes-probe-helper", "created_at": NOW, "record": rec,
           "profile": {"implementation_profile": common.PROFILE_ID, "implementation_profile_version": common.PROFILE_VERSION,
                       "schema_name": common.SCHEMA_NAME, "schema_version": common.SCHEMA_VERSION},
           "provenance": {"source_artifacts": [], "source_record_refs": [], "decision_facts": {}, "execution_facts": {},
                          "redaction": {}, "unsupported_semantics": [], "limits": []}}
    return seal(pkg)


def policy(**over):
    common, _ = odes()
    p = {"now": NOW, "relying_party": "any-authorized-relying-party", "purpose": "reliance-review", "jurisdiction": "unspecified",
         "supported_profiles": [common.PROFILE_ID], "evaluation_scope": "audit", "status_max_age_seconds": 300,
         "allow_unauthenticated_informational_inspection": True}
    p.update(over)
    return p


def evaluate(pkg, pol=None):
    _, rv = odes()
    return rv.evaluate_recipient_package(pkg, pol if pol is not None else policy())


def failing(result):
    return {k for k, v in result.items() if isinstance(v, dict) and v["status"] != "pass"}


def test_probe_odes_control_intact_package_passes_every_layer_except_issuer_authentication():
    r = evaluate(make_package())
    assert failing(r) - {"recipient_reliance_decision"} <= {"integrity_authentication_checks", "historical_authority_assertions", "authority_status_and_freshness"}
    for layer in ("schema_validity", "declared_profile_conformance", "package_content_integrity", "consumption_conditions"):
        assert r[layer]["status"] == "pass", (layer, r[layer]["reasons"])
    assert r["recipient_reliance_decision"]["status"] != "pass"  # unauthenticated content is never relied upon


def test_probe_odes_structural_failure_is_reported_by_schema_layer_only_not_as_verifier_rejection_or_reliance_policy():
    def drop(rec):
        del rec["decision_id"]
    r = evaluate(make_package(drop))
    assert r["schema_validity"]["status"] == "fail" and any("decision_id" in x for x in r["schema_validity"]["reasons"])
    assert r["package_content_integrity"]["status"] == "pass"  # digests were recomputed: not an integrity rejection
    assert r["declared_profile_conformance"]["status"] == "pass"
    assert r["consumption_conditions"]["status"] == "pass"  # not a recipient-policy refusal
    assert r["recipient_reliance_decision"]["status"] == "fail"
    assert "schema_validity" in r["recipient_reliance_decision"]["reasons"][0]
    assert "consumption_conditions" not in r["recipient_reliance_decision"]["reasons"][0]


def test_probe_odes_non_object_input_is_structural_not_evaluated_and_fails_reliance():
    _, rv = odes()
    for bad in ([], "x", None, {"package_type": "wrong"}):
        r = rv.evaluate_recipient_package(bad, {})
        assert r["schema_validity"]["status"] == "not_evaluated"
        assert r["recipient_reliance_decision"]["status"] == "fail"


def test_probe_odes_verifier_rejection_tampered_content_fails_integrity_while_schema_still_passes():
    pkg = make_package()
    pkg["record"]["decision_type"] = "tampered_after_sealing"  # schema-valid change, digests not recomputed
    r = evaluate(pkg)
    assert r["schema_validity"]["status"] == "pass"
    assert r["package_content_integrity"]["status"] == "fail"
    assert r["consumption_conditions"]["status"] == "pass"
    assert "package_content_integrity" in r["recipient_reliance_decision"]["reasons"][0]
    assert "schema_validity" not in r["recipient_reliance_decision"]["reasons"][0]


def test_probe_odes_verifier_rejection_unsupported_profile_is_unsupported_not_fail_and_not_schema():
    common, _ = odes()
    pkg = make_package()
    pkg["profile"]["implementation_profile_version"] = "odes-cognous-stack-export-9.9.9"
    seal(pkg)
    r = evaluate(pkg)
    assert r["declared_profile_conformance"]["status"] == "unsupported"
    assert r["schema_validity"]["status"] == "pass" and r["package_content_integrity"]["status"] == "pass"
    assert r["recipient_reliance_decision"]["status"] == "fail"


def test_probe_odes_local_reliance_refusal_is_a_recipient_policy_outcome_over_a_valid_verified_package():
    pkg = make_package()
    r = evaluate(pkg, policy(relying_party="some-other-party"))
    assert r["schema_validity"]["status"] == "pass"
    assert r["package_content_integrity"]["status"] == "pass"
    assert r["declared_profile_conformance"]["status"] == "pass"
    assert r["consumption_conditions"]["status"] == "fail"
    assert "consumption_conditions" in r["recipient_reliance_decision"]["reasons"][0]
    assert "schema_validity" not in r["recipient_reliance_decision"]["reasons"][0]
    assert "package_content_integrity" not in r["recipient_reliance_decision"]["reasons"][0]
    # the package itself is unchanged: the same bytes are acceptable to a recipient whose policy permits them
    ok = evaluate(pkg, policy())
    assert ok["consumption_conditions"]["status"] == "pass"


def test_probe_odes_three_failure_classes_have_disjoint_layer_signatures_and_distinct_reliance_reasons():
    def drop(rec):
        del rec["decision_id"]
    structural = evaluate(make_package(drop))
    tampered = make_package(); tampered["record"]["decision_type"] = "tampered"
    rejection = evaluate(tampered)
    reliance = evaluate(make_package(), policy(purpose="not-permitted"))
    core = {"schema_validity", "package_content_integrity", "consumption_conditions"}
    sig = [failing(x) & core for x in (structural, rejection, reliance)]
    assert sig == [{"schema_validity"}, {"package_content_integrity"}, {"consumption_conditions"}]
    reasons = {x["recipient_reliance_decision"]["reasons"][0] for x in (structural, rejection, reliance)}
    assert len(reasons) == 3


def status_for(rec):
    return {"issuer": rec["issuer"], "record_id": rec["decision_id"], "authority_basis": rec["authority"]["authority_basis"],
            "evaluation_scope": "audit", "evaluated_at": "2026-10-15T23:59:00Z", "evidence_freshness": "current",
            "freshness": "current", "revoked": False, "superseded": False, "authority_valid_at_decision_verified": True}


def test_probe_odes_informational_inspection_is_not_reliance_and_never_rescues_a_structural_or_integrity_failure():
    pkg = make_package()
    rec = pkg["record"]
    pol = policy(status_inputs=status_for(rec), trusted_issuer=rec["issuer"])
    r = evaluate(pkg, pol)
    assert failing(r) - {"recipient_reliance_decision"} == {"integrity_authentication_checks"}, failing(r)
    assert r["recipient_reliance_decision"]["status"] == "informational_only"  # reachable, and not "pass"
    off = evaluate(pkg, dict(pol, allow_unauthenticated_informational_inspection=False))
    assert off["recipient_reliance_decision"]["status"] == "fail"
    def drop(x):
        del x["decision_id"]
    bad = make_package(drop)
    assert evaluate(bad, dict(pol, status_inputs=status_for(vector())))["recipient_reliance_decision"]["status"] == "fail"
    tampered = make_package(); tampered["record"]["decision_type"] = "tampered"
    assert evaluate(tampered, pol)["recipient_reliance_decision"]["status"] == "fail"
