"""Receipts remain complete and explicit without pretending to be audits."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
spec=importlib.util.spec_from_file_location('security_coverage',Path(__file__).resolve().parents[1]/'tools/security_coverage.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class CoverageTests(unittest.TestCase):
    def test_binary_and_symlinks_are_not_claimed_reviewed(self):
        self.assertEqual(m.inspect_blob(b'\xff','image.bin','100644')[2]['semantic_review'],'deferred')
        self.assertEqual(m.inspect_blob(b'../secret','link','120000')[2]['semantic_review'],'deferred')
    def test_no_secret_values_emitted(self):
        value=b'ghp_'+b'A'*40
        methods,flags,details=m.inspect_blob(value,'fixture.txt','100644')
        self.assertEqual(flags[0]['rule'],'credential-format');self.assertNotIn(value.decode(),str(flags))
    def test_python_screen_is_not_semantic_clearance(self):
        methods,flags,details=m.inspect_blob(b'import subprocess\nsubprocess.run(["x"])\n','tool.py','100644')
        self.assertIn('python-ast-parse',methods);self.assertEqual(flags[0]['rule'],'process-execution')
        self.assertEqual(details['semantic_review'],'not_established_by_automated_screen')
    def test_budget_and_invalid_python_are_explicit(self):
        self.assertEqual(m.inspect_blob(b'x'*(m.MAX_PARSE_BYTES+1),'large.txt','100644')[1][0]['rule'],'parse-budget-exceeded')
        self.assertEqual(m.inspect_blob(b'def\n','bad.py','100644')[1][0]['rule'],'python-parse-unavailable')
    def test_exact_git_objects_ignore_dirty_worktree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            def git(*a):return subprocess.check_output(['git','-C',tmp,*a],text=True)
            git('init','-q');(root/'a.py').write_text('x=1\n');git('add','a.py')
            git('-c','user.name=Fixture','-c','user.email=f@example.invalid','commit','-qm','fixture');sha=git('rev-parse','HEAD').strip()
            (root/'a.py').write_text('BROKEN WORKTREE')
            result=m.screen(root,sha,label='test');self.assertEqual(result['totals']['paths'],1)
            self.assertIn('python-ast-parse',result['files'][0]['methods'])
            with self.assertRaises(ValueError):m.tree_inventory(root,'main')
    def test_delta_distinguishes_new_review_scope(self):
        a={'files':[{'path':'old','git_blob':'a'},{'path':'same','git_blob':'b'}]};b={'files':[{'path':'new','git_blob':'c'},{'path':'same','git_blob':'b'}]}
        self.assertEqual(m.delta(a,b),{'added':['new'],'removed':['old'],'changed':[],'unchanged':['same']})
