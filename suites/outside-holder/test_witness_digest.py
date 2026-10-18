"""M3 outside-held digest: a dropped or rewritten entry after a published digest is detected (addendum 101726_B, M3).

SPDX-License-Identifier: Apache-2.0

Scenarios: ``dropped_entry_after_published_digest_rejected`` (with its rewrite, drop-and-append, positive-control and mutation
companions) and the ``*_accepted_today`` characterisations of the same tampering on the code as it stands.

PROVENANCE of "expected today" (template leg e), per test:

* ``test_*_accepted_today_*``  RUN. They use only code that exists on control plane main fd0d5e0 (the shipped HMAC of
  ``signing.py`` over a ``ReplayBundle``; ``BoundedRecordStore``) and pass on a pristine checkout of it. The Ed25519 variant is
  MODELLED: no shipped signature covers a bounded journal or a replay bundle; the only shipped Ed25519 verification is for
  evidence statements (``runtime_authority.validate_evidence``). The test signs the canonical bytes of the record set with the
  same primitive and canonicalisation (``_canonical_bytes``) to stand for any key-holder-verifiable seal. Reading the code
  predicted "accepted"; running it confirmed it.
* ``test_*_rejected*`` and the other witness tests: new opt-in behaviour (``agent_control_plane.witness``). There is no expected
  value today and they FAIL on main fd0d5e0 by design (the module is absent).

What these prove: with a digest held by someone other than the key holder, a record set that lost or changed a covered row is
rejected, whatever seal the key holder re-applied. What they do NOT prove: tamper evidence against whoever holds the witness
(``witness_holder_can_rewrite_the_witness_limit`` shows a holder who controls the witness defeats the control), protection of rows
appended after the latest published digest, or anything about where a real witness is held. No network call, tag, release or
publication is made; the witness here is a file in ``tmp_path``.
"""
from __future__ import annotations

import copy
import json
import pathlib

import pytest

from _oi_flow import Flow

PRINCIPAL = "urn:cognous:principal:refund-service"
TODAY_RUN = ("run", "control plane main fd0d5e0 (pristine) and runtime main 6bfb77ee: the shipped HMAC (signing.py) and "
                    "BoundedRecordStore accept a record set after an entry is dropped and the set is re-sealed by the key holder")
SECRET = "synthetic-record-store-key"


def W():
    import agent_control_plane.witness as witness  # lazy: absent on main fd0d5e0, so tests that need it fail by design there
    return witness


# ---------------------------------------------------------------------------------------------------- the record set
def refused_flow(tmp_path, mp):
    """A real journal: an authorised effect whose grant is revoked before dispatch, so the store holds a refusal row."""
    flow = Flow(tmp_path, mp, identity=False)
    next(iter(flow.r.statuses.values())).status = "revoked"
    result = flow.run(flow.d1)
    assert result.status == "denied" and flow.record().refusals
    return flow


def store_document(flow) -> dict:
    return json.loads(pathlib.Path(flow.f.records.path).read_text(encoding="utf-8"))


def write_document(flow, document) -> None:
    pathlib.Path(flow.f.records.path).write_text(json.dumps(document, indent=2), encoding="utf-8")


def drop_refusal(document: dict) -> dict:
    """The key holder hides the refusal: the row is removed and everything else is left as it was."""
    tampered = copy.deepcopy(document)
    assert tampered["refusals"]
    tampered["refusals"] = []
    return tampered


def rewrite_refusal(document: dict) -> dict:
    """The key holder rewrites the refusal so it no longer says the grant was revoked."""
    tampered = copy.deepcopy(document)
    tampered["refusals"][0]["reasons"] = ["status_unreadable"]
    return tampered


# ---------------------------------------------------------------------------------------------------- the seals
def ed25519_pair():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    private = Ed25519PrivateKey.generate()
    return private, private.public_key()


def sign_set(private, document: dict) -> bytes:
    from agent_control_plane.bounded import _canonical_bytes
    return private.sign(_canonical_bytes(document))


def verify_set(public, document: dict, signature: bytes) -> bool:
    from agent_control_plane.bounded import _canonical_bytes
    try:
        public.verify(signature, _canonical_bytes(document))
        return True
    except Exception:
        return False


def replay_bundle():
    """A real ReplayBundle with a blocked action (the shipped HMAC signs this type)."""
    from agent_control_plane.records import RunRecorder
    recorder = RunRecorder()
    recorder.start_run(task="outside-holder", actor="test-agent", environment="test", allowed_tools=["crm_read"],
                       blocked_tools=["email_send"], policy_version="v1.0")
    for tool, kind in (("crm_read", "read"), ("email_send", "external_send")):
        recorder.evaluate_action(recorder.propose_action(tool_name=tool, action_type=kind, target="customer:1"))
    recorder.complete_run("done")
    bundle = recorder.generate_replay_bundle()
    assert bundle.blocked_actions
    return bundle


# ---------------------------------------------------------------------------------------------------- today (run)
def test_dropped_entry_accepted_today_hmac_replay_bundle(record_property):
    """RUN today: the key holder drops a blocked-action row and re-signs with the HMAC key; the shipped verifier accepts."""
    from agent_control_plane.signing import sign_replay_bundle, verify_signed_replay_bundle
    original = replay_bundle()
    signed = sign_replay_bundle(original, SECRET)
    assert verify_signed_replay_bundle(signed, SECRET) is True
    tampered = original.model_copy(update={"blocked_actions": []})
    resigned = sign_replay_bundle(tampered, SECRET)  # the key holder can mint any signature
    assert verify_signed_replay_bundle(resigned, SECRET) is True, "expected today: accepted"
    record_property("principal", PRINCIPAL)
    record_property("m3_today_hmac", "accepted: dropped blocked_actions row, re-signed with the HMAC key")
    record_property("provenance", json.dumps(TODAY_RUN))


def test_dropped_entry_accepted_today_signature_scheme(tmp_path, record_property):
    """RUN today (scheme MODELLED, see module docstring): the key holder drops the refusal row and re-signs with Ed25519."""
    mp = pytest.MonkeyPatch()
    try:
        flow = refused_flow(tmp_path, mp)
        private, public = ed25519_pair()
        original = store_document(flow)
        assert verify_set(public, original, sign_set(private, original))
        tampered = drop_refusal(original)
        assert verify_set(public, tampered, sign_set(private, tampered)), "expected today: accepted"
        record_property("principal", PRINCIPAL)
        record_property("m3_today_signature", "accepted: dropped refusals row, re-signed with the Ed25519 key (modelled seal)")
    finally:
        mp.undo()


def test_dropped_entry_accepted_today_bounded_record_store(tmp_path, record_property):
    """RUN today: the store accepts a journal file whose refusal row was removed; load() validates shape only."""
    mp = pytest.MonkeyPatch()
    try:
        flow = refused_flow(tmp_path, mp)
        write_document(flow, drop_refusal(store_document(flow)))
        loaded = flow.f.records.load()
        assert loaded.refusals == [] and loaded.decisions, "expected today: accepted"
        record_property("principal", PRINCIPAL)
        record_property("m3_today_store", "accepted: BoundedRecordStore.load() validates schema only")
    finally:
        mp.undo()


# ---------------------------------------------------------------------------------------------------- the witness (new)
def published(flow, tmp_path):
    witness = W()
    held = witness.LocalFileWitness(tmp_path / "witness" / "digests.jsonl")
    record = witness.publish_head(store_document(flow), held)
    assert record["sequence"] == 0 and record["ledgers"]["refusals"]["count"] == 1
    return held


def test_dropped_entry_after_published_digest_rejected(tmp_path, record_property):
    """The scenario. Legs: (a) negative: the tampered set is not accepted under any seal; (b) the verdict names the failed check
    and the ledger; (c) control: the untouched set verifies, and honest appends after the digest are not rejected (they are
    reported as unwitnessed); (d) mutation: see ``test_blind_head_comparison_lets_the_drop_through``; (e) provenance: new
    behaviour, see module docstring."""
    witness = W()
    mp = pytest.MonkeyPatch()
    try:
        flow = refused_flow(tmp_path, mp)
        held = published(flow, tmp_path)
        original = store_document(flow)

        # (c) control first: untouched, and with an honest append after the digest.
        assert witness.verify_against_witness(original, held).ok
        appended = copy.deepcopy(original)
        appended["refusals"].append(copy.deepcopy(original["refusals"][0]))
        control = witness.verify_against_witness(appended, held)
        assert control.ok and control.unwitnessed_rows == {"refusals": 1}, control

        # the three seals, each re-applied by the key holder over the tampered set
        tampered = drop_refusal(original)
        from agent_control_plane.signing import sign_replay_bundle, verify_signed_replay_bundle
        bundle = replay_bundle()
        bundle_held = witness.LocalFileWitness(tmp_path / "witness" / "bundle.jsonl")
        witness.publish_head(bundle, bundle_held)
        resigned = sign_replay_bundle(bundle.model_copy(update={"blocked_actions": []}), SECRET)
        assert verify_signed_replay_bundle(resigned, SECRET)                       # the seal accepts
        private, public = ed25519_pair()
        assert verify_set(public, tampered, sign_set(private, tampered))           # the seal accepts
        write_document(flow, tampered)
        assert flow.f.records.load()                                                # the store accepts

        for label, subject, witness_held in (("hmac_replay_bundle", resigned.replay_bundle, bundle_held),
                                             ("signature_scheme", tampered, held),
                                             ("bounded_record_store", store_document(flow), held)):
            verdict = witness.verify_against_witness(subject, witness_held)
            assert not verdict.ok, label                                            # (a)
            assert verdict.reasons == [witness.CODE_SHRUNK], (label, verdict.reasons)  # (b)
            assert verdict.findings[0]["published_count"] == 1 and verdict.findings[0]["found_count"] == 0
        record_property("principal", PRINCIPAL)
        record_property("m3_rejected", json.dumps({"reasons": verdict.reasons, "scope": verdict.scope}))
    finally:
        mp.undo()


def test_rewritten_entry_after_published_digest_rejected(tmp_path):
    witness = W()
    mp = pytest.MonkeyPatch()
    try:
        flow = refused_flow(tmp_path, mp)
        held = published(flow, tmp_path)
        verdict = witness.verify_against_witness(rewrite_refusal(store_document(flow)), held)
        assert not verdict.ok and verdict.reasons == [witness.CODE_HEAD_MISMATCH]
        assert verdict.findings[0]["ledger"] == "refusals"
    finally:
        mp.undo()


def test_dropped_then_replaced_entry_is_a_head_mismatch(tmp_path):
    """Dropping a row and appending another restores the count; the head still differs."""
    witness = W()
    mp = pytest.MonkeyPatch()
    try:
        flow = refused_flow(tmp_path, mp)
        held = published(flow, tmp_path)
        tampered = drop_refusal(store_document(flow))
        tampered["refusals"].append({**store_document(flow)["refusals"][0], "refusal_id": "forged"})
        verdict = witness.verify_against_witness(tampered, held)
        assert not verdict.ok and verdict.reasons == [witness.CODE_HEAD_MISMATCH]
    finally:
        mp.undo()


def test_dropped_entry_in_an_earlier_published_digest_is_still_caught(tmp_path):
    """Every held digest is checked, not only the latest: a drop that predates the latest publication is caught too, and a latest-only
    witness (no history) still catches a drop covered by that latest digest."""
    witness = W()
    mp = pytest.MonkeyPatch()
    try:
        flow = refused_flow(tmp_path, mp)
        held = published(flow, tmp_path)
        grown = store_document(flow)
        grown["refusals"].append({**grown["refusals"][0], "refusal_id": "second"})
        witness.publish_head(grown, held)                       # sequence 1 covers two refusals
        tampered = drop_refusal(grown)
        verdict = witness.verify_against_witness(tampered, held)
        assert not verdict.ok and verdict.reasons == [witness.CODE_SHRUNK]
        assert {f["sequence"] for f in verdict.findings} == {0, 1}

        class LatestOnly:
            def publish(self, digest):
                return held.publish(digest)

            def latest(self):
                return held.latest()
        assert not witness.verify_against_witness(tampered, LatestOnly()).ok
    finally:
        mp.undo()


def test_publisher_refuses_to_publish_over_a_rewrite(tmp_path):
    """An honest publisher verifies first: publishing a rewrite as the next digest would make it the baseline."""
    witness = W()
    mp = pytest.MonkeyPatch()
    try:
        flow = refused_flow(tmp_path, mp)
        held = published(flow, tmp_path)
        with pytest.raises(witness.WitnessRefused):
            witness.publish_head(rewrite_refusal(store_document(flow)), held)
        assert len(held.history()) == 1
    finally:
        mp.undo()


def test_no_digest_is_not_a_pass(tmp_path):
    witness = W()
    mp = pytest.MonkeyPatch()
    try:
        flow = refused_flow(tmp_path, mp)
        verdict = witness.verify_against_witness(store_document(flow), witness.LocalFileWitness(tmp_path / "none.jsonl"))
        assert not verdict.ok and verdict.reasons == [witness.CODE_NO_DIGEST]
    finally:
        mp.undo()


def test_blind_head_comparison_lets_the_drop_through(tmp_path):
    """Leg (d), mutation check. Make the head comparison blind (every commitment constant) and the same drop-and-replace is
    accepted: the rejection above depends on the head comparison, not on the scaffolding around it."""
    witness = W()
    mp = pytest.MonkeyPatch()
    try:
        flow = refused_flow(tmp_path, mp)
        mp.setattr(witness, "commitment", lambda value: "sha256:" + "1" * 64)
        held = witness.LocalFileWitness(tmp_path / "blind.jsonl")
        witness.publish_head(store_document(flow), held)
        tampered = rewrite_refusal(store_document(flow))
        assert witness.verify_against_witness(tampered, held).ok, "mutation must let the rewrite through (the real test then fails)"
    finally:
        mp.undo()


def test_witness_holder_can_rewrite_the_witness_limit(tmp_path):
    """The stated limit, as a test. Whoever controls the witness can replace the held chain with one that matches a tampered record
    set, and the verifier accepts it. The digest gives visibility to a reader who holds an independent copy of it, not tamper
    evidence against the witness holder."""
    witness = W()
    mp = pytest.MonkeyPatch()
    try:
        flow = refused_flow(tmp_path, mp)
        path = tmp_path / "witness" / "digests.jsonl"
        held = witness.LocalFileWitness(path)
        witness.publish_head(store_document(flow), held)
        honest_copy = path.read_text(encoding="utf-8")            # an independent reader's copy of the original digest
        tampered = rewrite_refusal(store_document(flow))
        path.unlink()
        witness.LocalFileWitness(path).publish(witness.make_record(tampered))   # the witness holder rewrites the chain
        assert witness.verify_against_witness(tampered, witness.LocalFileWitness(path)).ok
        copy_path = tmp_path / "honest-copy.jsonl"
        copy_path.write_text(honest_copy, encoding="utf-8")
        assert not witness.verify_against_witness(tampered, witness.LocalFileWitness(copy_path)).ok  # the independent copy still catches it
    finally:
        mp.undo()
