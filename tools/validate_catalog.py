"""Validate scenario specifications; does not execute qualification scenarios."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
catalog = json.loads((root / 'scenarios/catalog.json').read_text())
cases = catalog['scenarios']
ids = [case['id'] for case in cases]
assert len(ids) == len(set(ids)), 'Duplicate scenario IDs'
required_ids = {f'D{i:02}' for i in range(1, 10)} | {f'A{i:02}' for i in range(1, 7)} | {'H01', 'H02'}
assert required_ids <= set(ids), 'Missing original addendum case'
allowed = {'PASS', 'FAIL', 'INCONCLUSIVE', 'NOT RUN', 'NOT APPLICABLE'}
markdown = (root / 'scenarios/README.md').read_text()
for case in cases:
    for field in ('id', 'version', 'title', 'suite', 'status', 'source', 'stimulus', 'required_observation', 'applicability', 'execution_spec', 'steps', 'forbidden_effects', 'implementation_status'):
        assert case.get(field), f"{case['id']}: missing {field}"
    assert case['status'] in allowed, f"{case['id']}: unsupported status"
    assert case['source']['document'] in {'A', 'B'}, 'Unknown source'
    assert (root / case['execution_spec']).is_file(), 'Missing execution contract'
    assert f"## {case['id']}\n" in markdown, 'Missing browsable scenario'
    for related in case.get('related_scenarios', []):
        assert related in ids, f'Unknown related ID: {related}'
    if case['implementation_status'] == 'SPECIFICATION ONLY':
        assert case['status'] == 'NOT RUN' and case['results'] == [], 'Specification misrepresented as execution'
    for field in ('stimulus', 'required_observation'):
        assert case[field] in markdown, f"{case['id']}: Markdown/catalog drift"
print(f'Catalog structure valid: {len(cases)} scenario specifications. No qualification scenarios executed.')
