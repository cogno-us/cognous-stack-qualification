"""Prevent workflows from running tests before their suite has been assembled."""
from pathlib import Path
import unittest
import yaml

class AssemblyOrder(unittest.TestCase):
    def test_assembly_precedes_test_commands(self):
        root=Path(__file__).resolve().parents[1]
        for path in (root/'.github/workflows').glob('*.yml'):
            doc=yaml.safe_load(path.read_text())
            for name,job in doc.get('jobs',{}).items():
                steps=job.get('steps',[])
                assembly=[i for i,s in enumerate(steps) if 'install_suite.py' in s.get('run','')]
                if not assembly: continue
                for i,step in enumerate(steps):
                    command=step.get('run','')
                    if 'pytest' in command or 'unittest' in command or 'python tools/' in command:
                        with self.subTest(workflow=path.name,job=name,step=i):
                            self.assertLess(assembly[0],i)
