"""Capture allowlisted public GitHub run metadata as an append-only manifest.

Never downloads logs/artifact bytes, executes source code or changes case verdicts.
SPDX-License-Identifier: Apache-2.0
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
from qualification_results import REPOSITORIES, workflow_manifest, write_immutable


def get_json(path):
    headers = {'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'Cognous-qualification-recorder'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    request = urllib.request.Request('https://api.github.com/' + path, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def collection(path, key):
    rows = []
    for page in range(1, 101):
        data = get_json(path + f'?per_page=100&page={page}')
        rows.extend(data[key])
        if len(data[key]) < 100:
            return rows
    raise ValueError('Metadata exceeds bounded pagination; no complete capture inferred')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', required=True, choices=sorted(REPOSITORIES))
    parser.add_argument('--run-id', required=True, type=int)
    parser.add_argument('--snapshot', type=Path, help='Previously fetched run/jobs/artifacts JSON; no network when supplied')
    parser.add_argument('--output', type=Path, default=Path('results/workflows'))
    args = parser.parse_args()
    if args.run_id <= 0:
        parser.error('Run ID must be positive')
    observed_at = datetime.now(timezone.utc).isoformat()
    if args.snapshot:
        data = json.loads(args.snapshot.read_text())
        observed_at = data.get('observed_at', observed_at)
    else:
        base = f'repos/{args.repository}/actions/runs/{args.run_id}'
        run = get_json(base)
        # Freeze the specific attempt; do not silently mix jobs from a rerun.
        jobs = collection(base + f"/attempts/{run['run_attempt']}/jobs", 'jobs')
        artifacts = collection(base + '/artifacts', 'artifacts')
        again = get_json(base)
        if (run['head_sha'], run['run_attempt'], run['status'], run.get('conclusion'), run['updated_at']) != (again['head_sha'], again['run_attempt'], again['status'], again.get('conclusion'), again['updated_at']):
            raise ValueError('Run changed during capture; retry a coherent snapshot')
        data = {'run': run, 'jobs': jobs, 'artifacts': artifacts}
    if data['run']['id'] != args.run_id:
        raise ValueError('Requested run identity mismatch')
    record = workflow_manifest(data, args.repository, observed_at)
    print(write_immutable(record, args.output))


if __name__ == '__main__':
    main()
