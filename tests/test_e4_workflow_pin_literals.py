"""E-4: the pinned-repository shas written as literals in .github/workflows/v1-validation.yml (checkout refs, probes matrix) must equal the
pins in force (freeze manifest + refreeze overlay). Nothing tied them before; a refreeze that moved a pin left the workflow on the old one."""
import copy
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'suites'))
import _pins  # noqa: E402
import v1_validation as v  # noqa: E402

WF = ROOT / '.github/workflows/v1-validation.yml'
TEXT = WF.read_text()
RESOLVED = _pins.RESOLVED_MANIFEST


class WorkflowPinLiterals(unittest.TestCase):
    def test_the_workflow_literals_equal_the_resolved_pins(self):
        self.assertEqual(v.workflow_pin_mismatches(TEXT, RESOLVED), [])

    def test_the_parser_sees_checkout_refs_and_probe_matrix_shas(self):
        lits = v.workflow_pin_literals(TEXT)
        repos = {r for r, _ in lits}
        self.assertIn('cogno-us/cognous-open-control-stack', repos)       # checkout ref
        self.assertIn('cogno-us/cognous-evidence-registry', repos)        # checkout ref and probes matrix
        self.assertIn('cogno-us/cognous-institutional-governance', repos)  # probes matrix only
        self.assertGreaterEqual(len(lits), 18)

    def test_a_moved_pin_is_reported_for_a_checkout_ref(self):
        res = copy.deepcopy(RESOLVED)
        res['components_lock_remainder']['the_index']['sha'] = 'e' * 40
        bad = v.workflow_pin_mismatches(TEXT, res)
        self.assertTrue(bad)
        self.assertTrue(all('cognous-evidence-registry' in b for b in bad))

    def test_a_moved_pin_is_reported_for_a_probes_matrix_sha(self):
        res = copy.deepcopy(RESOLVED)
        res['components_subject']['control_plane']['sha'] = 'e' * 40
        self.assertTrue(any('cognous-control-plane' in b for b in v.workflow_pin_mismatches(TEXT, res)))

    def test_a_moved_hub_head_is_reported(self):
        res = copy.deepcopy(RESOLVED)
        res['identities']['hub']['head'] = 'e' * 40
        self.assertTrue(any('cognous-open-control-stack' in b for b in v.workflow_pin_mismatches(TEXT, res)))

    def test_a_non_sha_ref_for_a_pinned_repository_is_reported(self):
        text = TEXT.replace('ref: 8e10387f8b7808e5dd1965fea38b74141761d7a6', 'ref: main', 1)
        self.assertTrue(any('main' in b for b in v.workflow_pin_mismatches(text, RESOLVED)))

    def test_the_plan_job_runs_the_check_before_planning(self):
        self.assertIn('check-workflow-pins', TEXT)
        self.assertLess(TEXT.index('check-workflow-pins'), TEXT.index('v1_validation.py plan'))

    def test_the_subcommand_passes_on_the_repository(self):
        proc = subprocess.run([sys.executable, str(ROOT / 'tools/v1_validation.py'), 'check-workflow-pins', '--workflow', str(WF),
                               '--manifest', str(_pins.validation_dir() / 'freeze-manifest.json'),
                               '--refreeze-log', str(_pins.validation_dir() / 'refreeze-log.json')], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == '__main__':
    unittest.main()
