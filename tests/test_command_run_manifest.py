"""Exercise subprocess failure/timeout retention without an integration environment."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import run_suite


class CommandRuns(unittest.TestCase):
    def fixture(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name)
        source=root/'source';source.mkdir();qual=root/'qual';qual.mkdir()
        for p in (source,qual):
            subprocess.run(['git','-C',str(p),'init','-q'],check=True)
            (p/'README').write_text('Unit-test fixture; not an integration result.\n')
        path=qual/'migrations/cross-component-2026-10-15.json';path.parent.mkdir();path.write_text(json.dumps({'repositories':{'fixture':{'repository':'cogno-us/cognous-open-control-stack'}}}))
        for p in (source,qual):
            subprocess.run(['git','-C',str(p),'add','.'],check=True)
            subprocess.run(['git','-C',str(p),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture'],check=True)
        return root,source,qual
    def execute(self,command,timeout=5,setup_failure=False):
        root,source,qual=self.fixture();out=root/'out'
        def assembly(suite,src,evidence):
            if setup_failure:raise ValueError('deliberate fixture assembly refusal')
            value={'source_status_before_assembly':'','migration_manifest_sha256':'a'*64};evidence.write_text(json.dumps(value));return value
        argv=['run_suite.py','--suite','fixture','--source-root',str(source),'--results-dir',str(out),'--timeout',str(timeout),'--',sys.executable,'-c',command]
        with patch.object(run_suite,'ROOT',qual),patch.object(run_suite,'install',side_effect=assembly),patch.object(sys,'argv',argv):code=run_suite.main()
        return code,json.loads((out/'manifest.json').read_text()),out
    def test_failed_command_preserves_output_and_manifest(self):
        code,r,out=self.execute('print("deliberate fixture failure",flush=True); raise SystemExit(7)')
        self.assertEqual(code,7);self.assertEqual(r['execution']['outcome'],'FAIL');self.assertEqual(r['scenario_results'],[]);self.assertIn('deliberate fixture failure',(out/'execution.log').read_text())
    def test_timeout_retains_log_and_explicit_failure(self):
        code,r,out=self.execute('import time; print("fixture started",flush=True); time.sleep(30)',timeout=1)
        self.assertEqual(code,124);self.assertTrue(r['execution']['timed_out']);self.assertEqual(r['execution']['outcome'],'FAIL');self.assertIn('fixture started',(out/'execution.log').read_text())
    def test_setup_failure_retains_inconclusive_without_pass(self):
        code,r,out=self.execute('raise SystemExit(0)',setup_failure=True)
        self.assertEqual(code,2);self.assertEqual(r['execution']['outcome'],'INCONCLUSIVE');self.assertEqual(r['execution']['stage'],'setup');self.assertFalse((out/'execution.log').exists())
    def test_success_is_command_only(self):
        code,r,out=self.execute('print("fixture complete")')
        self.assertEqual(code,0);self.assertEqual(r['execution']['outcome'],'PASS');self.assertEqual(r['scenario_results'],[]);self.assertEqual(r['component_set']['completeness'],'UNVERIFIED')


if __name__=='__main__':unittest.main()
