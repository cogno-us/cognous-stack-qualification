"""Check relocation completeness, source provenance and retained license bytes.

SPDX-License-Identifier: Apache-2.0
"""
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT=Path(__file__).resolve().parents[1]


def validate(root=ROOT):
    record=json.loads((root/'migrations/cross-component-2026-10-15.json').read_text())
    count=0;workflows=0;seen=set()
    for name,spec in record['repositories'].items():
        if len(spec['source_commit'])!=40:
            raise ValueError('Non-exact source commit')
        for row in spec['files']:
            relative=PurePosixPath(row['destination_path'])
            if relative.is_absolute() or '..' in relative.parts or row['destination_path'] in seen:
                raise ValueError('Unsafe or duplicate destination')
            seen.add(row['destination_path'])
            path=root.joinpath(*relative.parts)
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=row['destination_sha256']:
                raise ValueError('Missing or modified relocated file: '+str(path))
            if row.get('source_mode') not in {'100644','100755'} or bool(path.stat().st_mode & 0o100)!=(row['source_mode']=='100755'):
                raise ValueError('Relocated executable mode differs from source')
            if row['source_sha256']!=row['destination_sha256']:
                raise ValueError('Initial relocation must retain original bytes')
            if f'/blob/{spec["source_commit"]}/' not in row['source_url']:
                raise ValueError('Unpinned provenance')
            if row['license'] not in {'Apache-2.0','MIT'}:
                raise ValueError('Unsupported/unreviewed inbound license')
            if path.suffix=='.py':ast.parse(path.read_text(),filename=str(path))
            count+=1
        for notice in spec['license_notices']:
            path=root/notice['retained_path']
            if hashlib.sha256(path.read_bytes()).hexdigest()!=notice['sha256']:
                raise ValueError('Retained license or notice changed')
        for mapping in spec['workflow_mappings']:
            if not (root/mapping['qualification_workflow']).is_file():
                raise ValueError('Missing reusable workflow')
            text=(root/mapping['qualification_workflow']).read_text()
            if 'workflow_call:' not in text or 'install_suite.py' not in text:
                raise ValueError('Reusable workflow lacks assembly/provenance')
            workflows+=1
    if len(record['inventory'])!=19 or record['private_inventory']['public_export'] is not False:
        raise ValueError('Repository inventory or private boundary incomplete')
    print(f'Migration integrity: {count} original files, {workflows} workflows, 19 public repositories inventoried; private export disabled. No qualification claim.')


if __name__=='__main__':validate()
