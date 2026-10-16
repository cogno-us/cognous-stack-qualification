"""Matched synthetic refund stimulus using native Cognous atomic authority/effect APIs.

Apache-2.0. The account trigger is a TEST-ONLY destination adapter. It does not
replace native claim checks or commit logic. No payment/network/model is used.
"""
from __future__ import annotations
import argparse
from contextlib import closing
import dataclasses
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from xml.etree import ElementTree

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from pristine_checkout import require_pristine

VARIANTS=('valid','revoked','approval-withdrawn','policy-changed','evidence-stale',
          'lost-ack-reconcile','duplicate-redelivery','observer-unavailable',
          'changed-consequence','new-consequence-no-fresh-claim')


def check(value,message):
    if not value:raise ValueError(message)


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')


def readback(path):
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        db.row_factory=sqlite3.Row
        try:db.execute('CREATE TABLE observer_write_must_fail(x)')
        except sqlite3.OperationalError as exc:check('readonly' in str(exc).lower(),'Observer probe failed unexpectedly')
        else:raise ValueError('Observer can write')
        tables={}
        for row in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
            name=row['name'];quoted='"'+name.replace('"','""')+'"'
            tables[name]=[dict(r) for r in db.execute('SELECT * FROM '+quoted+' ORDER BY rowid')]
    return {'tables':tables,'account':tables['account'][0],'effects':tables['effects'],
            'attempts':tables['attempts'],'writer_effects':tables['writer_effects'],
            'observer':'separate Python process; SQLite mode=ro; same trusted OS account',
            'read_only_verified':True,'operational_independence':False,
            'horizon':'after synchronous native operations; no asynchronous or external writer'}


def observe(path):
    env={k:v for k,v in os.environ.items() if not k.startswith('PYTHON')}
    env['PYTHONDONTWRITEBYTECODE']='1'
    return json.loads(subprocess.check_output([sys.executable,__file__,'--observe',str(path)],env=env,text=True,timeout=30))


def backup(source,target):
    with closing(sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True)) as src:
        with closing(sqlite3.connect(target)) as dest:
            src.backup(dest);dest.execute('PRAGMA journal_mode=DELETE')
            check(dest.execute('PRAGMA integrity_check').fetchone()[0]=='ok','Snapshot integrity')


ADAPTER_SQL='''
CREATE TABLE account(resource TEXT PRIMARY KEY,balance_cents INTEGER NOT NULL,version INTEGER NOT NULL);
CREATE TABLE writer_effects(effect_id TEXT PRIMARY KEY,before_cents INTEGER,after_cents INTEGER,before_version INTEGER,after_version INTEGER);
CREATE TRIGGER matched_refund_guard BEFORE INSERT ON effects BEGIN
 SELECT CASE WHEN NEW.target != (SELECT resource FROM account)
 OR NEW.unit != 'USD' OR NEW.amount*100 != json_extract(NEW.payload_json,'$.refund_cents')
 OR json_extract(NEW.payload_json,'$.currency') != 'USD'
 OR json_extract(NEW.payload_json,'$.effect_id') != NEW.effect_id
 OR json_extract(NEW.payload_json,'$.expected_state_version') != (SELECT version FROM account)
 OR (SELECT balance_cents FROM account) < json_extract(NEW.payload_json,'$.refund_cents')
 THEN RAISE(ABORT,'matched refund precondition failed') END;
END;
CREATE TRIGGER matched_refund_write AFTER INSERT ON effects BEGIN
 UPDATE account SET balance_cents=balance_cents-CAST(ROUND(NEW.amount*100) AS INTEGER),version=version+1 WHERE resource=NEW.target;
 INSERT INTO writer_effects SELECT NEW.effect_id,balance_cents+CAST(ROUND(NEW.amount*100) AS INTEGER),balance_cents,version-1,version FROM account WHERE resource=NEW.target;
END;
'''


def run(runtime,control,fixture_path,output):
    fixture=json.loads(fixture_path.read_text())
    common={'account':fixture['initial_state']['account'],'params':fixture['params'],'simulation_clock':fixture['simulation_clock']}
    check(common['account']=={'resource':'synthetic-wallet:refund-demo-001','balance_cents':10000,'version':1},'Unmatched initial account')
    check(common['params']=={'currency':'USD','effect_id':'effect:synthetic-refund-001','expected_state_version':1,'refund_cents':1000},'Unmatched action')
    sources={}
    for name,path in [('runtime',runtime),('control_plane',control),('qualification',ROOT)]:
        revision=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
        require_pristine(path,revision,name)
        sources[name]={'commit':revision,'tree':subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD^{tree}'],text=True).strip(),'pristine':True}
    sys.path[:0]=[str(runtime),str(control/'src')]
    spec=importlib.util.spec_from_file_location('native_atomic_fixture',ROOT/'suites/cognous-execution-runtime/tests/test_local_authority_effect.py')
    helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
    from engine.safe_executor import ExecutionEnvelope,LocalExecutionPolicy,commitment,snapshot_envelope
    from engine.local_authority_effect import AtomicAuthorityEffectDestination,AtomicLocalControlPlaneExecutor
    from engine.producer_contract import export_execution_artifacts
    base=datetime.fromisoformat(common['simulation_clock']['issued'].replace('Z','+00:00'))
    helpers.BASE=base
    output.mkdir(parents=True,exist_ok=False)
    write(output/'fixture.json',{'common_stimulus':common,'source_fixture_sha256':hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
          'authority':'Cognous local claim fixture, not SCQOS PERMIT or institutional adoption','adapter':'test-only SQLite triggers over native effects; same transaction',
          'native_profile':'local-authority-effect:0.1.0-proposed; opt-in, nonselected'})
    (output/'account-adapter.sql').write_text(ADAPTER_SQL)
    cases=[]
    suite=ElementTree.Element('testsuite',name='matched-synthetic-refund',tests=str(len(VARIANTS)*2),failures='0',errors='0',skipped='0')
    for variant in VARIANTS:
        for repetition in (1,2):
            trial=output/'trials'/f'{variant}-{repetition}';trial.mkdir(parents=True)
            state=trial/'state';trace=[];clock=helpers.MutableClock(base)
            class CapturedDestination(AtomicAuthorityEffectDestination):
                def _transaction_stage(self,stage):trace.append({'sequence':len(trace)+1,'native_transaction_stage':stage})
            payload=dict(common['params'])
            op=dataclasses.replace(helpers.operation(),target=common['account']['resource'],payload=payload,
                  payload_commitment=commitment(payload),amount=10.0,unit='USD',action_id='synthetic.refund',adapter_id='cognous:matched-sqlite-refund')
            env=ExecutionEnvelope('0.2.0','decision:matched-refund',common['params']['effect_id'],op,'attempt:d04:001')
            dest=CapturedDestination(state,clock=clock)
            claim=helpers.make_claim(env,claim_id='claim:matched-refund',budget_id='budget:matched-refund')
            dest.provision_claim(claim)
            with closing(dest._connect()) as db:
                db.executescript(ADAPTER_SQL)
                db.execute('INSERT INTO account VALUES(?,?,?)',(common['account']['resource'],10000,1))
            policy=LocalExecutionPolicy(frozenset({op.institution_id}),frozenset({op.authority_domain}),frozenset({op.adapter_id}),frozenset({op.action_id}),
                                        (common['account']['resource'],),frozenset({'USD'}),10.0,1)
            executor=AtomicLocalControlPlaneExecutor(workflow=object(),destination=dest,policy=policy)
            initial=observe(dest.path);backup(dest.path,trial/'initial.db')
            write(trial/'claim.json',claim.model_dump(mode='json'));write(trial/'envelope.json',dataclasses.asdict(snapshot_envelope(env)))
            trace.append({'sequence':len(trace)+1,'checkpoint':'claim issued and baseline observed; before intervention/dispatch'})
            if variant=='revoked':dest.set_grant_status(claim.grant_id,status='revoked')
            elif variant=='approval-withdrawn':dest.set_approval_status(helpers.APPROVAL,status='revoked')
            elif variant=='policy-changed':dest.set_policy_state(helpers.POLICY_REF,version='2')
            elif variant=='evidence-stale':dest.set_evidence_state(helpers.EVIDENCE,state='stale')
            if variant=='changed-consequence':
                modified={**payload,'refund_cents':1100}
                env=dataclasses.replace(env,operation=dataclasses.replace(op,payload=modified,payload_commitment=commitment(modified),amount=11.0))
            if variant in ('revoked','approval-withdrawn','policy-changed','evidence-stale'):
                trace.append({'sequence':len(trace)+1,'checkpoint':'authoritative intervention committed before native admission'})
                write(trial/'after-intervention.json',observe(dest.path))
            clock.value=datetime.fromisoformat(common['simulation_clock']['committed'].replace('Z','+00:00'))
            lost=variant in ('lost-ack-reconcile','observer-unavailable')
            first=executor.execute(envelope=env,claim_id=claim.claim_id,attempt_id='attempt:d04:001',simulate='lost_ack' if lost else None)
            outcomes=[dataclasses.asdict(first)];post=observe(dest.path)
            transport={'first_acknowledgement':'ACK_UNKNOWN' if lost else ('ACK_RECEIVED' if first.acknowledged else 'NOT_DISPATCHED'),
                       'first_attempt_id':first.attempt_id,'second_attempt_id':None,'reconciliation':None,
                       'native_executor_post_timeout_observation':first.observed_state if lost else None,
                       'independent_observer_unavailable':variant=='observer-unavailable'}
            if lost:
                check(first.status=='unknown' and not first.acknowledged,'Lost acknowledgement not preserved')
                write(trial/'post_commit_readback.json',post);backup(dest.path,trial/'post_commit.db')
                before_trace=len(trace)
                reopened=CapturedDestination(state,clock=clock)
                retry=AtomicLocalControlPlaneExecutor(workflow=object(),destination=reopened,policy=policy)
                snap=snapshot_envelope(env);attempt=reopened.begin_attempt('attempt:d04:002',snap)
                transport['second_attempt_id']=attempt
                if variant=='observer-unavailable':
                    # Fault injected at the independent-observation route. No redispatch fallback.
                    reopened.transition_attempt(attempt,'unknown','independent_observer_unavailable')
                    transport['reconciliation']='INCONCLUSIVE';transport['writer_invoked_on_second_attempt']=False
                else:
                    recovery=retry.reconcile(claim_id=claim.claim_id,envelope=env)
                    reopened.transition_attempt(attempt,'reconciled')
                    outcomes.append(dataclasses.asdict(recovery));transport['reconciliation']=recovery.observed_state
                    check(recovery.observed_state=='applied' and recovery.observation['retry_eligible'] is False,'Reconciliation did not establish applied/nonretryable')
                    transport['writer_invoked_on_second_attempt']=len(trace)!=before_trace
                    check(not transport['writer_invoked_on_second_attempt'],'Reconcile entered native effect transaction')
                dest=reopened
            elif variant in ('duplicate-redelivery','new-consequence-no-fresh-claim'):
                if variant=='new-consequence-no-fresh-claim':
                    dest.set_grant_status(claim.grant_id,status='revoked')
                    newer={**payload,'effect_id':'effect:synthetic-refund-002','expected_state_version':2}
                    env=dataclasses.replace(env,effect_id=newer['effect_id'],operation=dataclasses.replace(op,payload=newer,payload_commitment=commitment(newer)))
                second=executor.execute(envelope=env,claim_id=claim.claim_id,attempt_id='attempt:d04:002')
                outcomes.append(dataclasses.asdict(second));check(second.status=='denied','Consumed claim was reused')
            final=observe(dest.path);backup(dest.path,trial/'synthetic-refund.db')
            denied=variant in ('revoked','approval-withdrawn','policy-changed','evidence-stale','changed-consequence')
            check(first.status==('denied' if denied else 'unknown' if lost else 'executed'),'Native outcome')
            check(final['account']=={**common['account'],'balance_cents':10000 if denied else 9000,'version':1 if denied else 2},'Destination balance/version')
            check(len(final['effects'])==len(final['writer_effects'])==(0 if denied else 1),'Effect or writer multiplicity')
            check(len([e for e in trace if e.get('native_transaction_stage')=='after_commit'])==(0 if denied else 1),'Commit ordering/count')
            if lost:check(len(final['attempts'])==2 and final['attempts'][0]['attempt_id']!=final['attempts'][1]['attempt_id'],'Distinct native attempt records')
            consumed=sum(r['state']=='consumed' for r in final['tables']['execution_claims_v1'])
            check(consumed==(0 if denied else 1),'Authorization consumption count')
            write(trial/'initial.json',initial);write(trial/'observation.json',final);write(trial/'transport.json',transport)
            write(trial/'execution-results.json',outcomes);write(trial/'transaction-trace.json',trace)
            try:write(trial/'native-executor-export.json',export_execution_artifacts(env,first,dest,repository_revision=sources['runtime']['commit']))
            except (ValueError,PermissionError) as exc:write(trial/'native-export-gap.json',{'status':'UNSUPPORTED','reason':str(exc)})
            case={'variant':variant,'repetition':repetition,'verdict':'PASS','scenario_id':'D01' if variant=='valid' else 'D03' if variant in ('revoked','approval-withdrawn','policy-changed','evidence-stale') else 'D04',
                  'effect_count':len(final['effects']),'balance_cents':final['account']['balance_cents'],'state_version':final['account']['version'],
                  'observation_verdict':'INCONCLUSIVE' if variant=='observer-unavailable' else 'OBSERVED','assertion_scope':'named synthetic assertion; not whole catalog acceptance'}
            cases.append(case);ElementTree.SubElement(suite,'testcase',classname=variant,name=str(repetition))
    loaded={}
    for module in list(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename:
            path=Path(filename).resolve()
            for name,root in [('runtime',runtime),('control_plane',control),('qualification',ROOT)]:
                if path.is_relative_to(root) and path.is_file():loaded[name+'/'+path.relative_to(root).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    loaded['qualification/tools/run_matched_refund.py']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for name,path in [('runtime',runtime),('control_plane',control),('qualification',ROOT)]:require_pristine(path,sources[name]['commit'],name)
    summary={'profile':'matched-synthetic-refund/1; native local atomic profile, nonselected','sources':sources,'loaded_files':loaded,'common_stimulus':common,
             'cases':cases,'counts':{'PASS':len(cases)},'comparison':'matched business stimulus and fault; SCQOS arm supplied, not rerun',
             'limits':['Test-only SQL account adapter; not built-in production account management','Same-host cooperating authority/SQLite only','Observer separate read-only process, same trusted OS account',
                       'Authority claims issued by trusted test fixture, not live institutional workflow','D04 native executor immediately observes after timeout; transport acknowledgement still UNKNOWN',
                       'Second recovery attempt journal created by harness via native begin_attempt/transition APIs; native reconcile creates no attempt automatically',
                       'No process kill, financial finality, distributed atomicity or model calls','Replay/Evidence Pack consumer interoperability not claimed'],
             'executed_at':datetime.now(timezone.utc).isoformat(),'release_authorized':False,'production_authorized':False}
    write(output/'summary.json',summary)
    ElementTree.ElementTree(suite).write(output/'test-results.xml',encoding='utf-8',xml_declaration=True)
    print(json.dumps({'counts':summary['counts'],'sources':sources,'output':str(output)},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observe',type=Path)
    for name in ('runtime','control','fixture','output'):parser.add_argument('--'+name,type=Path)
    args=parser.parse_args()
    if args.observe:print(json.dumps(readback(args.observe)));raise SystemExit(0)
    check(all(getattr(args,name) for name in ('runtime','control','fixture','output')),'--runtime --control --fixture --output required')
    run(args.runtime.resolve(),args.control.resolve(),args.fixture.resolve(),args.output.resolve())
