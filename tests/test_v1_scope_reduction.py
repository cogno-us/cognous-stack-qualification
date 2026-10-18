"""Unit tests for the D15 scope-reduction reporting in tools/v1_validation.py (verdict rule unchanged)."""
import argparse
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import v1_validation as v  # noqa: E402

REQS = ROOT / 'process/v1-validation/v1-2026-10-16-a/requirements.json'
SR = {'decision': 'D15', 'final_status': 'FAIL', 'category': 'design-limit'}


def row(rid, status, mandatory=True, sr=None):
    r = {'id': rid, 'status': status, 'mandatory': mandatory}
    if sr:
        r['scope_reduction'] = dict(sr)
    return r


def aggregate(reqs_doc, jobs):
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        inp = td / 'in'
        (inp / 'v1v-freeze').mkdir(parents=True)
        (inp / 'v1v-freeze' / 'freeze-verification.json').write_text(json.dumps({'status': 'PASS'}))
        for name, st in jobs.items():
            (inp / ('v1v-' + name)).mkdir()
            (inp / ('v1v-' + name) / 'result.json').write_text(json.dumps({'component': name, 'status': st, 'os': 'ubuntu-latest', 'python': '3.12'}))
        rq = td / 'requirements.json'
        rq.write_text(json.dumps(reqs_doc))
        out = td / 'out'
        with contextlib.redirect_stdout(io.StringIO()):
            v.cmd_aggregate(argparse.Namespace(inputs=str(inp), out=str(out), validation_id='v1-2026-10-16-t', requirements=str(rq)))
        return json.loads((out / 'summary.json').read_text()), (out / 'summary.md').read_text()


def job_req(rid, comp, mandatory=True, sr=None):
    r = {'id': rid, 'kind': 'job', 'component': comp, 'mandatory': mandatory}
    if sr:
        r['scope_reduction'] = dict(sr)
    return r


class VerdictUnchanged(unittest.TestCase):
    def test_all_mandatory_pass_with_reduced_rows_is_pass(self):
        reqs = [row('A', 'PASS'), row('B', 'FAIL', False, SR), row('C', 'INCONCLUSIVE', False, dict(SR, final_status='INCONCLUSIVE')), row('D', 'NOT RUN', False, dict(SR, final_status='NOT RUN'))]
        self.assertEqual(v.verdict(reqs), 'PASS')

    def test_mandatory_fail_still_fails(self):
        self.assertEqual(v.verdict([row('A', 'PASS'), row('B', 'FAIL')]), 'FAIL')

    def test_mandatory_inconclusive_is_incomplete(self):
        self.assertEqual(v.verdict([row('A', 'PASS'), row('B', 'INCONCLUSIVE')]), 'INCOMPLETE')


class Blocks(unittest.TestCase):
    def setUp(self):
        self.reqs = [row('A', 'PASS'), row('B', 'FAIL', False, SR), row('C', 'INCONCLUSIVE', False, dict(SR, final_status='INCONCLUSIVE', category='inconclusive-partial-coverage')),
                     row('N', 'NOT APPLICABLE', False)]

    def test_full_catalog_keeps_real_statuses(self):
        fc = v.full_catalog_status(self.reqs)
        self.assertEqual(fc['status_counts']['PASS'], 1)
        self.assertEqual(fc['status_counts']['FAIL'], 1)
        self.assertEqual(fc['status_counts']['INCONCLUSIVE'], 1)
        self.assertEqual(fc['unreduced_mandatory_rows'], 3)
        self.assertEqual(fc['unreduced_mandatory_verdict'], 'FAIL')

    def test_scope_reduction_lists_every_moved_row_with_real_status(self):
        sr = v.scope_reduction_block(self.reqs)
        self.assertEqual(sr['count'], 2)
        self.assertEqual({(x['id'], x['decision'], x['final_status']) for x in sr['rows']}, {('B', 'D15', 'FAIL'), ('C', 'D15', 'INCONCLUSIVE')})

    def test_reduced_row_is_never_counted_pass(self):
        fc = v.full_catalog_status([row('B', 'FAIL', False, SR)])
        self.assertEqual(fc['status_counts']['PASS'], 0)


class EndToEnd(unittest.TestCase):
    def test_reduced_scope_pass_and_full_catalog_shows_fail(self):
        doc = {'requirements': [job_req('R1', 'good'), job_req('R2', 'bad', False, SR)]}
        s, md = aggregate(doc, {'good': 'PASS', 'bad': 'FAIL'})
        self.assertEqual(s['selected_v1_verdict'], 'PASS')
        self.assertEqual(s['mandatory_requirement_status_counts']['PASS'], 1)
        self.assertEqual(s['full_catalog_status']['status_counts']['FAIL'], 1)
        self.assertEqual(s['full_catalog_status']['unreduced_mandatory_verdict'], 'FAIL')
        self.assertEqual(s['scope_reduction']['rows'][0]['final_status'], 'FAIL')
        self.assertIn('Full-catalog status', md)
        self.assertIn('Scope reduction (1 rows', md)

    def test_mandatory_fail_still_fails_with_reduction_present(self):
        doc = {'requirements': [job_req('R1', 'bad'), job_req('R2', 'bad', False, SR)]}
        s, _ = aggregate(doc, {'bad': 'FAIL'})
        self.assertEqual(s['selected_v1_verdict'], 'FAIL')


class Catalog(unittest.TestCase):
    def test_d15_records_are_well_formed(self):
        rows = json.loads(REQS.read_text())['requirements']
        moved = [r for r in rows if r.get('scope_reduction')]
        self.assertEqual(len(moved), 36)
        cats = {'failed', 'inconclusive-partial-coverage', 'not-run-unimplemented', 'deferred', 'design-limit', 'fix-merged-outside-pinned-tuple'}
        for r in moved:
            self.assertFalse(r['mandatory'])
            self.assertEqual(r['scope_reduction']['decision'], 'D15')
            self.assertIn(r['scope_reduction']['category'], cats)
            self.assertIn(r['scope_reduction']['final_status'], ('FAIL', 'INCONCLUSIVE', 'NOT RUN'))
        self.assertEqual(sum(1 for r in rows if r['mandatory']), 39)


if __name__ == '__main__':
    unittest.main()
