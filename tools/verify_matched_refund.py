"""Portable stdlib-only verification of the matched monetary refund evidence.

Apache-2.0. Snapshot consistency is not signer authentication or rerun of the assessed architecture.
"""
from contextlib import closing
import hashlib
import json
from pathlib import Path,PurePosixPath
import sqlite3
import sys
from xml.etree import ElementTree


def check(value,message):
    if not value:raise ValueError(message)


def strict_pairs(items):
    result={}
    for key,value in items:
        check(key not in result,'Duplicate JSON key');result[key]=value
    return result


def load(path):
    def invalid(value):raise ValueError('Nonfinite JSON')
    return json.loads(path.read_text(),object_pairs_hook=strict_pairs,parse_constant=invalid)


def digest(value):
    return 'sha256:'+hashlib.sha256(json.dumps(value,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def database(path):
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)) as db:
        db.row_factory=sqlite3.Row;check(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','Database integrity')
        return {r['name']:[dict(x) for x in db.execute('SELECT * FROM "'+r['name'].replace('"','""')+'" ORDER BY rowid')]
                for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")}


def verify(root):
    root=Path(root).resolve();manifest=load(root/'manifest.json')
    check(manifest['format']=='cognous-matched-refund/1','Format')
    indexed={}
    for record in manifest['artifacts']:
        name=record['file'];p=PurePosixPath(name)
        check(not p.is_absolute() and '..' not in p.parts and '\\' not in name and str(p)==name and name not in ('.','manifest.json'),'Unsafe path')
        check(name not in indexed,'Duplicate artifact');indexed[name]=record
    files=set()
    for path in root.rglob('*'):
        check(not path.is_symlink(),'Symlink')
        if path.is_file() and path!=root/'manifest.json':files.add(path.relative_to(root).as_posix())
    check(files==set(indexed),'Missing or extra file')
    for name,record in indexed.items():
        data=(root/name).read_bytes();check(len(data)==record['bytes'] and hashlib.sha256(data).hexdigest()==record['sha256'],'Artifact hash: '+name)
        if name.endswith('.json'):load(root/name)
    summary=load(root/'native/summary.json');common=summary['common_stimulus']
    check(common['account']=={'balance_cents':10000,'version':1,'resource':'synthetic-wallet:refund-demo-001'},'Unmatched initial state')
    check(common['params']=={'currency':'USD','effect_id':'effect:synthetic-refund-001','expected_state_version':1,'refund_cents':1000},'Unmatched action')
    check(manifest['sources']==summary['sources'] and manifest['selected'] is False,'Source/profile binding')
    expected={(v,i) for v in ('valid','revoked','approval-withdrawn','policy-changed','evidence-stale','lost-ack-reconcile','duplicate-redelivery','observer-unavailable','changed-consequence','new-consequence-no-fresh-claim') for i in (1,2)}
    seen=set()
    for case in summary['cases']:
        key=(case['variant'],case['repetition']);check(key in expected and key not in seen,'Trial identity');seen.add(key)
        trial=root/'native/trials'/f'{key[0]}-{key[1]}'
        final=database(trial/'synthetic-refund.db');initial=database(trial/'initial.db')
        observation=load(trial/'observation.json');start=load(trial/'initial.json')
        check(initial==start['tables'] and final==observation['tables'],'Readback/database mismatch')
        for observed in (start,observation):
            check(observed['account']==observed['tables']['account'][0] and observed['effects']==observed['tables']['effects'] and observed['attempts']==observed['tables']['attempts'] and observed['writer_effects']==observed['tables']['writer_effects'],'Readback projection')
            check(observed['read_only_verified'] is True and observed['operational_independence'] is False,'Observer scope')
        check(initial['account']==[common['account']] and not initial['effects'],'Initial business state')
        denied=key[0] in ('revoked','approval-withdrawn','policy-changed','evidence-stale','changed-consequence')
        expected_account={**common['account'],'balance_cents':10000 if denied else 9000,'version':1 if denied else 2}
        check(final['account']==[expected_account],'Balance/version')
        check(len(final['effects'])==len(final['writer_effects'])==(0 if denied else 1),'Effect/writer cardinality')
        check(sum(c['state']=='consumed' for c in final['execution_claims_v1'])==(0 if denied else 1),'Claim consumption')
        results=load(trial/'execution-results.json');transport=load(trial/'transport.json');trace=load(trial/'transaction-trace.json')
        lost=key[0] in ('lost-ack-reconcile','observer-unavailable')
        check(results[0]['status']==('denied' if denied else 'unknown' if lost else 'executed'),'Native outcome')
        check(len([e for e in trace if e.get('native_transaction_stage')=='after_commit'])==(0 if denied else 1),'Commit trace')
        if final['effects']:
            effect=final['effects'][0];check(effect['effect_id']==common['params']['effect_id'] and effect['target']==common['account']['resource'] and effect['amount']==10 and effect['unit']=='USD','Effect binding')
            payload=json.loads(effect['payload_json']);check(payload==common['params'],'Effect payload')
            export=load(trial/'native-executor-export.json');operation=export['execution_envelope']['operation']
            check(digest(operation)==effect['operation_digest'] and digest(payload)==operation['payload_commitment'],'Native operation commitment')
            check(operation['proposal_commitment']==digest(common),'Common proposal commitment')
            writer=final['writer_effects'][0]
            check(writer=={'effect_id':common['params']['effect_id'],'before_cents':10000,'after_cents':9000,'before_version':1,'after_version':2},'Writer state transition')
            check(export['effects']==final['effects'] and export['attempts']==final['attempts'],'Native producer export correlations')
        if lost:
            check(transport['first_acknowledgement']=='ACK_UNKNOWN' and results[0]['acknowledged'] is False,'Historical UNKNOWN')
            check(len(final['attempts'])==2 and {r['attempt_id'] for r in final['attempts']}=={'attempt:d04:001','attempt:d04:002'},'Distinct native attempts')
            committed=database(trial/'post_commit.db');check(committed['effects']==final['effects'] and committed['account']==final['account'] and len(committed['attempts'])==1,'Postcommit/preretry state')
            check(transport['writer_invoked_on_second_attempt'] is False,'Second effect transaction invoked')
            if key[0]=='lost-ack-reconcile':
                check(transport['reconciliation']=='applied' and results[1]['attempted'] is False and results[1]['observation']['retry_eligible'] is False,'Read-only native reconciliation')
                check(case['observation_verdict']=='OBSERVED','Recovery observation verdict')
            else:
                check(transport['reconciliation']=='INCONCLUSIVE' and (trial/'observer-fault.json').is_file() and case['observation_verdict']=='INCONCLUSIVE','Missing observation promoted')
        if key[0] in ('duplicate-redelivery','new-consequence-no-fresh-claim'):check(results[1]['status']=='denied','Claim reused')
        check(case['verdict']=='PASS' and case['balance_cents']==expected_account['balance_cents'] and case['state_version']==expected_account['version'] and case['effect_count']==len(final['effects']),'Trial summary mismatch')
    check(seen==expected and summary['counts']=={'PASS':20},'Incomplete trial set')
    xml=ElementTree.parse(root/'test-results.xml').getroot()
    check(int(xml.attrib['tests'])==20 and xml.attrib['failures']=='0' and xml.attrib['errors']=='0','JUnit result')
    check({(t.attrib['classname'],int(t.attrib['name'])) for t in xml.findall('testcase')}==seen,'JUnit trial mapping')
    exemplar=root/'native/trials/lost-ack-reconcile-1'
    check(load(root/'transport.json')==load(exemplar/'transport.json') and load(root/'observation.json')==load(exemplar/'observation.json') and load(root/'post_commit_readback.json')==load(exemplar/'post_commit_readback.json'),'Root exemplar mapping')
    check(database(root/'synthetic-refund.db')==database(exemplar/'synthetic-refund.db'),'Root destination copy')
    return {'integrity':'PASS','matched_business_trials':20,'state_and_native_receipt_checks':'PASS',
            'lost_ack':'UNKNOWN preserved; distinct native recovery attempt; one effect',
            'scope':'nonselected local atomic profile with test-only account adapter; same-host observer',
            'assessed_architecture_reexecution':'NOT RUN','signer_authentication':'NOT VERIFIED BY THIS PORTABLE VERIFIER'}


if __name__=='__main__':
    try:
        check(len(sys.argv)==2,'usage: python verify_export.py <package-directory>')
        print(json.dumps(verify(sys.argv[1]),indent=2,sort_keys=True))
    except (ValueError,KeyError,TypeError,OSError,sqlite3.Error,ElementTree.ParseError) as exc:
        print('VERIFICATION FAILED: '+str(exc),file=sys.stderr);raise SystemExit(1)
