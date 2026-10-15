"""SEC01 preparation checks against real disposable Git repositories."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / 'suites/cognous-open-control-stack'
sys.path.insert(0, str(SUITE))
from tools.optional_execution_profile import validate_checkout, qualification_environment, prepare
import tools.optional_execution_profile as optional
from tools import merged_chain_qualification as merged
from tools import protected_qualification as protected


class CheckoutSecurity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.component = self.root/'component'; self.component.mkdir()
        self.git('init', '-q')
        (self.component/'source.py').write_text('value = 1\n')
        (self.component/'.gitignore').write_text('ignored.py\n')
        self.git('add', '.'); self.git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture')
        self.sha = self.git('rev-parse','HEAD').strip()
        self.lock = self.root/'component-lock.json'
        self.lock.write_text(json.dumps({'components':{'component':{'sha':self.sha}}}))
        self.profile = self.root/'profile.json'
        self.profile.write_text(json.dumps({'components':{'component':{'sha':self.sha}}}))

    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.component),*args],text=True)

    def run_optional(self):
        with patch.object(optional,'ROOT',self.root), patch.object(optional,'COMPONENTS',('component',)):
            return prepare(self.root)

    def run_merged(self):
        with patch.object(merged,'PROFILE',self.profile), patch.object(merged,'run',side_effect=AssertionError('child launched')), patch.object(sys,'argv',['merged','--batch','recovery','--work',str(self.root),'--out',str(self.root.parent/(self.root.name+'-out'))]):
            try: return merged.main()
            finally:
                import shutil
                shutil.rmtree(self.root.parent/(self.root.name+'-out'),ignore_errors=True)

    def test_clean_checkout_and_controlled_environment(self):
        self.git('checkout','--detach','-q',self.sha)
        self.assertEqual(validate_checkout(self.component,self.sha),self.sha)
        env,pins,_=self.run_optional(); self.assertEqual(pins,{'component':self.sha})
        with patch.dict(os.environ,{'PYTHONHOME':'/bad','PYTHONPATH':'/bad','PYTHONUSERBASE':'/bad','PYTHONSTARTUP':'/bad'}):
            env=qualification_environment()
        self.assertNotIn('PYTHONHOME',env);self.assertNotIn('PYTHONPATH',env)
        self.assertNotIn('PYTHONUSERBASE',env);self.assertNotIn('PYTHONSTARTUP',env)
        self.assertEqual(env['PYTHONNOUSERSITE'],'1')

    def test_untracked_ignored_staged_and_unstaged_refused_by_both_runners(self):
        for mode in ('untracked','ignored','staged','unstaged'):
            with self.subTest(mode=mode):
                if mode in ('untracked','ignored'):
                    path=self.component/('ignored.py' if mode=='ignored' else 'sentinel.py')
                    path.write_text("raise AssertionError('sentinel executed')\n")
                else:
                    path=self.component/'source.py';path.write_text('value = 2\n')
                    if mode=='staged':self.git('add','source.py')
                with self.assertRaises(RuntimeError):self.run_optional()
                with self.assertRaises(RuntimeError):self.run_merged()
                with patch.object(protected,'ROOT',self.root),patch.object(protected,'NAMES',('component',)):
                    with self.assertRaises(RuntimeError):protected.checkouts(self.root)
                if mode in ('untracked','ignored'):path.unlink()
                else:self.git('reset','--hard','-q',self.sha)

    def test_mismatched_revision_and_escaping_tracked_symlink(self):
        with self.assertRaises(RuntimeError):validate_checkout(self.component,'0'*40)
        (self.component/'escape.py').symlink_to(self.root/'outside.py')
        self.git('add','escape.py');self.git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','symlink')
        with self.assertRaisesRegex(RuntimeError,'symlink'):validate_checkout(self.component,self.git('rev-parse','HEAD').strip())

    def test_output_cannot_contaminate_reused_sources(self):
        with self.assertRaises(RuntimeError):optional.separate_output(self.component/'output',self.root)
        optional.separate_output(self.root.parent/'results',self.root)


if __name__=='__main__':unittest.main()
