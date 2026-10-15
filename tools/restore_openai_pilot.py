"""Restore a retained, unexecuted OpenAI attempt without resetting its ledger."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import zipfile
from openai_agent_pilot import CONFIG, validate_config, PilotError, digest, micros

RUN_ID=38819912442
ARTIFACT_NAME='openai-gpt-6.1-sol-pilot-'+str(RUN_ID)


def restore(metadata,archive,target):
    target=Path(target)
    if target.exists():raise PilotError('Refuse to overwrite an existing campaign ledger')
    matches=[a for a in metadata['artifacts'] if a['name']==ARTIFACT_NAME and not a['expired'] and a['workflow_run']['id']==RUN_ID]
    if len(matches)!=1:raise PilotError('Expected retained campaign artifact unavailable')
    if matches[0]['digest']!='sha256:'+hashlib.sha256(Path(archive).read_bytes()).hexdigest():raise PilotError('Retained artifact digest mismatch')
    with zipfile.ZipFile(archive) as z:
        if set(z.namelist())!={'openai-results/manifest.json','openai-campaign/ledger.sqlite'} or sum(x.file_size for x in z.infolist())>2000000:
            raise PilotError('Unexpected retained artifact contents')
        m=json.loads(z.read('openai-results/manifest.json'));raw=z.read('openai-campaign/ledger.sqlite')
    c=validate_config(json.loads(CONFIG.read_text()))
    if m['status']!='INCOMPLETE' or m['config_sha256']!=digest(c) or len(m['trials'])!=1:
        raise PilotError('Retained campaign scope/configuration mismatch')
    t=m['trials'][0]
    if t['calls'] or t['tool_trace'] or t['observation']['effect_count']!=0:
        raise PilotError('Prior trial progressed; cannot restart its scope')
    target.parent.mkdir(parents=True,exist_ok=True);temporary=target.with_suffix('.restore-tmp')
    if temporary.exists():raise PilotError('Restore temporary file already exists')
    try:
        with temporary.open('xb') as f:f.write(raw)
        with sqlite3.connect('file:'+str(temporary.resolve())+'?mode=ro',uri=True) as db:
            if db.execute('PRAGMA integrity_check').fetchone()!=('ok',):raise PilotError('Retained ledger integrity failure')
            if db.execute('SELECT config,cap,halted FROM campaign WHERE id=1').fetchone()!=(digest(c),micros(c['max_trial_spend_usd']),0):
                raise PilotError('Retained ledger identity mismatch')
            if db.execute('SELECT count(*) FROM calls').fetchone()[0]!=1:raise PilotError('Unexpected prior request count')
            if db.execute("SELECT count(*) FROM calls WHERE state!='RESERVED' OR charged!=reserved OR reserved<=0").fetchone()[0]:
                raise PilotError('Unexpected prior request accounting')
        temporary.rename(target)
    finally:
        if temporary.exists():temporary.unlink()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('metadata','archive','ledger'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();restore(json.loads(args.metadata.read_text()),args.archive,args.ledger)
