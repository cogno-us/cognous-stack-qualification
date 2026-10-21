"""E2: the aggregate applies the zero-skip rule to the hub-tests job row (wiring from job counts to evaluate_requirements)."""
import argparse, contextlib, io, json, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import v1_validation as v  # noqa: E402
import agg_util as _agg_util  # noqa: E402

ROW = {'requirements': [{'id': 'SC-HUB-TESTS', 'kind': 'job', 'component': 'hub-tests', 'mandatory': True}]}


def aggregate(skipped):
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); inp = td / 'in'
        (inp / 'v1v-freeze').mkdir(parents=True)
        (inp / 'v1v-freeze' / 'freeze-verification.json').write_text(json.dumps({'status': 'PASS', 'validation_id': 'v1-2026-10-16-t', 'components': {'x': {}}, 'components_expected': ['x']}))
        (inp / 'v1v-hub-tests').mkdir()
        counts = {'testcases': 10, 'failures': 0, 'errors': 0, 'skipped': skipped}
        (inp / 'v1v-hub-tests' / 'result.json').write_text(json.dumps({'component': 'hub-tests', 'status': 'PASS', 'os': 'ubuntu-latest', 'python': '3.12',
                                                                       'attempts': [{'outcome': 'PASS', 'counts': counts}]}))
        (td / 'req.json').write_text(json.dumps(ROW))
        ns = argparse.Namespace(inputs=str(inp), out=str(td / 'out'), validation_id='v1-2026-10-16-t', requirements=str(td / 'req.json'),
                                declared_twin=None, declared_set=None, require_committed_twin=False)
        with contextlib.redirect_stdout(io.StringIO()):
            _agg_util.cmd_aggregate(ns)
        return json.loads((td / 'out' / 'summary.json').read_text())


class HubTestsSkips(unittest.TestCase):
    def test_zero_skips_passes(self):
        self.assertEqual(aggregate(0)['selected_v1_verdict'], 'PASS')

    def test_any_skip_blocks_the_row_and_the_verdict(self):
        s = aggregate(1)
        self.assertEqual(s['requirement_status_counts']['INCONCLUSIVE'], 1)
        self.assertEqual(s['selected_v1_verdict'], 'INCOMPLETE')


if __name__ == '__main__':
    unittest.main()
