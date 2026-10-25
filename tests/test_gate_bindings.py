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


class MatrixDrift(unittest.TestCase):
    def test_changed_plan_row_is_detected_and_unchanged_passes(self):
        rows = [{'gate_id': gid, 'name': gid} for gid in g.GATE_IDS]
        t = copy.deepcopy(TABLE)
        for r, m in zip(t['requirements'], rows):
            r['gate']['plan_row_sha256'] = g.row_digest(m)
        g.compare_to_matrix(t, rows)
        rows[3] = dict(rows[3], name='changed')
        with self.assertRaises(ValueError) as cm:
            g.compare_to_matrix(t, rows)
        self.assertIn('QG-04', str(cm.exception))


class NothingHistoricalChanges(unittest.TestCase):
    def test_validation_reads_but_never_writes_inventory_files(self):
        paths = [g.CROSSWALK, g.CATALOG, ROOT / 'process/v1-validation/v1-2026-10-16-a/requirements.json']
        before = [(p, p.stat().st_mtime_ns, p.read_bytes()) for p in paths]
        g.validate()
        for p, mtime, data in before:
            self.assertEqual((p.stat().st_mtime_ns, p.read_bytes()), (mtime, data))


if __name__ == '__main__':
    unittest.main()
