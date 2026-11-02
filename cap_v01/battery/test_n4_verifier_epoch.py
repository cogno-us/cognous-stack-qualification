"""N4: unavailable or substituted verifier, and a missing epoch floor. A verifier that is None, a subclass, a stub or a look-alike is `verifier_unavailable` and the Registry core is never
entered; a caller cannot inject `selection_source` or `verifier` through the factory; an unimportable Registry is `verifier_unavailable`; a snapshot without a per-selection floor
is `epoch_floor_missing` even when everything else admits. Refusals leave every file unchanged."""
import importlib

import pytest

import harness as H
from harness import AP, Source, build, expect_refusal, make_kit, material, refused_build, snapshot_doc, snapshot_files, spy  # noqa: F401


class AcceptAnything:
    """A caller-injected STUB verifier: not the Registry adapter, accepts everything. Must never be consulted."""

    def __init__(self):
        self.calls = 0

    def __getattr__(self, name):
        def any_method(*a, **k):
            self.calls += 1
            return True
        return any_method


class SubclassedVerifier(H.ev.Ed25519Verifier):
    """A SUBCLASS of the real verifier that approves every key. Must be refused by exact-type check, never consulted."""
    checks = 0

    def key_admission(self, alg, public_key):
        type(self).checks += 1
        return True

    def acceptable_public_key(self, public_key):
        type(self).checks += 1
        return True


def direct_source(kit, verifier, host=None):
    profile = kit.load(digest=kit.digest)
    return AP.PinnedSelectionSource(profile, host if host is not None else Source(material()), verifier, expected_mode="synthetic", expected_config_digest=kit.digest)


@pytest.mark.parametrize("label,make", [
    ("none", lambda: None),
    ("subclass_that_approves_everything", lambda: SubclassedVerifier()),
    ("stub_accepts_anything", lambda: AcceptAnything()),
    ("class_not_instance", lambda: H.ev.Ed25519Verifier),
    ("plain_object", lambda: object()),
    ("string", lambda: "Ed25519Verifier"),
    ("registry_evidence_adapter", lambda: (lambda ad: H.RegistryEvidenceVerifierV2(ad, ad.key_admission))(H.ev.Ed25519Verifier())),
])
@pytest.mark.row("N4.a", "the selection source is given a verifier that is None / a subclass / a stub / a look-alike: verifier_unavailable, the host source is not read, the Registry core is never entered, the stub is never consulted, last_refusal is typed")
def test_non_exact_verifier_is_unavailable_and_never_consulted(tmp_path, spy, label, make):
    kit = make_kit(tmp_path)
    verifier = make()
    host = Source(material())
    wrapper = direct_source(kit, verifier, host)
    SubclassedVerifier.checks = 0
    before = snapshot_files(tmp_path)
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        wrapper()
    assert exc.value.code == "verifier_unavailable"
    assert wrapper.last_refusal.code == "verifier_unavailable"
    assert host.calls == 0 and not spy.reached and spy.crypto == 0 and SubclassedVerifier.checks == 0
    if isinstance(verifier, AcceptAnything):
        assert verifier.calls == 0
    assert snapshot_files(tmp_path) == before


@pytest.mark.parametrize("kwarg,make", [
    ("verifier", lambda: H.ev.Ed25519Verifier()),
    ("verifier", lambda: AcceptAnything()),
    ("verifier", lambda: None),
    ("selection_source", lambda: Source(material())),
    ("selection_source", lambda: (lambda: material().selection_material())),
])
@pytest.mark.row("N4.b", "the factory is handed a verifier= or selection_source= keyword (even a genuine one): authority_factory_argument_refused, nothing read, verifier not reached, no file changed")
def test_factory_refuses_caller_supplied_verifier_and_selection_source(tmp_path, spy, kwarg, make):
    kit = make_kit(tmp_path)
    obj = make()
    refused_build(tmp_path, kit, material(), "authority_factory_argument_refused", spy, reached=False, **{kwarg: obj})
    if isinstance(obj, AcceptAnything):
        assert obj.calls == 0


@pytest.mark.parametrize("bad", [None, "not callable", 7, object()])
@pytest.mark.row("N4.c", "host_source that is not callable: authority_factory_argument_refused (typed), no workflow")
def test_non_callable_host_source_is_refused(tmp_path, spy, bad):
    kit = make_kit(tmp_path)
    profile = kit.load()
    p, kw = H.flow_kwargs(tmp_path)
    got = None
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        got = AP.governed_age_workflow(profile, host_source=bad, scope=H.SCOPE, expected_mode="synthetic", **kw)
    assert got is None and exc.value.code == "authority_factory_argument_refused" and not spy.reached


@pytest.mark.parametrize("bad", [None, {"mode": "synthetic"}, "profile"])
@pytest.mark.row("N4.d", "the factory is given something that is not a loader's AuthorityProfile: authority_factory_argument_refused (no duck-typed or dict profile)")
def test_non_profile_object_is_refused(tmp_path, spy, bad):
    p, kw = H.flow_kwargs(tmp_path)
    got = None
    with pytest.raises((AP.AuthorityProfileRefusal, AttributeError, TypeError)) as exc:
        got = AP.governed_age_workflow(bad, host_source=Source(material()), scope=H.SCOPE, expected_mode="synthetic", **kw)
    assert got is None and not spy.reached
    if isinstance(exc.value, AP.AuthorityProfileRefusal):
        assert exc.value.code in ("authority_factory_argument_refused", "authority_config_scope_mismatch", "authority_config_mode_mismatch")


@pytest.mark.row("N4.e", "the built workflow's verifier is the exact Registry Ed25519Verifier: the core receives type(verifier) is Ed25519Verifier on every read, never a subclass or stub")
def test_workflow_verifier_is_the_exact_registry_adapter(tmp_path, spy):
    kit = make_kit(tmp_path)
    flow, p, src, _ = build(tmp_path, kit, material())
    d = flow.decide(p, now=H.NOW)
    assert d.result == "authorized"
    assert spy.n >= 2 and set(spy.verifier_types) == {H.ev.Ed25519Verifier}
    assert type(flow._f4_verifier) is H.ev.Ed25519Verifier and type(flow.cap_selection_source._verifier) is H.ev.Ed25519Verifier


@pytest.mark.row("N4.f", "the Registry is NOT importable (verifier layer missing): verifier_unavailable at construction, nothing read, nothing written")
def test_unimportable_registry_is_verifier_unavailable(tmp_path, spy, monkeypatch):
    kit = make_kit(tmp_path)
    real_import = importlib.import_module

    def broken(name, *a, **k):
        if name.startswith(("registry_successor", "registry_adapters")):
            raise ImportError("registry unavailable (test)")
        return real_import(name, *a, **k)

    prepared = H.flow_kwargs(tmp_path)
    before = snapshot_files(tmp_path)
    monkeypatch.setattr(AP.importlib, "import_module", broken)
    host = Source(material())
    got = None
    with pytest.raises(AP.AuthorityProfileRefusal) as exc:
        got = build(tmp_path, kit, None, host_source=host, prepared=prepared)
    assert got is None and exc.value.code == "verifier_unavailable"
    assert host.calls == 0 and not spy.reached and snapshot_files(tmp_path) == before


@pytest.mark.row("N4.g", "the Registry becomes unavailable AFTER construction: the next decide() is refused (selection_source_failed) with typed cause verifier_unavailable; no file changed; service returns when the Registry returns")
def test_registry_lost_after_construction_refuses_the_decision(tmp_path, spy, monkeypatch):
    kit = make_kit(tmp_path)
    flow, p, src, _ = build(tmp_path, kit, material())
    real_import = importlib.import_module

    def broken(name, *a, **k):
        if name.startswith(("registry_successor", "registry_adapters")):
            raise ImportError("registry unavailable (test)")
        return real_import(name, *a, **k)

    with monkeypatch.context() as m:
        m.setattr(AP.importlib, "import_module", broken)
        spy.reset()
        before = snapshot_files(tmp_path)
        with pytest.raises(Exception) as exc:
            flow.decide(p, now=H.NOW)
        assert "selection_source_failed" in str(exc.value)
        assert flow.cap_selection_source.last_refusal.code == "verifier_unavailable"
        assert snapshot_files(tmp_path) == before and not spy.reached
    assert flow.decide(p, now=H.NOW).result == "authorized"


# ---------------------------------------------------------------------------------------------------------------------------------------------- epoch floor
@pytest.mark.parametrize("label,floors", [("no_floors_at_all", []), ("floor_for_another_selection_only", [["sel-other", 1]])])
@pytest.mark.row("N4.h", "the pinned snapshot has NO per-selection epoch floor for the selection (empty min_epochs, or a floor for another selection): everything else admits, yet the unit refuses epoch_floor_missing")
def test_missing_epoch_floor_is_refused_even_when_the_verifier_admits(tmp_path, spy, label, floors):
    doc = snapshot_doc(min_epochs=floors)
    kit = make_kit(tmp_path, doc=doc)
    refused_build(tmp_path, kit, material(host_trust=H.trust_object(doc)), "epoch_floor_missing", spy, reached=True)
    (verdict,) = spy.verdicts
    assert verdict.admitted is True and verdict.epoch_floor_applied is False   # the Registry itself admitted: it is the unit that refuses
    assert all(x == "pass" for _, x in verdict.layers)


@pytest.mark.row("N4.i", "the epoch floor is removed from the pinned file only: that is a pin mismatch (fingerprint), caught BEFORE the verifier; floors cannot be stripped silently")
def test_stripping_the_floor_from_the_pinned_file_is_a_pin_mismatch(tmp_path, spy):
    kit = make_kit(tmp_path)
    kit.snapshot_path.write_bytes(H.dump(snapshot_doc(min_epochs=[])))
    refused_build(tmp_path, kit, material(), "snapshot_pin_mismatch", spy, reached=False)


@pytest.mark.row("N4.j", "a floor ABOVE the selection epoch (floor 2, selection epoch 1): the real verifier's epoch layer refuses (registry_not_applied), not epoch_floor_missing")
def test_floor_above_the_selection_epoch_is_refused_by_the_verifier(tmp_path, spy):
    doc = snapshot_doc(min_epochs=[[H.SELECTION_ID, 2]])
    kit = make_kit(tmp_path, doc=doc)
    refused_build(tmp_path, kit, material(host_trust=H.trust_object(doc)), "registry_not_applied", spy, reached=True)
    assert H.layers_of(spy.verdicts[0])["epoch"] == "refuse"


@pytest.mark.row("N4.k", "decision-time: once built, the pinned snapshot loses its floor (file rewritten WITH a matching new pin is impossible without the config): the next decide() refuses, no state changed")
def test_floor_lost_after_construction_refuses_the_decision(tmp_path, spy):
    kit = make_kit(tmp_path)
    flow, p, src, _ = build(tmp_path, kit, material())
    kit.snapshot_path.write_bytes(H.dump(snapshot_doc(min_epochs=[])))
    spy.reset()
    before = snapshot_files(tmp_path)
    with pytest.raises(Exception):
        flow.decide(p, now=H.NOW)
    assert flow.cap_selection_source.last_refusal.code == "snapshot_pin_mismatch"
    assert snapshot_files(tmp_path) == before and not spy.reached
