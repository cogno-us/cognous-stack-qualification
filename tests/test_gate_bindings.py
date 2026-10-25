"""QPR-1: the proposed QG-01..QG-14 binding table is complete, consistent, resolves against the existing inventory,
keeps QG-02 inactive, and stores no execution result or verdict. The tests execute no qualification scenario."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'process/registry-v1'))
import validate_gate_bindings as g  # noqa: E402

TABLE = json.loads((ROOT / 'process/registry-v1/gate-bindings.proposed.v1.json').read_text(encoding='utf-8'))


def mutated(edit):
    t = copy.deepcopy(TABLE)
    edit(t)
    return t


def row(t, gid):
    return next(r for r in t['requirements'] if r['id'] == gid)


class RealTable(unittest.TestCase):
    def test_table_is_valid_and_shaped_as_specified(self):
        s = g.validate()
        self.assertEqual((s['gates'], s['active'], s['inactive']), (14, 13, ['QG-02']))

    def test_qg02_is_inactive_and_not_mandatory(self):
        r = row(TABLE, 'QG-02')
        self.assertEqual((r['gate']['v1_status'], r['mandatory']), ('INACTIVE_MAX_AMOUNT_DEFERRED', False))
        self.assertTrue(all(row(TABLE, f'QG-{i:02d}')['mandatory'] for i in range(1, 15) if i != 2))

    def test_every_gate_is_prepare_only_and_unqualified(self):
        for r in TABLE['requirements']:
            self.assertIs(r['gate']['qualified'], False)
            self.assertEqual(r['gate']['qualification_mode'], g.MODE)

    def test_scenario_ids_resolve_in_the_existing_inventory(self):
        known = g.inventory_ids()
        ids = {e['id'] for r in TABLE['requirements'] for e in r['gate']['scenario_ids']}
        self.assertGreaterEqual(len(ids), 33)
        self.assertLessEqual(ids, known)

    def test_qg14_binds_all_scenarios_without_listing_them(self):
        r = row(TABLE, 'QG-14')['gate']
        self.assertEqual((r['scenario_scope'], r['scenario_ids']), ('all_canonical_scenarios', []))

    def test_pins_match_the_audited_plan_revision(self):
        self.assertEqual((TABLE['plan_source']['revision'], TABLE['plan_source']['matrix_sha256']), (g.PLAN_REVISION, g.MATRIX_SHA256))


class Rejections(unittest.TestCase):
    def rejects(self, edit, fragment):
        with self.assertRaises(ValueError) as cm:
            g.validate(mutated(edit))
        self.assertIn(fragment, str(cm.exception))

    def test_missing_gate(self):
        self.rejects(lambda t: t['requirements'].pop(5), 'exactly QG-01..QG-14')

    def test_duplicate_gate_id_is_refused_by_the_reused_row_model(self):
        self.rejects(lambda t: t['requirements'][1].update(id='QG-01'), 'duplicate')

    def test_qg02_made_active(self):
        self.rejects(lambda t: row(t, 'QG-02')['gate'].update(v1_status='ACTIVE'), 'QG-02 must be INACTIVE')

    def test_qg02_made_mandatory(self):
        self.rejects(lambda t: row(t, 'QG-02').update(mandatory=True), 'QG-02 must be INACTIVE')

    def test_active_gate_made_inactive(self):
        self.rejects(lambda t: row(t, 'QG-03')['gate'].update(v1_status='INACTIVE_MAX_AMOUNT_DEFERRED'), 'QG-03')

    def test_gate_marked_qualified(self):
        self.rejects(lambda t: row(t, 'QG-04')['gate'].update(qualified=True), 'qualified must be false')

    def test_mode_changed(self):
        self.rejects(lambda t: row(t, 'QG-05')['gate'].update(qualification_mode='QUALIFIED'), 'qualification_mode')

    def test_unknown_scenario_id(self):
        self.rejects(lambda t: row(t, 'QG-04')['gate']['scenario_ids'].append({'id': 'ZZ99'}), 'does not resolve')

    def test_scenario_ids_removed(self):
        self.rejects(lambda t: row(t, 'QG-10')['gate'].update(scenario_ids=[]), 'no scenario ids')

    def test_all_scope_only_for_qg14(self):
        self.rejects(lambda t: row(t, 'QG-01')['gate'].update(scenario_scope='all_canonical_scenarios'), 'only QG-14')

    def test_qg14_cannot_narrow_to_a_listed_scope(self):
        self.rejects(lambda t: row(t, 'QG-14')['gate'].update(scenario_scope='listed', scenario_ids=[{'id': 'D01'}]), 'QG-14 must')

    def test_missing_existing_path(self):
        def edit(t):
            row(t, 'QG-03')['gate']['existing_test_refs'][0]['path'] = 'suites/does-not-exist.py'
        self.rejects(edit, 'not found in this repository')

    def test_no_existing_references(self):
        self.rejects(lambda t: row(t, 'QG-06')['gate'].update(existing_test_refs=[]), 'no existing test references')

    def test_result_status_key_refused_anywhere(self):
        for key in ('status', 'verdict', 'declared_status', 'result'):
            with self.subTest(key=key):
                self.rejects(lambda t, k=key: row(t, 'QG-07')['gate'].update({k: 'PASS'}), 'Result-like key')

    def test_qualification_claim_phrase_refused(self):
        self.rejects(lambda t: row(t, 'QG-08')['gate']['known_gaps'].append('This gate is independently qualified.'), 'claim phrase')

    def test_known_gaps_required(self):
        self.rejects(lambda t: row(t, 'QG-09')['gate'].update(known_gaps=[]), 'known_gaps')

    def test_plan_pin_changed(self):
        self.rejects(lambda t: t['plan_source'].update(matrix_sha256='0' * 64), 'pin mismatch')

    def test_incomplete_contract_reference(self):
        self.rejects(lambda t: t['contract_refs'][0].pop('revision'), 'Incomplete contract reference')

    def test_contract_reference_missing_locally(self):
        def edit(t):
            next(c for c in t['contract_refs'] if c['repository'].endswith('stack-qualification'))['path'] = 'nope.json'
        self.rejects(edit, 'not found in this repository')

    def test_malformed_row_is_refused_by_the_reused_requirement_model(self):
        self.rejects(lambda t: t['requirements'][0].update(kind='tests', selectors=[]), 'at least one selector')


def synthetic_matrix():
    rows = []
    for i, gid in enumerate(g.GATE_IDS):
        rows.append({'gate_id': gid, 'name': f'name {gid}', 'sprint': 'S5-2', 'v1_status': 'INACTIVE_MAX_AMOUNT_DEFERRED' if gid == 'QG-02' else 'ACTIVE',
                     'qualification_mode': g.MODE, 'scenario_ids': ['all'] if gid == 'QG-14' else ['C11', 'D02 (NO_TEST)'],
                     'existing_test_ids': ['suites/v1-scenarios/test_scn_c11.py (parametrized)', '/home/claude/cognous-ocs-registry/tests/test_x.py::test_y', 'some descriptive row'],
                     'new_tests_needed': ['a', 'b', 'c'][: 1 + i % 3]})
    return rows


def synthetic_table(rows):
    t = copy.deepcopy(TABLE)
    for r, m in zip(t['requirements'], rows):
        want = g.expected_binding(m)
        r['mandatory'], r['text'] = want['mandatory'], want['text']
        r['gate'].update(want['gate'])
        r['gate']['plan_row_sha256'] = g.row_digest(m)
    return t


class MatrixDrift(unittest.TestCase):
    def test_unchanged_matrix_passes(self):
        rows = synthetic_matrix()
        g.compare_to_matrix(synthetic_table(rows), rows)

    def test_changed_plan_row_is_detected_by_digest(self):
        rows = synthetic_matrix()
        t = synthetic_table(rows)
        rows[3] = dict(rows[3], name='changed')
        with self.assertRaises(ValueError) as cm:
            g.compare_to_matrix(t, rows)
        self.assertIn('QG-04', str(cm.exception))

    def test_binding_edited_while_source_and_digest_stay_intact_is_detected(self):
        rows = synthetic_matrix()
        edits = {
            'sprint': lambda gate: gate.update(sprint='S9-9'),
            'item count': lambda gate: gate.update(predeclared_new_test_items=99),
            'scenario list': lambda gate: gate.update(scenario_ids=[{'id': 'D01'}]),
            'references': lambda gate: gate.update(existing_test_refs=gate['existing_test_refs'][:1]),
            'scope': lambda gate: gate.update(scenario_scope='all_canonical_scenarios', scenario_ids=[]),
            'status': lambda gate: gate.update(v1_status='INACTIVE_MAX_AMOUNT_DEFERRED'),
        }
        for name, edit in edits.items():
            with self.subTest(edit=name):
                t = synthetic_table(rows)
                edit(row(t, 'QG-01')['gate'])
                with self.assertRaises(ValueError) as cm:
                    g.compare_to_matrix(t, rows)
                self.assertIn('QG-01', str(cm.exception))
        t = synthetic_table(rows)
        row(t, 'QG-01')['text'] = 'edited'
        with self.assertRaises(ValueError):
            g.compare_to_matrix(t, rows)

    def test_validate_passes_the_matrix_through(self):
        with self.assertRaises(ValueError):
            g.validate(synthetic_table(synthetic_matrix()), matrix_rows=synthetic_matrix()[:13])


class NothingHistoricalChanges(unittest.TestCase):
    def test_validation_reads_but_never_writes_inventory_files(self):
        paths = [g.CROSSWALK, g.CATALOG, ROOT / 'process/v1-validation/v1-2026-10-16-a/requirements.json']
        before = [(p, p.stat().st_mtime_ns, p.read_bytes()) for p in paths]
        g.validate()
        for p, mtime, data in before:
            self.assertEqual((p.stat().st_mtime_ns, p.read_bytes()), (mtime, data))


if __name__ == '__main__':
    unittest.main()
