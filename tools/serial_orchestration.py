"""Validate serial orchestration state and retained local-variant evidence.

SPDX-License-Identifier: Apache-2.0
"""
from collections import Counter
import argparse
import json
from pathlib import Path
import subprocess
from trajectory_contract import ROOT, digest, file_digest, validate_record

STATUSES={'PLANNED','READY','IN PROGRESS','BLOCKED','IN REVIEW','ACCEPTED','INTEGRATED'}


def load_serial(root=ROOT):
    path=root/'qualification/orchestration-state.json'
    if not path.exists():return None
    state=json.loads(path.read_text())
    if state['human_oversight']!='NOT EVALUATED' or state['selected'] is not False:
        raise ValueError('Invalid oversight or selected-profile claim')
    if [p['id'] for p in state['phases']]!=['T1','T2','T3','T4','CLOSEOUT']:
        raise ValueError('Serial phases must retain fixed dependency order')
    for phase in state['phases']:
        if phase['status'] not in STATUSES or not phase['next_action']:
            raise ValueError('Phase status and next action required')
        for dep in phase['dependencies']:
            predecessor=next(p for p in state['phases'] if p['id']==dep)
            if phase['status'] in {'ACCEPTED','INTEGRATED'} and predecessor['status'] not in {'ACCEPTED','INTEGRATED'}:
                raise ValueError('Phase accepted before dependency')
    ref=state.get('evidence')
    if ref:
        p=root/ref['path']
        if Path(ref['path']).is_absolute() or '..' in Path(ref['path']).parts or not p.resolve().is_relative_to(root.resolve()):
            raise ValueError('Unsafe record path')
        if file_digest(p)!=ref['sha256']:raise ValueError('Record commitment changed')
        supplemental=json.loads((p.parent/'command-evidence.json').read_text())
        for name,sha in supplemental['artifacts'].items():
            if Path(name).name!=name or file_digest(p.parent/name)!=sha:
                raise ValueError('Supplemental command evidence changed')
        record=json.loads(p.read_text());plan=json.loads((p.parent/'plan.json').read_text())
        validate_record(record,plan,json.loads((root/'scenarios/catalog.json').read_text()),artifact_root=p.parent)
        # Code/plan/catalog edits stale the run; presentation-only dashboard edits do not.
        for relative,sha in record['sources']['qualification']['files'].items():
            if file_digest(root/relative)!=sha:raise ValueError('Relevant qualification input changed; rerun: '+relative)
        if dict(Counter(c['result']['verdict'] for c in record['cases']))!=state['variant_counts']:
            raise ValueError('Dashboard count mismatch')
        if record['sources']!=state['tested_sources']:raise ValueError('Dashboard tested SHA mismatch')
    return state


def markdown(state):
    if not state:return ''
    lines=['## Serial qualification orchestration','',
        f"**{state['overall_status']}** · Profile `{state['profile']}` · nonselected synthetic fixture · updated {state['verified_at']}",'',
        'Human participation excluded. Human oversight effectiveness: **NOT EVALUATED**. Full catalog acceptance remains unchanged.','',
        '| Phase | Status | Next action |','|---|---|---|']
    for p in state['phases']:lines.append(f"| {p['id']} — {p['scope']} | {p['status']} | {p['next_action']} |")
    lines+=['',f"Named local variant counts: `{json.dumps(state['variant_counts'],sort_keys=True)}`. These are diagnostic assertions, not whole-scenario or selected-stack acceptance.",'']
    if state.get('evidence'):lines.append(f"[Native evidence record](../{state['evidence']['path']}) · [Serial packet and reproduction](serial-qualification.md)")
    for b in state['blockers']:lines.append(f"- {b['id']}: {b['reason']} Owner: {b['owner']}. Resolution: {b['resolution']}")
    lines+=['', 'Deferred final-package review and issue reconciliation remain queued until current engineering/testing finishes; this increment does not perform them.','']
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--hub',type=Path)
    a=p.parse_args();state=load_serial()
    if a.hub and state.get('tested_sources'):
        source=state['tested_sources']['hub']
        head=subprocess.check_output(['git','-C',str(a.hub),'rev-parse','HEAD'],text=True).strip()
        if head!=source['commit']:raise ValueError('Hub revision differs from tested source')
        for path,sha in source['files'].items():
            if file_digest(a.hub/path)!=sha:raise ValueError('Loaded hub source changed')
    print(markdown(state))


if __name__=='__main__':main()
