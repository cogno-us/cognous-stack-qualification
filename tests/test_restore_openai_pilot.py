"""Offline restoration controls with generated evidence; no provider request."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import openai_agent_pilot as pilot
from restore_openai_pilot import restore,RUN_ID,ARTIFACT_NAME


class RestoreTests(unittest.TestCase):
    def fixture(self,progress=False):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup);root=Path(folder.name)
        c=pilot.validate_config(json.loads(pilot.CONFIG.read_text()))
        ledger=pilot.OpenAILedger(root/'original.sqlite',c);ledger.reserve(70480)
        m={'status':'INCOMPLETE','config_sha256':pilot.digest(c),'trials':[{'calls':[{}] if progress else [],'tool_trace':[],'observation':{'effect_count':0}}]}
        archive=root/'prior.zip'
        with zipfile.ZipFile(archive,'w') as z:
            z.writestr('openai-results/manifest.json',json.dumps(m));z.write(ledger.path,'openai-campaign/ledger.sqlite')
        metadata={'artifacts':[{'name':ARTIFACT_NAME,'expired':False,'workflow_run':{'id':RUN_ID},'digest':'sha256:'+hashlib.sha256(archive.read_bytes()).hexdigest()}]}
        return root,metadata,archive,c

    def test_restore_preserves_reservation_and_cannot_overwrite(self):
        root,metadata,archive,c=self.fixture();target=root/'next/ledger.sqlite'
        restore(metadata,archive,target)
        self.assertEqual(pilot.OpenAILedger(target,c).summary()['charged_or_reserved_usd'],'0.07048')
        self.assertEqual(target.read_bytes(),(root/'original.sqlite').read_bytes())
        with self.assertRaises(pilot.PilotError):restore(metadata,archive,target)

    def test_digest_or_origin_substitution_fails_before_copy(self):
        for change in ('digest','origin'):
            root,metadata,archive,c=self.fixture()
            if change=='digest':metadata['artifacts'][0]['digest']='sha256:wrong'
            else:metadata['artifacts'][0]['workflow_run']['id']=1
            with self.subTest(change=change),self.assertRaises(pilot.PilotError):restore(metadata,archive,root/'restored.sqlite')
            self.assertFalse((root/'restored.sqlite').exists())

    def test_progressed_trial_cannot_be_silently_restarted(self):
        root,metadata,archive,c=self.fixture(progress=True)
        with self.assertRaisesRegex(pilot.PilotError,'progressed'):restore(metadata,archive,root/'restored.sqlite')
