"""Validate coverage/run commitments and build GitHub Markdown plus a static UI.

SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
from qualification_results import ROOT, digest, validate_manifest

REPO = 'https://github.com/cogno-us/cognous-stack-qualification'


def symbols(path):
    found = set()
    def visit(nodes, prefix=''):
        for node in nodes:
            if isinstance(node, ast.ClassDef):
                visit(node.body, prefix + node.name + '.')
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                found.add(prefix + node.name)
    visit(ast.parse(path.read_text()).body)
    return found


def load_data(root=ROOT):
    catalog = json.loads((root/'scenarios/catalog.json').read_text())
    coverage = json.loads((root/'scenarios/coverage-map.json').read_text())
    cases = {s['id']: s for s in catalog['scenarios']}
    if len(cases) != len(catalog['scenarios']):
        raise ValueError('Duplicate catalog case')
    mappings = coverage['mappings']
    ids = [m['scenario_id'] for m in mappings]
    if len(ids) != len(set(ids)) or set(ids) != set(cases):
        raise ValueError('Coverage must map every Cognous case exactly once')
    migration = json.loads((root/'migrations/cross-component-2026-10-15.json').read_text())
    provenance = {r['destination_path']: r for s in migration['repositories'].values() for r in s['files']}
    symbol_cache = {}
    rows = []
    for mapping in mappings:
        case = cases[mapping['scenario_id']]
        case_hash = hashlib.sha256(json.dumps(case, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        if mapping['scenario_sha256'] != case_hash or mapping['scenario_version'] != case['version']:
            raise ValueError('Scenario changed; remap explicitly: ' + case['id'])
        if mapping['scenario_verdict'] != 'NOT RUN' or case['status'] != 'NOT RUN':
            raise ValueError('Static coverage cannot adopt a scenario verdict')
        if mapping['mapping_status'] not in {'PARTIAL', 'UNIMPLEMENTED', 'DEFERRED'} or not mapping['gaps']:
            raise ValueError('Mapping requires an explicit status and remaining gaps')
        if mapping['mapping_status'] == 'PARTIAL' and not mapping['tests']:
            raise ValueError('Partial mapping requires source references')
        if mapping['mapping_status'] == 'UNIMPLEMENTED' and mapping['tests']:
            raise ValueError('Unimplemented mapping cannot count test references')
        if mapping['scenario_provenance'] != case['provenance'] or mapping['scenario_license'] != case['license']:
            raise ValueError('Scenario provenance/license drift')
        for ref in mapping['tests']:
            path = PurePosixPath(ref['path'])
            if path.is_absolute() or '..' in path.parts or not ref['path'].startswith('suites/'):
                raise ValueError('Unsafe test path')
            target = root.joinpath(*path.parts)
            if target.is_symlink() or not target.resolve().is_relative_to(root.resolve()):
                raise ValueError('Test reference escapes canonical suite')
            if digest(target) != ref['sha256']:
                raise ValueError('Mapped test changed; review mapping: ' + ref['path'])
            row = provenance.get(ref['path'])
            if row is None or any(ref[k] != row[k] for k in ('source_url', 'source_sha256', 'license')):
                raise ValueError('Test provenance/license differs from migration')
            if not re.fullmatch(r'[0-9a-f]{40}', ref['suite_commit']):
                raise ValueError('Test link must pin its suite commit')
            if ref['path'] not in symbol_cache:
                symbol_cache[ref['path']] = symbols(target)
            if ref['symbol'] not in symbol_cache[ref['path']] or not ref['symbol'].split('.')[-1].startswith('test_'):
                raise ValueError('Missing mapped test symbol: ' + ref['symbol'])
        rows.append({**mapping, 'title': case['title'], 'suite': case['suite'],
                     'stimulus': case['stimulus'], 'required_observation': case['required_observation']})
    records = []
    for path in sorted((root/'results/workflows').glob('*/*.json')):
        record = validate_manifest(json.loads(path.read_text()))
        if path.stem != digest(path) or path.parent.name != record['run_id']:
            raise ValueError('Immutable result path/content commitment mismatch: ' + str(path))
        records.append({**record, 'manifest_path': path.relative_to(root).as_posix()})
    # Multiple snapshots of an in-progress run are history, not additional trials.
    latest = {}
    for record in records:
        key = record['run_id']
        stamp = lambda item: datetime.fromisoformat(item['observed_at'].replace('Z', '+00:00'))
        if key not in latest or stamp(record) > stamp(latest[key]):
            latest[key] = record
    wiki = json.loads((root/'scenarios/ai-security-wiki/catalog.json').read_text())
    wiki_count = len(wiki['scenarios'])
    return {'schema_version': '1.0.0', 'scenarios': rows,
            'mapping_counts': dict(Counter(m['mapping_status'] for m in rows)),
            'runs': sorted(latest.values(), key=lambda r: r.get('observed_at', ''), reverse=True),
            'snapshots': records, 'wiki_specifications': wiki_count,
            'wiki_status': 'NOT RUN; applicability unassessed',
            'migration': {'moved_files': sum(r['action']=='move' for s in migration['repositories'].values() for r in s['files']),
                          'workflows': sum(len(s['workflow_mappings']) for s in migration['repositories'].values()),
                          'public_repositories': len(migration['inventory'])}}


def cell(text):
    value = str(text).replace('\n', ' ').replace('\r', ' ').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return re.sub(r'([\\`*_\[\]()!|])', r'\\\1', value)


def render_html(template, data):
    payload = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    if template.count('__QUALIFICATION_DATA__') != 1:
        raise ValueError('Dashboard template requires one data boundary')
    return template.replace('__QUALIFICATION_DATA__', payload)


def markdown(data):
    counts = data['mapping_counts']
    lines = ['# Cognous qualification dashboard', '',
             '**40 Cognous scenarios: NOT RUN.** Static test associations and GitHub workflow outcomes are separate evidence types.', '',
             f"{counts.get('PARTIAL',0)} partial mappings · {counts.get('UNIMPLEMENTED',0)} unimplemented · {counts.get('DEFERRED',0)} deferred. Wiki specifications remain applicability-unassessed; the linked Wiki index maintains their current count.", '',
             '[Coverage map](../scenarios/coverage-map.json) · [Run contract](qualification-dashboard.md#run-manifest-contract) · [Source/licensing register](../sources/documents.json) · [Wiki attribution](../scenarios/ai-security-wiki/README.md)', '',
             '## Recorded execution', '',
             'Workflow PASS means that workflow reported success. It does not accept a catalog scenario or establish the complete loaded component set. Historical results identify their tested source; they do not qualify later commits.', '',
             '| Workflow / source | Outcome | Recorded workflow head | Evidence |',
             '|---|---|---|---|']
    for r in data['runs']:
        e = r['execution']
        label = cell(e.get('name',r['run_id']))
        lines.append(f"| [{label}]({e['url']}) / {cell(r['source']['repository'])} | {e['outcome']} | `{r['source']['commit']}` | [Manifest](../{r['manifest_path']}) |")
    if not data['runs']:
        lines.append('| No captured workflow records | NOT RUN | — | — |')
    lines += ['', '## Scenario mappings', '',
              'Every mapping below is proposed and partial, unimplemented or deferred. Follow the source links for exact assertions; the gap is part of the record.', '',
              '| Case | Scenario | Mapping | Supporting source | Remaining gap |', '|---|---|---|---|---|']
    for row in data['scenarios']:
        refs = [f"[{cell(t['symbol'])}]({REPO}/blob/{t['suite_commit']}/{t['path']})" for t in row['tests']]
        lines.append(f"| {row['scenario_id']} | {cell(row['title'])} | {row['mapping_status']} · NOT RUN | {'; '.join(refs) or 'None established'} | {cell(' '.join(row['gaps']))} |")
    lines += ['', '## Run manifest contract', '',
              'Version 1 captures exact source/suite identities exposed by the recorder, execution outcomes, profile/component-set gaps, command/environment details when available, evidence digests and expiry, and explicit limitations. Scenario results remain empty until a separate versioned evaluator is implemented. Expected/observed state and the three verdict dimensions remain unassessed when no authoritative observations were captured.', '',
              'Committed run snapshots are durable metadata. Workflow log links and artifacts may expire; their bytes are not preserved merely by committing this manifest. Release-accepted evidence must have durable references and verified hashes.', '',
              '## Maintain through GitHub', '',
              'Use **Actions → Capture qualification run metadata → Run workflow**, choose an inventoried public repository and enter its run ID. The workflow validates metadata and opens a results PR; merging it refreshes this dashboard. No offline file maintenance is needed.', '',
              'The Dashboard build workflow also produces a searchable static HTML artifact. The optional Pages workflow can publish it after a repository administrator enables GitHub Pages with Actions as its source. Pages activation is not performed by this repository code.', '',
              'See [the detailed operating guide](qualification-dashboard-guide.md). Existing selection and publication/production HOLD decisions remain with their owners.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'_site')
    parser.add_argument('--write-markdown', action='store_true')
    parser.add_argument('--check-markdown', action='store_true')
    args = parser.parse_args()
    data = load_data()
    md = markdown(data)
    if args.check_markdown and (ROOT/'docs/qualification-dashboard.md').read_text() != md:
        raise ValueError('Dashboard Markdown is stale; regenerate explicitly')
    if args.write_markdown:
        (ROOT/'docs/qualification-dashboard.md').write_text(md)
    args.output.mkdir(parents=True, exist_ok=True)
    template = (ROOT/'dashboard/index.template.html').read_text()
    (args.output/'index.html').write_text(render_html(template, data))
    for asset in ('app.js','style.css'):
        shutil.copyfile(ROOT/'dashboard'/asset, args.output/asset)
    (args.output/'data.json').write_text(json.dumps(data, indent=2)+'\n')
    print(f"Dashboard: {len(data['scenarios'])} NOT RUN cases, {len(data['runs'])} workflow records, {len(data['snapshots'])} immutable snapshots")


if __name__ == '__main__':
    main()
