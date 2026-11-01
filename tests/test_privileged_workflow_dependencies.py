"""Privileged publication workflows install only hash-locked dependencies."""
from pathlib import Path
import re
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT/'tools/requirements-ci.lock'
PRIVILEGED = ('capture-qualification-run.yml', 'upstream-wiki-refresh.yml', 'publish-qualification-dashboard.yml')


class PrivilegedWorkflowDependencies(unittest.TestCase):
    def test_lock_pins_every_requirement_with_hashes(self):
        entries = re.split(r'\n(?=[A-Za-z])', '\n'.join(
            l for l in LOCK.read_text().splitlines() if l.strip() and not l.lstrip().startswith('#')))
        names = set()
        for entry in entries:
            head = entry.split()[0]
            self.assertRegex(head, r'^[A-Za-z0-9_.-]+==[^=\s]+$')
            self.assertIn('--hash=sha256:', entry)
            names.add(head.split('==')[0].lower())
        self.assertTrue({'pyyaml', 'jsonschema', 'referencing', 'rpds-py', 'attrs'} <= names)

    def test_privileged_jobs_require_hashes_and_limit_credential_persistence(self):
        for name in PRIVILEGED:
            doc = yaml.safe_load((ROOT/'.github/workflows'/name).read_text())
            for job_name, job in doc['jobs'].items():
                steps = job['steps']
                runs = '\n'.join(s.get('run', '') for s in steps)
                pushes = 'git push' in runs
                for step in steps:
                    for line in step.get('run', '').splitlines():
                        if 'pip install' in line:
                            with self.subTest(workflow=name, job=job_name, line=line):
                                self.assertIn('--require-hashes', line)
                                self.assertIn('-r tools/requirements-ci.lock', line)
                    if step.get('uses', '').startswith('actions/checkout@'):
                        with self.subTest(workflow=name, job=job_name, step='checkout'):
                            # Only a job that later pushes with the checkout token may persist it.
                            self.assertIs(step.get('with', {}).get('persist-credentials'), pushes)


if __name__ == '__main__':
    unittest.main()
