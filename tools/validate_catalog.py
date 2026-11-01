"""Validate provenance and specifications; never execute qualification scenarios.

SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(root=ROOT):
    catalog = json.loads((root / 'scenarios/catalog.json').read_text())
    sources = json.loads((root / 'sources/documents.json').read_text())['sources']
    cases = catalog['scenarios']
    ids = [case['id'] for case in cases]
    require(len(ids) == len(set(ids)), 'Duplicate Cognous scenario IDs')
    original = {f'D{i:02}' for i in range(1, 10)} | {f'A{i:02}' for i in range(1, 7)} | {'H01', 'H02'}
    require(original <= set(ids), 'Missing original addendum case')
    allowed = {'PASS', 'FAIL', 'INCONCLUSIVE', 'NOT RUN', 'NOT APPLICABLE'}
    markdown = (root / 'scenarios/README.md').read_text()
    for case in cases:
        for field in ('id', 'version', 'title', 'suite', 'status', 'source', 'stimulus', 'required_observation', 'applicability', 'execution_spec', 'steps', 'forbidden_effects', 'implementation_status', 'provenance', 'license'):
            require(bool(case.get(field)), f"{case['id']}: missing {field}")
        require(case['status'] in allowed, 'Unsupported status')
        require(case['source']['document'] in sources, 'Unknown source')
        source = sources[case['source']['document']]
        provenance = case['provenance']
        require(provenance['source_id'] == case['source']['document'], 'Source registry mismatch')
        require(provenance['registry'] == 'sources/documents.json', 'Unknown source registry')
        require(provenance['document_sha256'] == source['sha256'], 'Document digest mismatch')
        require(bool(provenance['source_section']) and bool(provenance['reuse_basis']), 'Missing source section or reuse basis')
        require(case['license'] == source['adaptation_license'] == 'Apache-2.0', 'Cognous adaptation license mismatch')
        require((root / case['execution_spec']).is_file(), 'Missing execution contract')
        require(f"## {case['id']}\n" in markdown, 'Missing browsable scenario')
        for related in case.get('related_scenarios', []):
            require(related in ids, f'Unknown related ID: {related}')
        if case['implementation_status'] == 'SPECIFICATION ONLY':
            require(case['status'] == 'NOT RUN' and case['results'] == [], 'Specification misrepresented as execution')
        for field in ('stimulus', 'required_observation'):
            require(case[field] in markdown, f"{case['id']}: Markdown/catalog drift")
    lock = json.loads((root / 'sources/ai-security-wiki.lock.json').read_text())
    base = root / 'scenarios/ai-security-wiki'
    wiki = json.loads((base / 'catalog.json').read_text())
    sha = lock['source_commit']
    require(bool(re.fullmatch(r'[0-9a-f]{40}', sha)), 'Non-exact source identity')
    require(hashlib.sha256((base / 'LICENSE').read_bytes()).hexdigest() == lock['approved_license_sha256'], 'Imported license differs from approved terms')
    require(lock['license'] == wiki['license'] == 'CC-BY-SA-4.0', 'Wiki license mismatch')
    require(wiki['source_commit'] == sha, 'Wiki revision mismatch')
    by_path = {}
    page_case_ids = set()
    for page in lock['pages']:
        path = root / page['redistributed_path']
        require(path.is_file(), 'Missing imported page')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == page['redistributed_sha256'], 'Imported page modified without provenance regeneration')
        text = path.read_text()
        require('SPDX-License-Identifier: CC-BY-SA-4.0' in text, 'Missing page license')
        require(bool(page['authors']) and all(author in text for author in page['authors']), 'Missing author attribution')
        page_ids = re.findall(r'^### (TC-[A-Z]\d+-\d+): ', text, re.M)
        require(len(page_ids) == page['case_count'], 'Page case count mismatch')
        require(not (page_case_ids & set(page_ids)), 'Duplicate page case ID')
        page_case_ids.update(page_ids)
        by_path[page['path']] = page
    wiki_ids = []
    for case in wiki['scenarios']:
        source = case['source']
        require(source['repository'] == lock['repository'] and source['commit'] == sha, 'Wiki provenance mismatch')
        page = by_path[source['path']]
        require(case['authors'] == page['authors'] and bool(case['authors']), 'Case author mismatch')
        require(case['license'] == 'CC-BY-SA-4.0', 'Wiki case relicensed')
        require(source['page_sha256'] == page['sha256'], 'Source page digest mismatch')
        require(bool(re.fullmatch(r'[0-9a-f]{64}', source['case_block_sha256'])), 'Missing case commitment')
        require(source['url'] == f"{lock['repository_url']}/blob/{sha}/{source['path']}#{case['id'].lower()}", 'Source URL is not exact')
        require(source['anchor'] == case['id'].lower(), 'Source anchor mismatch')
        require(case['status'] == 'NOT RUN' and case['results'] == [], 'Imported reference misrepresented as execution')
        require(case['implementation_status'] == 'UPSTREAM SPECIFICATION ONLY' and bool(case['applicability']), 'Missing reference scope')
        detail, anchor = case['details'].split('#')
        require((base / detail).is_file() and anchor == case['id'].lower(), 'Broken case details reference')
        require(f'### {case["id"]}: {case["title"]}' in (base / detail).read_text(), 'Case content mismatch')
        wiki_ids.append(case['id'])
    require(len(wiki_ids) == len(set(wiki_ids)), 'Duplicate Wiki scenario IDs')
    require(set(wiki_ids) == page_case_ids == set(lock['case_ids']), 'Source cases omitted from catalog')
    require(len(wiki_ids) == lock['case_count'], 'Wiki count mismatch')
    print(f'Valid: {len(cases)} Cognous + {len(wiki_ids)} Wiki specifications; provenance/license records checked. No qualification scenarios executed.')


if __name__ == '__main__':
    validate()
