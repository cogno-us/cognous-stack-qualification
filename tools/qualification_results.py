"""Execution telemetry for qualification; command success is not scenario acceptance.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OUTCOMES = {'PASS', 'FAIL', 'RUNNING', 'CANCELLED', 'INCONCLUSIVE', 'NOT RUN'}
REPOSITORIES = {
    'cogno-us/' + name for name in (
        'cognous-stack-qualification', 'cognous-open-control-stack',
        'cognous-execution-runtime', 'cognous-replay-bundle',
        'cognous-governance-evidence-pack', 'cognous-governed-exchange',
        'open-decision-evidence-standard', 'cognous-evidence-registry')
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def outcome(status, conclusion):
    if status != 'completed':
        return 'RUNNING'
    return {'success': 'PASS', 'failure': 'FAIL', 'timed_out': 'FAIL',
            'cancelled': 'CANCELLED'}.get(conclusion, 'INCONCLUSIVE')


def validate_manifest(record):
    required = set(json.loads((ROOT/'schemas/run-manifest-v1.schema.json').read_text())['required'])
    if not required <= record.keys():
        raise ValueError('Missing run manifest fields: ' + ', '.join(sorted(required-record.keys())))
    if record.get('schema_version') != '1.0.0' or record.get('record_kind') not in {'workflow', 'command'}:
        raise ValueError('Unsupported run manifest')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,159}', record.get('run_id', '')):
        raise ValueError('Unsafe run ID')
    if record.get('source', {}).get('repository') not in REPOSITORIES:
        raise ValueError('Uninventoried source repository')
    if not re.fullmatch(r'[0-9a-f]{40}', record['source'].get('commit', '')):
        raise ValueError('Exact source commit required')
    qualification = record.get('qualification', {})
    if qualification.get('repository') != 'cogno-us/cognous-stack-qualification':
        raise ValueError('Qualification repository required')
    if any(not re.fullmatch(r'[0-9a-f]{40}', c) for c in qualification.get('commits', [])):
        raise ValueError('Exact suite commits required')
    if record.get('execution', {}).get('outcome') not in OUTCOMES:
        raise ValueError('Unknown execution outcome')
    observed = datetime.fromisoformat(record.get('observed_at', '').replace('Z', '+00:00'))
    if observed.tzinfo is None or observed.utcoffset().total_seconds() != 0:
        raise ValueError('Observation timestamp must be explicit UTC')
    # Version 1 deliberately has no acceptance evaluator. A workflow/JUnit pass cannot
    # be used to insert self-asserted case verdicts into the authoritative catalog.
    if record.get('scenario_results') != []:
        raise ValueError('Scenario acceptance requires a future versioned evaluator; v1 records execution only')
    if record.get('component_set', {}).get('completeness') != 'UNVERIFIED':
        raise ValueError('v1 cannot certify the complete loaded component set')
    if record.get('expected_state') is not None or record.get('observed_state') is not None:
        raise ValueError('v1 telemetry has no authoritative destination oracle')
    if record.get('verdict_dimensions') != dict.fromkeys(('evidence_integrity', 'business_correctness', 'authority_acceptance'), 'NOT ASSESSED'):
        raise ValueError('v1 cannot assess integrity/business/authority acceptance')
    if record['record_kind'] == 'workflow':
        execution = record['execution']
        if execution['outcome'] != outcome(execution.get('status'), execution.get('conclusion')):
            raise ValueError('Reported outcome contradicts provider conclusion')
    if record.get('assurance', {}).get('release_authorized') is not False or record['assurance'].get('production_authorized') is not False:
        raise ValueError('Run telemetry cannot authorize release or production')
    if not isinstance(record.get('evidence'), list) or not record.get('limitations'):
        raise ValueError('Evidence and limitations required')
    for ref in record['evidence']:
        if ref.get('retention') not in {'GIT_MANIFEST', 'EXPIRING_ARTIFACT', 'EXTERNAL_LINK', 'LOCAL_ONLY'}:
            raise ValueError('Evidence retention must be explicit')
        if ref.get('sha256') is not None and not re.fullmatch(r'[0-9a-f]{64}', ref['sha256']):
            raise ValueError('Invalid evidence digest')
        if 'url' in ref and not ref['url'].startswith('https://'):
            raise ValueError('Evidence links require HTTPS')
    return record


def base_record(run_id, kind, repository, source_commit, qualification_commits):
    return {
        'schema_version': '1.0.0', 'run_id': run_id, 'record_kind': kind,
        'source': {'repository': repository, 'commit': source_commit},
        'qualification': {'repository': 'cogno-us/cognous-stack-qualification', 'commits': qualification_commits},
        'profile': {'label': 'UNSPECIFIED', 'sha256': None},
        'component_set': {'completeness': 'UNVERIFIED', 'components': []},
        'environment': {}, 'execution': {}, 'evidence': [], 'scenario_results': [],
        'expected_state': None, 'observed_state': None,
        'verdict_dimensions': {'evidence_integrity': 'NOT ASSESSED', 'business_correctness': 'NOT ASSESSED', 'authority_acceptance': 'NOT ASSESSED'},
        'assurance': {'release_authorized': False, 'production_authorized': False},
        'limitations': ['Execution outcome only. No catalog scenario has been accepted by this manifest.',
                        'The complete loaded component set, final-state oracle, reset/containment and evaluator evidence are not established by metadata.']}


def workflow_manifest(snapshot, repository, observed_at):
    run = snapshot['run']
    if repository not in REPOSITORIES or run.get('repository', {}).get('full_name') != repository:
        raise ValueError('Workflow repository identity mismatch')
    if run['repository'].get('private') is not False:
        raise ValueError('Only explicitly public workflow sources may be recorded')
    if not isinstance(run.get('id'), int) or run['id'] <= 0:
        raise ValueError('Invalid workflow identity')
    commits = sorted({x['sha'] for x in run.get('referenced_workflows', [])
                      if x.get('path', '').startswith('cogno-us/cognous-stack-qualification/')})
    if repository == 'cogno-us/cognous-stack-qualification':
        commits = sorted(set(commits + [run['head_sha']]))
    attempt = run.get('run_attempt', 1)
    record = base_record(f"gh-{repository.split('/')[-1]}-{run['id']}-attempt-{attempt}",
                         'workflow', repository, run['head_sha'], commits)
    record['observed_at'] = observed_at
    record['source']['identity_basis'] = 'GitHub-reported workflow head_sha; per-job checkout unverified'
    record['qualification']['identity_basis'] = 'GitHub referenced_workflows; overlay artifacts not independently inspected'
    record['environment'] = {'kind': 'github-actions', 'event': run.get('event'), 'workflow_path': run.get('path')}
    record['execution'] = {
        'outcome': outcome(run['status'], run.get('conclusion')),
        'workflow_id': run['id'], 'attempt': attempt, 'name': run['name'],
        'status': run['status'], 'conclusion': run.get('conclusion'),
        'url': f"https://github.com/{repository}/actions/runs/{run['id']}",
        'started_at': run.get('run_started_at'), 'last_updated_at': run.get('updated_at'),
        'finished_at': None,
        'jobs': [{k: j.get(k) for k in ('id', 'name', 'status', 'conclusion', 'started_at', 'completed_at')}
                 for j in snapshot.get('jobs', [])]}
    record['evidence'] = [{'kind': 'workflow-log-reference', 'url': record['execution']['url'],
                           'retention': 'EXTERNAL_LINK', 'sha256': None}]
    for artifact in snapshot.get('artifacts', []):
        raw_digest = artifact.get('digest') or ''
        sha = raw_digest.removeprefix('sha256:') if raw_digest.startswith('sha256:') else None
        record['evidence'].append({
            'kind': 'github-artifact', 'name': artifact['name'], 'artifact_id': artifact['id'],
            'url': record['execution']['url'] + '/artifacts/' + str(artifact['id']),
            'sha256': sha, 'digest_basis': 'GitHub API metadata; bytes not independently downloaded',
            'retention': 'EXPIRING_ARTIFACT', 'expires_at': artifact.get('expires_at'),
            'expired_at_observation': artifact.get('expired')})
    record['limitations'] += ['Workflow/job conclusions are GitHub-reported metadata, not independent destination observations.',
                              'Individual jobs may load different or frozen checkouts. source.commit records the workflow head, not every loaded tree.',
                              'GitHub does not provide a reliable run completion timestamp here; finished_at is null.',
                              'External logs and artifacts may expire. Committed metadata does not preserve their bytes.']
    if not commits:
        record['limitations'].append('No qualification-suite commit was exposed by referenced_workflows.')
    return validate_manifest(record)


def write_immutable(record, root):
    validate_manifest(record)
    content = json.dumps(record, indent=2, sort_keys=True) + '\n'
    sha = hashlib.sha256(content.encode()).hexdigest()
    path = Path(root) / record['run_id'] / (sha + '.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text() != content:
            raise ValueError('Evidence path collision')
    else:
        with path.open('x') as stream:
            stream.write(content)
    return path
