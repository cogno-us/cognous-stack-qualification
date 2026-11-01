"""Independent verifier probes (PROBE2_VERIFIER_DIR) for the rules that exist only there: the binding members compared with
the decision's captured inputs, and the destination count against the grant ceiling. Run records and ledger snapshots are
read from the verifier's own test data and damaged one member at a time.
"""
import copy
import json

import pytest

from _support import known_limit, real_run, refusal_codes, verifier_data

RUNS = ("adapter-applied", "adapter-lost-ack-then-land", "adapter-renewal-race")
ROLES = {"run_record": "bounded-run-record.json", "proposal_export": "proposal.json", "manifest": "manifest.json"}
LEDGER = "destination-with-operation-digest.json"


def evaluate(name, record=None, ledger=None):
    """Verify one orchestrator run (record, proposal, manifest and the ledger projection that carries operation digests)."""
    from cognous_verify import engine
    from cognous_verify.canon import canonical_bytes
    directory = verifier_data("orchestrator-runs", name)
    files = []
    for role, filename in ROLES.items():
        data = (directory / filename).read_bytes()
        if role == "run_record" and record is not None:
            data = canonical_bytes(record)
        files.append(engine.InputFile(role, filename, data))
    data = (directory / LEDGER).read_bytes() if ledger is None else canonical_bytes(ledger)
    files.append(engine.InputFile("destination_ledger", LEDGER, data))
    result = engine.evaluate(files)
    assert not [r.check_id for r in result.results if r.error], "the verifier reported an internal error"
    refuted = sorted({f.code for r in result.results if r.verdict == "refuted" for f in r.findings})
    return result.overall, refuted


def record_of(name):
    return json.loads((verifier_data("orchestrator-runs", name) / ROLES["run_record"]).read_text(encoding="utf-8"))


def ledger_of(name):
    return json.loads((verifier_data("orchestrator-runs", name) / LEDGER).read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------- valid controls
@pytest.mark.parametrize("name", RUNS)
def test_control_orchestrator_runs_with_operation_digests_are_accepted(name):
    assert evaluate(name) == ("accept", [])


def test_control_the_largest_ceiling_among_a_grants_decisions_governs():
    """One decision's ceiling lowered, the other left at 2: the count of 2 is still inside the largest ceiling."""
    record = record_of("adapter-renewal-race")
    record["decisions"][0]["binding"]["effective_max_effects"] = 1
    assert evaluate("adapter-renewal-race", record=record) == ("accept", [])


# --------------------------------------------------------------------------------------------- ledger ceiling
def test_probe_a_destination_count_above_every_ceiling_of_the_grant_is_refused():
    """Both decisions of the grant carry ceiling 1 while the destination holds two applied effects for it."""
    record = record_of("adapter-renewal-race")
    for decision in record["decisions"]:
        decision["binding"]["effective_max_effects"] = 1
    assert ledger_of("adapter-renewal-race")["grant_effect_counts"] == {"urn:cognous:grant:routine-1": 2}
    overall, refuted = evaluate("adapter-renewal-race", record=record)
    assert overall == "reject" and refuted != []



# ------------------------------------------------------------------------------------------------ binding members
BINDING_MEMBERS = {  # member -> (a changed value, the captured input that states the member)
    "requirement_id": (lambda v: "urn:cognous:authority-requirement:other-v1", "conflict input id"),
    "policy_versions": (lambda v: [{**v[0], "version": "9.9"}], "policy input observed version"),
    "role_mapping_digest": (lambda v: "sha256:" + "a" * 64, "role mapping input observed digest"),
    "authority_context_status": (lambda v: "active", "authority context input observed interface status"),
    "effective_max_effects": (lambda v: v + 5, "grant ceiling"),
}


def _mutated(record, member):
    change, _ = BINDING_MEMBERS[member]
    damaged = copy.deepcopy(record)
    for decision in damaged["decisions"]:
        if decision["binding"] is not None:
            decision["binding"][member] = change(decision["binding"][member])
    return damaged


def test_control_the_unchanged_authorized_record_is_accepted():
    assert refusal_codes("verifier", real_run("journal-applied"), "control-plane-journal") == []


JOURNAL_ONLY_LIMIT = ("known limit: in a record verified without its proposal export and destination ledger, a change to this binding member "
                      "is checked against those two documents only, not against the captured inputs")
JOURNAL_ONLY_UNCHECKED = ("effective_max_effects",)


@pytest.mark.parametrize("member", [pytest.param(m, id=m, marks=[known_limit(JOURNAL_ONLY_LIMIT)] if m in JOURNAL_ONLY_UNCHECKED else [])
                                    for m in sorted(BINDING_MEMBERS)])
@pytest.mark.parametrize("run", ["journal-applied"])
def test_probe_a_binding_member_changed_alone_is_refused_against_the_captured_inputs(run, member):
    """One member of the decision binding changes; the inputs the decision captured still state the original value."""
    damaged = _mutated(real_run(run), member)
    assert refusal_codes("verifier", damaged, "control-plane-journal") != []


@pytest.mark.parametrize("member", sorted(BINDING_MEMBERS), ids=sorted(BINDING_MEMBERS))
def test_probe_a_binding_member_changed_alone_is_refused_with_proposal_and_ledger_supplied(member):
    """The same change in a run verified with its proposal export, manifest and destination ledger."""
    overall, refuted = evaluate("adapter-applied", record=_mutated(record_of("adapter-applied"), member))
    assert overall == "reject" and refuted != []
