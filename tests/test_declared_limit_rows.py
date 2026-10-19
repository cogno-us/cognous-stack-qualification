"""Unit tests for reporting declared known limits beside the `tests` rows they fall in (synthetic JUnit and a synthetic twin only).

No controller or aggregate run against real components: every JUnit report below is written by this file.
"""
import argparse
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import declared_limits as DL  # noqa: E402
import v1_validation as v  # noqa: E402

REPO = 'cogno-us/open-decision-evidence-standard'
MOD = 'tests.test_ex'
PATH = 'tests/test_ex.py'
ODES = 'odes'


def did(name):
    return f'{REPO}:{PATH}::{name}'


def twin(*declared_names, extra_amendments=()):
    ams = [{'timestamp': '2026-10-19T11:00:00Z', 'action': 'add_known_limit', 'id': did(n), 'text': 't', 'reason': 'r'} for n in declared_names]
    ams.extend(extra_amendments)
    return {'declared_known_limits': {'fix2_probes': {'declared': []},
                                      'authority_ra': {'selector_component': 'probes-control-plane', 'declared': []},
                                      'wiki_derived': {'declared': []}},
            'amendments': ams}


def case(name, kind='passed', cls=MOD):
    """One synthetic JUnit testcase element as text."""
    head = f'<testcase classname="{cls}" name="{name}">'
    body = {'passed': '', 'skipped': '<skipped type="pytest.skip" message="needs x"/>',
            'xfailed': '<skipped type="pytest.xfail" message="known"/>', 'failed': '<failure message="assert 1 == 2">x</failure>',
            'xpass': '<failure message="[XPASS(strict)] known">[XPASS(strict)] known</failure>'}[kind]
    return head + body + '</testcase>'


def junit(*cases):
    return '<?xml version="1.0"?><testsuites><testsuite name="pytest">' + ''.join(cases) + '</testsuite></testsuites>'


def selector(rx='example', min_=1, comp=ODES):
    return {'component': comp, 're': rx, 'min': min_}


def req(rid='ER-T-1', selectors=None, mandatory=True):
    return {'id': rid, 'kind': 'tests', 'mandatory': mandatory, 'selectors': selectors or [selector()]}


def index_from(junit_text, comp=ODES):
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / ('v1v-' + comp)
        d.mkdir()
        (d / 'junit-attempt1.xml').write_text(junit_text)
        return v.load_junit_index(Path(td), [{'component': comp, 'os': 'ubuntu-latest', 'python': '3.12', '_dir': d.name}], detail=True)


def evaluate(junit_text, declared_names, requirement=None, comp=ODES, **kw):
    record = DL.load(_write_twin(twin(*declared_names, **kw)))
    out = v.evaluate_requirements({'requirements': [requirement or req()]}, index_from(junit_text, comp), {}, record)
    return out[0]


_TMP = tempfile.TemporaryDirectory()
_N = [0]


def _write_twin(doc):
    _N[0] += 1
    p = Path(_TMP.name) / f'twin{_N[0]}.json'
    p.write_text(json.dumps(doc))
    return p


def tearDownModule():
    _TMP.cleanup()


class RowRule(unittest.TestCase):
    def test_undeclared_skip_is_inconclusive_even_beside_a_declared_pass(self):
        r = evaluate(junit(case('test_example_a'), case('test_example_b', 'skipped'), case('test_example_decl')), ['test_example_decl'])
        self.assertEqual(r['status'], 'INCONCLUSIVE')
        self.assertEqual(r['reason'], 'matched cases were skipped')
        self.assertEqual([c['outcome'] for c in r['declared_limit_cases']], ['passed'])

    def test_undeclared_failure_is_fail_even_when_a_declared_case_also_fails(self):
        r = evaluate(junit(case('test_example_a', 'failed'), case('test_example_decl', 'failed')), ['test_example_decl'])
        self.assertEqual(r['status'], 'FAIL')
        self.assertEqual(r['selector_results'][0]['failed_tests'], [f'{MOD}::test_example_a'])

    def test_declared_xfail_only_is_listed_and_does_not_make_the_row_inconclusive(self):
        r = evaluate(junit(case('test_example_a'), case('test_example_b'), case('test_example_decl', 'xfailed')), ['test_example_decl'])
        self.assertEqual(r['status'], 'PASS')
        self.assertEqual(r['undeclared_cases'], 2)
        self.assertEqual(r['declared_limit_cases'], [{'label': 'DECLARED-LIMIT', 'component': ODES, 'test': f'{MOD}::test_example_decl',
                                                      'declaration_id': did('test_example_decl'), 'outcome': 'xfailed', 'unexpected_pass': False}])
        self.assertEqual(r['reportable_conditions'], [])

    def test_declared_failure_is_listed_with_its_outcome_and_does_not_fail_the_row(self):
        r = evaluate(junit(case('test_example_a'), case('test_example_decl', 'failed')), ['test_example_decl'])
        self.assertEqual(r['status'], 'PASS')
        self.assertEqual([c['outcome'] for c in r['declared_limit_cases']], ['failed'])
        self.assertEqual(r['selector_results'][0]['failed'], 0)

    def test_declared_skip_is_listed_as_skipped_and_does_not_make_the_row_inconclusive(self):
        r = evaluate(junit(case('test_example_a'), case('test_example_decl', 'skipped')), ['test_example_decl'])
        self.assertEqual(r['status'], 'PASS')
        self.assertEqual([c['outcome'] for c in r['declared_limit_cases']], ['skipped'])

    def test_declared_pass_is_listed_as_passed(self):
        r = evaluate(junit(case('test_example_a'), case('test_example_decl')), ['test_example_decl'])
        self.assertEqual(r['status'], 'PASS')
        self.assertEqual([c['outcome'] for c in r['declared_limit_cases']], ['passed'])

    def test_unexpected_pass_of_a_declared_strict_xfail_fails_the_row_and_is_listed(self):
        r = evaluate(junit(case('test_example_a'), case('test_example_decl', 'xpass')), ['test_example_decl'])
        self.assertEqual(r['status'], 'FAIL')
        self.assertIn('DR-7', r['reason'])
        self.assertEqual(r['declared_limit_cases'][0]['outcome'], 'failed')
        self.assertTrue(r['declared_limit_cases'][0]['unexpected_pass'])
        self.assertEqual(r['reportable_conditions'], [f'declared test passed unexpectedly (strict expected failure XPASS): {MOD}::test_example_decl'])

    def test_a_declared_test_that_passes_without_being_a_strict_xfail_is_only_listed(self):
        r = evaluate(junit(case('test_example_a'), case('test_example_decl')), ['test_example_decl'])
        self.assertEqual(r['status'], 'PASS')
        self.assertFalse(r['declared_limit_cases'][0]['unexpected_pass'])
        self.assertEqual(r['reportable_conditions'], [])

    def test_declared_test_not_found_is_listed_as_not_run_and_makes_the_row_inconclusive(self):
        r = evaluate(junit(case('test_example_a'), case('test_example_b')), ['test_example_missing'])
        self.assertEqual(r['status'], 'INCONCLUSIVE')
        self.assertIn('was not run', r['reason'])
        self.assertEqual([(c['test'], c['outcome']) for c in r['declared_not_run']], [(f'{MOD}::test_example_missing', 'NOT RUN')])
        self.assertEqual(r['declared_limit_cases'], [])
        self.assertIn(f'declared test not run: {MOD}::test_example_missing', r['reportable_conditions'])

    def test_a_declared_test_the_row_would_not_select_is_not_listed_in_the_row(self):
        r = evaluate(junit(case('test_example_a')), ['test_other_missing'])
        self.assertEqual(r['status'], 'PASS')
        self.assertEqual(r['declared_not_run'], [])
        self.assertEqual(r['reportable_conditions'], [])

    def test_zero_undeclared_remaining_is_inconclusive_with_a_reason_and_a_condition(self):
        r = evaluate(junit(case('test_example_d1'), case('test_example_d2', 'xfailed')), ['test_example_d1', 'test_example_d2'],
                     req(selectors=[selector(min_=2)]))
        self.assertEqual(r['status'], 'INCONCLUSIVE')
        self.assertIn('zero undeclared cases remain', r['reason'])
        self.assertEqual(r['undeclared_cases'], 0)
        self.assertEqual(len(r['declared_limit_cases']), 2)
        self.assertTrue(any(c.startswith('zero undeclared cases remain') for c in r['reportable_conditions']))

    def test_zero_undeclared_is_judged_per_selector(self):
        r = evaluate(junit(case('test_example_d1'), case('test_other_a')), ['test_example_d1'],
                     req(selectors=[selector('example'), selector('other')]))
        self.assertEqual(r['status'], 'INCONCLUSIVE')

    def test_minimum_not_met_is_inconclusive(self):
        r = evaluate(junit(case('test_example_a'), case('test_example_decl')), ['test_example_decl'], req(selectors=[selector(min_=3)]))
        self.assertEqual(r['status'], 'INCONCLUSIVE')
        self.assertIn('fewer executed cases', r['reason'])

    def test_minimum_is_measured_over_all_matched_cases_declared_included(self):
        r = evaluate(junit(case('test_example_a'), case('test_example_b'), case('test_example_decl', 'xfailed')), ['test_example_decl'],
                     req(selectors=[selector(min_=3)]))
        self.assertEqual(r['status'], 'PASS')
        self.assertEqual(r['selector_results'][0]['matched'], 3)
        self.assertEqual(r['selector_results'][0]['undeclared_matched'], 2)

    def test_matching_is_exact_on_classname_and_name_and_never_a_pattern(self):
        j = junit(case('test_example_decl[a]'), case('test_example_decl'), case('test_example_decl', cls='tests.test_ex.Cls'), case('test_example_decl', cls='other.test_ex'))
        r = evaluate(j, ['test_example_decl'])
        self.assertEqual([c['test'] for c in r['declared_limit_cases']], [f'{MOD}::test_example_decl'])
        self.assertEqual(r['undeclared_cases'], 3)

    def test_a_parametrised_declaration_names_its_parameter(self):
        r = evaluate(junit(case('test_example_p[a.json]', 'failed'), case('test_example_p[b.json]')), ['test_example_p[a.json]'])
        self.assertEqual(r['status'], 'PASS')
        self.assertEqual(r['declared_limit_cases'][0]['test'], f'{MOD}::test_example_p[a.json]')

    def test_a_declared_test_of_another_component_does_not_apply(self):
        r = evaluate(junit(case('test_example_decl', 'skipped')), ['test_example_decl'], req(selectors=[selector(comp='bitrep')]), comp='bitrep')
        self.assertEqual(r['status'], 'INCONCLUSIVE')
        self.assertEqual(r['declared_limit_cases'], [])

    def test_a_row_with_no_declared_case_gets_the_rule_that_was_in_force(self):
        j = junit(case('test_example_a'), case('test_example_b', 'skipped'))
        with_empty = evaluate(j, [])
        plain = v.evaluate_requirements({'requirements': [req()]}, index_from(j), {})[0]
        self.assertEqual((with_empty['status'], with_empty['reason']), (plain['status'], plain['reason']))
        self.assertNotIn('declared_limit_cases', plain)

    def test_job_rows_are_unchanged(self):
        out = v.evaluate_requirements({'requirements': [{'id': 'J', 'kind': 'job', 'component': 'x'}]}, {}, {'x': 'FAIL'}, DL.load(_write_twin(twin())))
        self.assertEqual(out[0]['status'], 'FAIL')

    def test_verdict_stays_the_rule_over_row_statuses(self):
        rows = v.evaluate_requirements({'requirements': [req('A'), req('B', [selector('decl')])]},
                                       index_from(junit(case('test_example_a'), case('test_decl_x', 'failed'))), {}, DL.load(_write_twin(twin('test_decl_x'))))
        self.assertEqual([r['status'] for r in rows], ['PASS', 'INCONCLUSIVE'])
        self.assertEqual(v.verdict(rows), 'INCOMPLETE')


class DeclaredSet(unittest.TestCase):
    def test_set_is_twin_declarations_plus_additions_minus_withdrawals_in_order(self):
        w = {'timestamp': '2026-10-19T12:00:00Z', 'action': 'withdraw_known_limit', 'id': did('test_example_a')}
        a = {'timestamp': '2026-10-19T13:00:00Z', 'action': 'add_known_limit', 'id': did('test_example_a'), 'text': 't', 'reason': 'r'}
        self.assertEqual([e['name'] for e in DL.normalise(twin('test_example_a', 'test_example_b', extra_amendments=[w]))], ['test_example_b'])
        self.assertEqual([e['name'] for e in DL.normalise(twin('test_example_a', extra_amendments=[w, a]))], ['test_example_a'])

    def test_withdrawing_an_id_that_is_not_declared_is_refused(self):
        w = {'timestamp': 't', 'action': 'withdraw_known_limit', 'id': did('test_nope')}
        with self.assertRaises(DL.DeclaredSetError):
            DL.normalise(twin(extra_amendments=[w]))

    def test_duplicate_unknown_repository_and_wildcard_ids_are_refused(self):
        for bad in (did('t1'), 'cogno-us/not-a-component:tests/a.py::test_x', f'{REPO}:tests/*.py::test_x', f'{REPO}:tests/a.py::test_*', 'tests/a.py::test_x'):
            doc = twin('t1')
            doc['amendments'].append({'timestamp': 't', 'action': 'add_known_limit', 'id': bad, 'text': 't'})
            with self.assertRaises(DL.DeclaredSetError, msg=bad):
                DL.normalise(doc)

    def test_the_entry_of_an_external_id_names_its_classname_and_component(self):
        e = DL.normalise(twin('test_example_a'))[0]
        self.assertEqual((e['component'], e['classname'], e['name'], e['repository']), (ODES, MOD, 'test_example_a', REPO))

    def test_a_local_id_in_the_adversarial_tests_is_a_test_entry_without_a_controller_component(self):
        i = 'process/adversarial/tests/test_t05_target_equivalence.py::test_evaluators_agree_on_every_variant[namespace_prefix]'
        doc = twin()
        doc['amendments'].append({'timestamp': 't', 'action': 'add_known_limit', 'id': i, 'text': 't'})
        e = DL.normalise(doc)[0]
        self.assertEqual((e['kind'], e['component'], e['classname'], e['name']),
                         ('test', None, 'process.adversarial.tests.test_t05_target_equivalence', 'test_evaluators_agree_on_every_variant[namespace_prefix]'))
        self.assertEqual(DL.by_component(DL.load(_write_twin(doc))), {})

    def test_requirement_declarations_are_kept_but_are_not_cases(self):
        doc = twin()
        doc['amendments'].append({'timestamp': 't', 'action': 'add_known_limit', 'id': 'ADD-AUTH-RA', 'text': 't'})
        e = DL.normalise(doc)[0]
        self.assertEqual((e['kind'], e['component']), ('requirement', None))
        self.assertEqual(DL.by_component(DL.load(_write_twin(doc))), {})

    def test_hash_is_stable_and_changes_with_the_set(self):
        a = DL.load(_write_twin(twin('test_example_a', 'test_example_b')))
        b = DL.load(_write_twin(twin('test_example_b', 'test_example_a')))
        c = DL.load(_write_twin(twin('test_example_a')))
        self.assertEqual(a['declared_set_sha256'], b['declared_set_sha256'])
        self.assertNotEqual(a['declared_set_sha256'], c['declared_set_sha256'])

    def test_a_supplied_declared_set_that_differs_from_the_twin_is_refused(self):
        p = _write_twin(twin('test_example_a', 'test_example_b'))
        rec = DL.load(p)
        good = Path(_TMP.name) / 'set-good.json'
        good.write_text(json.dumps(rec))
        self.assertEqual(DL.load(p, declared_set_file=good)['declared_set_sha256'], rec['declared_set_sha256'])
        for name, mutate in (('dropped', lambda r: r['entries'].pop()), ('renamed', lambda r: r['entries'][0].update(name='test_example_z')),
                             ('hash only', lambda r: r.update(declared_set_sha256='0' * 64))):
            bad = json.loads(good.read_text())
            mutate(bad)
            f = Path(_TMP.name) / f'set-{name}.json'
            f.write_text(json.dumps(bad))
            with self.assertRaises(DL.DeclaredSetError, msg=name):
                DL.load(p, declared_set_file=f)

    def test_the_repository_twin_reads_as_a_set_and_the_component_table_matches_the_freeze_manifest(self):
        rec = DL.load()
        self.assertEqual(rec['counts']['entries'], len(rec['entries']))
        self.assertEqual(len(rec['declared_set_sha256']), 64)
        man = json.loads((ROOT / 'process/v1-validation/v1-2026-10-16-a/freeze-manifest.json').read_text())
        by_repo = {s['repository']: k for _, k, s in v.all_components(man)}
        for repo, comp in DL.EXTERNAL_REPO_COMPONENT.items():
            self.assertEqual(by_repo[repo], comp)

    def test_the_four_odes_retained_example_tests_of_the_twin_map_to_the_odes_component(self):
        got = {(e['classname'], e['name']) for e in DL.load()['entries'] if e['component'] == ODES}
        self.assertEqual(got, {('tests.test_restriction_semantics', 'test_control_legacy_export_is_digest_identical_to_the_retained_example'),
                               ('tests.test_restriction_semantics', 'test_explicit_export_end_to_end'),
                               ('tests.test_result_classification', 'test_control_producer_v2_examples_pass_the_semantic_layer[lost_ack.package.json]'),
                               ('tests.test_result_classification', 'test_control_producer_v2_examples_pass_the_semantic_layer[prior_absence.package.json]')})

    def test_a_twin_working_copy_that_differs_from_head_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            f = root / 'process/release-gate/preregistration.json'
            f.parent.mkdir(parents=True)
            f.write_text(json.dumps(twin('test_example_a')))
            for cmd in (['init', '-q'], ['add', '.'], ['-c', 'user.name=t', '-c', 'user.email=t@example.invalid', 'commit', '-q', '-m', 'x']):
                subprocess.run(['git', '-C', td, *cmd], check=True, capture_output=True)
            self.assertIn('committed copy', DL.committed_twin_bytes(f, root)[1])
            f.write_text(json.dumps(twin('test_example_a', 'test_example_b')))
            with self.assertRaises(DL.DeclaredSetError):
                DL.committed_twin_bytes(f, root)


def aggregate(junit_text, twin_doc, requirement, declared_set=None, comp=ODES, require_committed=False):
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        inp = td / 'in'
        (inp / 'v1v-freeze').mkdir(parents=True)
        (inp / 'v1v-freeze' / 'freeze-verification.json').write_text(json.dumps({'status': 'PASS'}))
        (inp / ('v1v-' + comp)).mkdir()
        (inp / ('v1v-' + comp) / 'result.json').write_text(json.dumps({'component': comp, 'status': 'FAIL', 'os': 'ubuntu-latest', 'python': '3.12'}))
        (inp / ('v1v-' + comp) / 'junit-attempt1.xml').write_text(junit_text)
        rq = td / 'requirements.json'
        rq.write_text(json.dumps({'requirements': [requirement]}))
        out = td / 'out'
        ns = argparse.Namespace(inputs=str(inp), out=str(out), validation_id='v1-2026-10-16-t', requirements=str(rq),
                                declared_twin=str(_write_twin(twin_doc)), declared_set=declared_set, require_committed_twin=require_committed)
        with contextlib.redirect_stdout(io.StringIO()):
            v.cmd_aggregate(ns)
        return json.loads((out / 'summary.json').read_text()), (out / 'summary.md').read_text(), json.loads((out / 'requirements-matrix.json').read_text()), (out / 'requirements-matrix.md').read_text()


class AggregateReport(unittest.TestCase):
    J = junit(case('test_example_a'), case('test_example_decl', 'xfailed'), case('test_example_x', 'xfailed'))

    def test_report_carries_the_hash_the_listing_and_the_row_status(self):
        j = junit(case('test_example_a'), case('test_example_b'), case('test_example_decl', 'xfailed'))
        summary, md, matrix, matrix_md = aggregate(j, twin('test_example_decl'), req())
        expected = DL.load(_write_twin(twin('test_example_decl')))['declared_set_sha256']
        self.assertEqual(summary['declared_limits']['declared_set_sha256'], expected)
        self.assertEqual(matrix['declared_set_sha256'], expected)
        self.assertIn(expected, md)
        self.assertIn(expected, matrix_md)
        self.assertIn(f'DECLARED-LIMIT `{MOD}::test_example_decl` ({ODES}): xfailed', md)
        self.assertEqual(summary['requirement_status_counts']['PASS'], 1)
        self.assertEqual(summary['selected_v1_verdict'], 'PASS')
        self.assertEqual(summary['declared_limits']['matchable_states'][0]['outcome'], 'xfailed')
        self.assertEqual(summary['declared_limits']['reportable_conditions'], [])

    def test_the_component_job_status_is_still_reported_as_it_is(self):
        summary, *_ = aggregate(junit(case('test_example_a'), case('test_example_decl', 'failed')), twin('test_example_decl'), req())
        self.assertEqual(summary['jobs'][0]['status'], 'FAIL')
        self.assertEqual(summary['selected_v1_verdict'], 'PASS')

    def test_zero_undeclared_is_reported_as_a_reportable_condition_and_blocks_the_verdict(self):
        summary, md, *_ = aggregate(junit(case('test_example_d1', 'xfailed')), twin('test_example_d1'), req())
        self.assertEqual(summary['selected_v1_verdict'], 'INCOMPLETE')
        self.assertEqual(len(summary['declared_limits']['reportable_conditions']), 1)
        self.assertIn('zero undeclared cases remain', md)

    def test_a_declared_test_of_an_uncollected_suite_does_not_affect_rows(self):
        doc = twin('test_example_a')
        doc['declared_known_limits']['wiki_derived']['declared'].append({'id': 'test_w.py::test_wiki_known_limit', 'path': 'suites/wiki-derived/test_w.py'})
        r = v.evaluate_requirements({'requirements': [req()]}, index_from(junit(case('test_example_a'), case('test_example_b'))), {}, DL.load(_write_twin(doc)))[0]
        self.assertEqual(r['status'], 'PASS')
        self.assertEqual(r['declared_not_run'], [])

    def test_not_run_declaration_is_listed_in_the_report_state_table(self):
        summary, md, *_ = aggregate(junit(case('test_example_a')), twin('test_example_gone'), req())
        self.assertEqual(summary['selected_v1_verdict'], 'INCOMPLETE')
        self.assertEqual(summary['declared_limits']['matchable_states'][0]['outcome'], 'NOT RUN')
        self.assertIn('NOT RUN', md)

    def test_aggregate_refuses_a_declared_set_that_differs_from_the_twin(self):
        rec = DL.load(_write_twin(twin('test_example_decl')))
        rec['entries'] = []
        f = Path(_TMP.name) / 'agg-set.json'
        f.write_text(json.dumps(rec))
        with self.assertRaises(SystemExit) as cm:
            aggregate(self.J, twin('test_example_decl'), req(), declared_set=str(f))
        self.assertIn('declared known limits cannot be taken from the committed twin', str(cm.exception))

    def test_aggregate_accepts_a_declared_set_equal_to_the_twin(self):
        f = Path(_TMP.name) / 'agg-set-ok.json'
        f.write_text(json.dumps(DL.load(_write_twin(twin('test_example_decl')))))
        summary, *_ = aggregate(self.J, twin('test_example_decl'), req(), declared_set=str(f))
        self.assertEqual(summary['declared_limits']['counts']['entries'], 1)

    def test_aggregate_refuses_a_twin_it_cannot_read_as_a_set(self):
        bad = twin()
        bad['amendments'].append({'timestamp': 't', 'action': 'add_known_limit', 'id': 'tests/*.py::test_x', 'text': 't'})
        with self.assertRaises(SystemExit):
            aggregate(self.J, bad, req())


if __name__ == '__main__':
    unittest.main()
