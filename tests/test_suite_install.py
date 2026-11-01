"""Failure and identity checks for relocating tests into disposable source trees."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('install_suite',Path(__file__).resolve().parents[1]/'tools/install_suite.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class SuiteInstall(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.source=self.root/'source';self.qual=self.root/'qualification'
        for p in (self.source,self.qual):
            p.mkdir();self.git(p,'init','-q');(p/'README').write_text('Synthetic repository\n');self.commit(p)
        self.relative='suites/fixture/tests/test_fixture.py'
        self.canonical=self.qual/self.relative;self.canonical.parent.mkdir(parents=True)
        self.canonical.write_text('def test_fixture():\n    assert 1 == 1\n')
        self.hash=hashlib.sha256(self.canonical.read_bytes()).hexdigest()
        self.manifest=self.qual/'migration.json'
        self.data={'repositories':{'fixture':{'repository':'synthetic/fixture','source_commit':self.git(self.source,'rev-parse','HEAD').strip(),'files':[{'source_path':'tests/test_fixture.py','destination_path':self.relative,'destination_sha256':self.hash,'source_sha256':self.hash,'source_url':'https://example.invalid/source','license':'Apache-2.0','action':'move'}]}}}
        self.save();self.commit(self.qual);self.evidence=self.root/'results/identity.json'

    def git(self,root,*args):
        return subprocess.check_output(['git','-C',str(root),*args],text=True,stderr=subprocess.DEVNULL)
    def commit(self,root):
        self.git(root,'add','.');self.git(root,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture')
    def save(self):self.manifest.write_text(json.dumps(self.data))
    def run_install(self,**kw):return module.install('fixture',self.source,evidence=self.evidence,manifest=self.manifest,qualification_root=self.qual,**kw)

    def test_retains_both_git_identities_and_test_bytes(self):
        report=self.run_install()
        self.assertEqual(report['owning_source_commit'],self.git(self.source,'rev-parse','HEAD').strip())
        self.assertEqual(report['qualification_commit'],self.git(self.qual,'rev-parse','HEAD').strip())
        self.assertEqual((self.source/'tests/test_fixture.py').read_bytes(),self.canonical.read_bytes())
        self.assertEqual(report['overlay'][0]['sha256'],self.hash)
        self.assertEqual(report['qualification_claim'],'NONE: assembly is not execution or acceptance')
    def test_refuses_changed_canonical_test(self):
        self.canonical.write_text('assert False\n')
        with self.assertRaisesRegex(ValueError,'differs from migration record'):self.run_install()
        self.assertFalse((self.source/'tests/test_fixture.py').exists())
    def test_refuses_newer_source_test(self):
        target=self.source/'tests/test_fixture.py';target.parent.mkdir();target.write_text('assert False\n')
        with self.assertRaisesRegex(ValueError,'advanced after inventory'):self.run_install()
        self.assertEqual(target.read_text(),'assert False\n')
    def test_accepts_only_explicitly_reconciled_source_bytes(self):
        target=self.source/'tests/test_fixture.py';target.parent.mkdir()
        target.write_text('def test_fixture():\n    assert 2 == 2\n')
        self.data['repositories']['fixture']['files'][0]['reconciled_sources']=[{
            'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}]
        self.save()
        self.run_install()
        self.assertEqual(target.read_bytes(),self.canonical.read_bytes())

    def test_refuses_symlink_escape(self):
        outside=self.root/'outside';outside.mkdir();(self.source/'tests').symlink_to(outside,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'Symlink'):self.run_install()
        self.assertFalse((outside/'test_fixture.py').exists())
    def test_refuses_path_traversal(self):
        self.data['repositories']['fixture']['files'][0]['source_path']='../escape.py';self.save()
        with self.assertRaisesRegex(ValueError,'Unsafe migration path'):self.run_install()
    def test_historical_source_is_recorded_without_replacement(self):
        report=self.run_install(historical_only=True)
        self.assertTrue(report['historical_frozen_source']);self.assertEqual(report['overlay'],[])
        self.assertFalse((self.source/'tests/test_fixture.py').exists())
    def test_cannot_overwrite_prior_evidence(self):
        self.evidence.parent.mkdir();self.evidence.write_text('prior evidence')
        with self.assertRaisesRegex(ValueError,'already exists'):self.run_install()
        self.assertEqual(self.evidence.read_text(),'prior evidence')

    def test_dependency_locks_are_copied_byte_for_byte_and_recorded(self):
        locks=self.qual/'.github/locks';locks.mkdir(parents=True)
        (locks/'tools-aaaaaa.txt').write_text('pytest==9.0.0 \\\n    --hash=sha256:00\n');(locks/'tools-aaaaaa.in').write_text('pytest\n');(locks/'notes.md').write_text('ignored\n')
        copied=module.provision_dependency_locks(self.source,self.qual)
        self.assertEqual([x['path'] for x in copied],['.github/locks/tools-aaaaaa.in','.github/locks/tools-aaaaaa.txt'])
        for item in copied:
            self.assertEqual(hashlib.sha256((self.source/item['path']).read_bytes()).hexdigest(),item['sha256'])
            self.assertEqual((self.source/item['path']).read_bytes(),(self.qual/item['path']).read_bytes())
        self.assertFalse((self.source/'.github/locks/notes.md').exists())
        self.assertEqual(module.provision_dependency_locks(self.source,self.qual),copied)
    def test_dependency_lock_with_different_bytes_is_never_overwritten(self):
        locks=self.qual/'.github/locks';locks.mkdir(parents=True);(locks/'tools-aaaaaa.txt').write_text('canonical\n')
        existing=self.source/'.github/locks';existing.mkdir(parents=True);(existing/'tools-aaaaaa.txt').write_text('other\n')
        with self.assertRaisesRegex(ValueError,'differs from the qualification lock'):module.provision_dependency_locks(self.source,self.qual)
        self.assertEqual((existing/'tools-aaaaaa.txt').read_text(),'other\n')
    def test_dependency_locks_absent_is_a_no_op(self):
        self.assertEqual(module.provision_dependency_locks(self.source,self.qual),[])
        self.assertFalse((self.source/'.github').exists())
    def test_dependency_locks_refuse_a_symlinked_destination(self):
        locks=self.qual/'.github/locks';locks.mkdir(parents=True);(locks/'tools-aaaaaa.txt').write_text('canonical\n')
        outside=self.root/'outside';outside.mkdir();(self.source/'.github').symlink_to(outside,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'Symlink'):module.provision_dependency_locks(self.source,self.qual)
        self.assertEqual(list(outside.iterdir()),[])


if __name__=='__main__':unittest.main()
