"""Per-scenario / per-principal reporting (C13) reads recorded results only and agrees with the recorded counts."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import scenario_report as SR  # noqa: E402
from build_dashboard import OUTCOMES_RUN, load_data, markdown  # noqa: E402

RUN = ROOT/OUTCOMES_RUN


JUNIT = """<?xml version="1.0"?><testsuites><testsuite>
<testcase classname="suites.v1-scenarios.test_scn_c11" name="test_a[other_principal]"><properties><property name="principal" value="urn:p:alice"/></properties></testcase>
<testcase classname="suites.v1-scenarios.test_scn_c11" name="test_a[x]"><failure message="no"/></testcase>
<testcase classname="suites.v1-scenarios.test_scn_c11" name="test_b"><properties><property name="principal" value="urn:p:bob"/></properties><skipped/></testcase>
<testcase classname="suites.v1-scenarios.test_asw_a" name="test_c"><error message="e"/></testcase>
<testcase classname="suites.v1-scenarios.test_add_c2c_bi" name="test_d"/>
</testsuite></testsuites>"""


class ScenarioReport(unittest.TestCase):
    def test_unit_mapping(self):
        self.assertEqual([SR.scenario_unit(c) for c in ('suites.v1-scenarios.test_scn_c03', 'x.test_scn_d02', 'x.test_asw_s', 'x.test_add_c2c_bi', 'x.test_other')],
                         ['C03', 'D02', 'ASW-S', 'ADD-C2C-BI', 'test_other'])

    def test_synthetic_junit_is_split_not_pooled(self):
        with tempfile.TemporaryDirectory() as d:
            job = Path(d)/'jobs/scenarios'
            job.mkdir(parents=True)
            (job/'junit.xml').write_text(JUNIT)
            r = SR.build(Path(d))
        by = {s['scenario']: s for s in r['per_scenario']}
        self.assertEqual((by['C11']['cases'], by['C11']['passed'], by['C11']['failed'], by['C11']['skipped']), (3, 1, 1, 1))
        self.assertEqual((by['ASW-A']['failed'], by['ADD-C2C-BI']['passed']), (1, 1))
        self.assertEqual({p['principal']: p['cases'] for p in r['per_principal']}, {'urn:p:alice': 1, 'urn:p:bob': 1, SR.UNRECORDED: 3})
        self.assertEqual(r['principal_attribution'], {'recorded': 2, 'unrecorded': 3})
        # an id token is a hint, never an attribution
        self.assertEqual(by['C11']['principals']['urn:p:alice']['cases'], 1)
        self.assertIn({'dimension': 'principal', 'cases': 1, 'passed': 1, 'failed': 0, 'skipped': 0}, r['identity_dimension_hint']['rows'])

    def test_recorded_run_agrees_with_job_counts_and_v1_validation_indexing(self):
        report = SR.build(RUN)
        counts = json.loads((RUN/'jobs/scenarios/result.json').read_text())['counts']
        t = report['totals']
        self.assertEqual((t['cases'], t['failed'], t['skipped']), (counts['testcases'], counts['failures'] + counts['errors'], counts['skipped']))
        self.assertEqual(sum(s['cases'] for s in report['per_scenario']), t['cases'])
        self.assertEqual(sum(s['failed'] for s in report['per_scenario']), t['failed'])
        self.assertEqual(sum(p['cases'] for p in report['per_principal']), t['cases'])
        # the outcome rule is the one tools/v1_validation.py uses to index the same JUnit (read-only function, no aggregate run)
        import v1_validation
        index = v1_validation.load_junit_index(RUN, [{'component': 'scenarios', 'os': 'ubuntu-latest', 'python': '3.12', '_dir': 'jobs/scenarios'}])
        mine = sorted((c['test'], {'failed': 'failed', 'skipped': 'skipped', 'passed': 'passed'}[c['outcome']]) for c in SR.read_cases(RUN/'jobs/scenarios/junit.xml', 'scenarios'))
        theirs = sorted((name, out) for _, name, out in index['scenarios'])
        self.assertEqual(mine, theirs)

    def test_c04_failures_are_visible_per_scenario(self):
        by = {s['scenario']: s for s in SR.build(RUN)['per_scenario']}
        self.assertEqual((by['C04']['cases'], by['C04']['failed']), (10, 4))
        self.assertTrue(all(s['failed'] == 0 for k, s in by.items() if k != 'C04'))

    def test_dashboard_carries_the_section_without_changing_scenario_verdicts(self):
        data = load_data()
        self.assertEqual(data['recorded_outcomes']['totals'], SR.build(RUN)['totals'])
        self.assertTrue(all(row['scenario_verdict'] == 'NOT RUN' for row in data['scenarios']))
        self.assertIn('## Recorded test outcomes by scenario and principal', markdown(data))


if __name__ == '__main__':
    unittest.main()
