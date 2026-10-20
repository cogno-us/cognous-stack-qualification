"""Report generator: required blocks, wording that must stay unchanged, masking and the block of RP-6."""
from comparators.runner import cells as C
from comparators.runner import ocs_column, report

OCS = ocs_column.OCS_PROFILE
OPA = 'opa-transactional-application'
GRAPH = 'langgraph-opa-transactional-application'
PROFILES = [OCS, OPA, GRAPH]
A = C.ASKED


def state():
    return dict(status=A, run=True, scored=True, reason='', reason_code=None, citations=[], origin='x', void=False)


def row(profile, ok, sid='S1'):
    return dict(case_id=sid, profile=profile, mode='scored', repetition=0, seed=1701, pass_case=ok, outputs=[], unexpected_effect_count=0,
                missing_effect_count=0, false_allows=0, false_blocks=0, denied_calls=0, durably_recorded_denials=0)


def table(results, profiles=PROFILES):
    states = {p: {'S1': state()} for p in profiles}
    rows = [row(p, results[p]) for p in profiles]
    return C.build_set('corner', [dict(id='S1', title='S1', scenarios=['S1'])], profiles, states, rows, 1, OCS)


def test_every_report_carries_the_unchanged_scope_text_caveats_and_blocks():
    text = report.render([table({OCS: True, OPA: True, GRAPH: True})], None)
    for needle in (report.SCOPE_TEXT, report.RP8_CAVEATS, 'Cases where a comparator passes and OCS does not (RP-6)', 'Run identity (RP-9)',
                   'Comparison table (RP-4)', 'Counts of the oracle (RP-5)', 'Comparative statements (RP-7)', report.NE_NC_MEANING,
                   'Operational trust stays on HOLD'):
        assert needle in text


def test_the_block_of_rp6_is_present_with_none_when_no_case_qualifies():
    text = report.render([table({OCS: True, OPA: True, GRAPH: True})], None)
    assert text.split('(RP-6)')[1].lstrip().startswith('None.')


def test_a_comparator_that_passes_where_the_destination_fails_is_listed():
    text = report.render([table({OCS: False, OPA: True, GRAPH: False})], None)
    assert '- S1: OPA application pass; OCS fail' in text


def test_no_comparison_is_made_for_a_set_that_was_not_run_for_every_configuration():
    states = {p: {'S1': state()} for p in PROFILES}
    t = C.build_set('corner', [dict(id='S1', title='S1', scenarios=['S1'])], PROFILES, states, [row(OCS, True), row(OPA, True)], 1, OCS)
    assert report.comparable(t) is False
    assert 'Not evaluated' in report.render([t], None)


def test_a_masked_report_shows_no_outcome_and_no_declaration():
    states = {p: {'twin-1': state()} for p in PROFILES}
    rows = [dict(case_id='twin-1', profile=p, mode='masked', repetition=0, seed=1701, executed=True) for p in PROFILES]
    t = C.build_set('corner', [dict(id='twin-1', title='(masked twin)', scenarios=['twin-1'])], PROFILES, states, rows, 1, OCS)
    text = report.render([t], None, masked=True)
    assert 'Counts of the oracle' not in text and 'Declarations for the protected destination' not in text
    assert '| twin-1 | masked' in text
    assert 'verdicts discarded' in text


def test_the_cross_reference_is_labelled_as_another_harness():
    assert report.CROSSREF_LABEL == 'different harness, not scored by this oracle'
