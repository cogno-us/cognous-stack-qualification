"""Run frozen local variants against pristine hub native fixtures, without overlays.

SPDX-License-Identifier: Apache-2.0
No production effects, arbitrary callback tools or model requests are performed.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys
import tempfile
from trajectory_contract import ROOT, digest, file_digest, evaluate, calibrate, validate_record


def git(root, *args):
    return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()


def observe(path):
    """Separate process, read-only SQLite connection; same trusted OS account."""
    uri=path.resolve().as_uri()+'?mode=ro'
    with sqlite3.connect(uri, uri=True) as c:
        read_only=False
        try: c.execute("INSERT INTO effects(id) VALUES('observer-must-not-write')")
        except sqlite3.OperationalError as exc: read_only='readonly' in str(exc).lower()
        if not read_only: raise RuntimeError('Observer read-only negative control failed')
        c.row_factory=sqlite3.Row
        effects=[dict(r) for r in c.execute('SELECT * FROM effects ORDER BY id')]
        objects=[dict(r) for r in c.execute("SELECT * FROM objects WHERE kind NOT IN ('command','admin-sequence','checkpoint') ORDER BY kind,id")]
        return {'read_only_verified':read_only,'effect_count':len(effects),
                'payloads':[r['payload'] for r in effects], 'effects':effects, 'business_objects':objects,
                'business_digest':digest({'objects':objects,'effects':effects}),
                'observer':'separate process SQLite mode=ro; same trusted OS user',
                'consistency':'transaction snapshot after synchronous apply returned; no async writer in this fixture',
                'operational_independence':False}


def readback(path):
    env={k:v for k,v in os.environ.items() if not k.startswith('PYTHON')}
    env['PYTHONDONTWRITEBYTECODE']='1'
    raw=subprocess.check_output([sys.executable,str(Path(__file__).resolve()),'--observe',str(path)],env=env,text=True,timeout=20)
    return json.loads(raw)


def native_events(path):
    with sqlite3.connect(path) as c:
        return [{'seq':r[0],'body':json.loads(r[1]),'previous':r[2],'head':r[3]}
                for r in c.execute('SELECT seq,body,previous,head FROM events ORDER BY seq')]


def load_fixture(root, relative, name):
    sys.path[:0]=[str(root),str(root/'tests')]
    spec=importlib.util.spec_from_file_location(name,root/relative)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def source(root, files):
    status=git(root,'status','--porcelain','--untracked-files=all','--ignored=matching')
    if status: raise ValueError('Source must be pristine including ignored files: '+str(root))
    for path in files:
        if (root/path).is_symlink(): raise ValueError('Loaded symlink not supported')
    return {'commit':git(root,'rev-parse','HEAD'), 'dirty':False,
            'files':{p:file_digest(root/p) for p in files}}


def trial(variant, number, protected, integrated, out):
    approval=variant['id'].startswith('approval-')
    fixture=integrated.IntegratedAssuranceTests() if approval else protected.DestinationTests()
    fixture.setUp()
    try:
        initial=readback(fixture.path)
        if initial['effect_count'] != 0: raise ValueError('Reset leaked prior effect')
        responses=[];attempts=[]
        def dispatch(request, effect='effect', ack='RECEIVED'):
            identity=request.get('body',{}).get('id',request.get('body',{}).get('nonce','unknown'))
            result=fixture.runtime.apply(request);responses.append(result)
            attempts.append({'attempt_id':identity,'effect_id':effect,'acknowledgement':ack,'request_digest':digest(request)})
            return result
        name=variant['id']
        if approval:
            fixture.queue()
            if name=='approval-approve': fixture.approve();fixture.checkpoint()
            elif name=='approval-deny':
                p=fixture.get('proposal','proposal-1');fixture.ok('review','review',proposal='proposal-1',binding_digest=p['binding_digest'],disposition='reject')
            elif name=='approval-wrong-reviewer':
                p=fixture.get('proposal','proposal-1')
                responses.append(fixture.call('challenge','review',proposal='proposal-1',binding_digest=p['binding_digest'],disposition='approve'))
            elif name=='approval-modified-binding':
                p=fixture.get('proposal','proposal-1')
                responses.append(fixture.call('review','review',proposal='proposal-1',binding_digest='0'*64,disposition='approve'))
            elif name=='approval-expiry': fixture.approve();fixture.now=700
            elif name=='approval-withdrawal':
                fixture.approve();fixture.ok('challenge','challenge',id='withdrawal',proposal='proposal-1',reason_digest='0'*64)
                fixture.ok('review','resolve_challenge',challenge='withdrawal',disposition='accept',reason_digest='0'*64)
            elif name=='approval-cancel-before-commit':
                fixture.approve();fixture.ok('incident','stop',run='root',incident_digest='0'*64,detected_at=fixture.now)
            elif name=='approval-policy-changed':
                fixture.approve();fixture.ok('ops','environment',id='env',manifest=fixture.manifest,expires_at=1000,max_event_lag=500,max_checkpoint_age=1000)
            dispatch(fixture.request('agent','execute',{'proposal':'proposal-1'}),'effect-1')
        else:
            request=fixture.request('execute',fixture.args())
            if name=='revoked': fixture.ok('revoke',grant='grant')
            elif name=='expired': fixture.now=200;request=fixture.request('execute',fixture.args())
            elif name=='policy-substitution': request=fixture.request('execute',fixture.args(policy='wrong-policy'))
            elif name=='target-substitution': request=fixture.request('execute',fixture.args(target='wrong-target'))
            elif name=='actor-substitution': request=fixture.request('execute',fixture.args(),actor='agent')
            elif name=='stale-verifier': fixture.now=101
            elif name=='alternate-route': request=fixture.request('shell',{'command':'not-executed'})
            if name=='lost-ack-retry':
                dispatch(request,ack='UNKNOWN')
                # Native synchronous apply returned: commit completed before deliberate ACK discard.
                committed=readback(fixture.path)
                if committed['effect_count']!=1: raise ValueError('Fault was not after commit')
                fixture.runtime=protected.ProtectedDestination(fixture.path,clock=lambda:fixture.now,**fixture.config)
                request=fixture.request('execute',fixture.args())
            dispatch(request)
        observed=readback(fixture.path)
        # Native protected destination stores canonical JSON payload; integrated runtime stores text.
        if not approval: observed['payloads']=[json.loads(p) for p in observed['payloads']]
        case={'variant':name,'trial':number,'scenario_id':variant['scenario_id'],
              'execution':'EXECUTED','initial_business_digest':initial['business_digest'],
              'reset_verified':True,'initial_observation':initial,'responses':responses,'attempts':attempts,
              'events':native_events(fixture.path),'audit_expected':True,
              'observation':observed,
              'verdict_scope':'named local variant only; catalog acceptance unchanged'}
        case['result']=evaluate(case,variant['expected'])
        return case
    finally: fixture.doCleanups()


def run(hub, output, repetitions=None):
    plan=json.loads((ROOT/'qualification/serial/plan.json').read_text())
    if repetitions is not None: plan['repetitions']=repetitions
    hub_files=['reference_profiles/protected_destination.py','reference_profiles/trust_evidence.py',
               'reference_profiles/assurance_runtime.py','reference_profiles/bounded_json.py',
               'tests/test_protected_destination.py','tests/test_integrated_assurance.py','component-lock.json']
    own_files=['tools/run_serial_qualification.py','tools/trajectory_contract.py','qualification/serial/plan.json',
               'schemas/trajectory-evidence-v2.schema.json','scenarios/catalog.json']
    sources={'hub':source(hub,hub_files),'qualification':source(ROOT,own_files)}
    sources['hub']['repository']='cogno-us/cognous-open-control-stack'
    sources['qualification']['repository']='cogno-us/cognous-stack-qualification'
    output.mkdir(parents=True,exist_ok=False)
    catalog=json.loads((ROOT/'scenarios/catalog.json').read_text())
    protected=load_fixture(hub,'tests/test_protected_destination.py','native_protected')
    integrated=load_fixture(hub,'tests/test_integrated_assurance.py','native_integrated')
    cases=[];initial_digests={}
    for variant in plan['variants']:
        for i in range(1,plan['repetitions']+1):
            c=trial(variant,i,protected,integrated,output)
            family='approval' if variant['id'].startswith('approval-') else 'protected'
            if family in initial_digests and initial_digests[family]!=c['initial_business_digest']:
                raise ValueError('Initial business state drift between reset trials')
            initial_digests[family]=c['initial_business_digest']
            scenario=next(s for s in catalog['scenarios'] if s['id']==variant['scenario_id'])
            c.update(scenario_sha256=digest(scenario),provenance=scenario['provenance'],license=scenario['license'])
            cases.append(c)
    calibration=calibrate()
    record={'schema_version':'2.0.0','record_kind':'bounded-local-trajectory',
            'observed_at':datetime.now(timezone.utc).isoformat(),'sources':sources,
            'profile':{'id':plan['profile'],'selected':False,'sha256':digest(plan)},
            'plan_sha256':digest(plan),'environment':{'python':platform.python_version(),'platform':platform.platform(),
               'dependencies':{'cryptography':__import__('cryptography').__version__},'model':None,
               'containment':'native synthetic SQLite-only routes; prohibited shell operation is actively refused; host network sandbox NOT ESTABLISHED'},
            'cases':cases,'calibration':calibration,'artifacts':{},
            'assurance':{'release_authorized':False,'production_authorized':False,'human_oversight':'NOT EVALUATED'},
            'limitations':plan['limitations']}
    (output/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    record['artifacts']['plan.json']=file_digest(output/'plan.json')
    validate_record(record,plan,catalog,artifact_root=output)
    # Fail if a source tree changed while loading/running native modules.
    if sources!={'hub':{**source(hub,hub_files),'repository':'cogno-us/cognous-open-control-stack'},
                 'qualification':{**source(ROOT,own_files),'repository':'cogno-us/cognous-stack-qualification'}}:
        raise ValueError('Source changed during qualification')
    (output/'record.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    summary={'record_sha256':file_digest(output/'record.json'),'counts':dict(Counter(c['result']['verdict'] for c in cases)),
             'trials':len(cases),'catalog_acceptance':'UNCHANGED; local variants only',
             'model_trials':'NOT RUN: no supported model adapter/configuration provided',
             'human_oversight':'NOT EVALUATED'}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))
    return int(any(c['result']['verdict']!='PASS' for c in cases) or calibration['critical_defects_detected']!=calibration['critical_defects_total'] or calibration['false_alarms']!=0)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--hub',type=Path);p.add_argument('--output',type=Path);p.add_argument('--observe',type=Path)
    a=p.parse_args()
    if a.observe: print(json.dumps(observe(a.observe)));return 0
    if not a.hub or not a.output:p.error('--hub and --output required')
    return run(a.hub.resolve(),a.output.resolve())


if __name__=='__main__': raise SystemExit(main())
