"""Validate the proposed OCS Registry V1 gate-binding table (QG-01..QG-14). Preparation only.

Checks structure and references. It never executes a scenario, stores a result status, or issues a verdict.
Lives beside the table, not in tools/: the MVP acceptance candidate commits every file in tools/ (see the QPR-1 doc).
Reuses `v1_validation.validate_requirements` for the requirement-row model and resolves scenario ids against
the existing canonical inventory. Reads no other repository; the optional matrix file is plain input data.

SPDX-License-Identifier: Apache-2.0
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLE = ROOT / 'process/registry-v1/gate-bindings.proposed.v1.json'
CROSSWALK = ROOT / 'docs/registry-v1-scope-assessment/data/canonical-scenario-crosswalk.json'
CATALOG = ROOT / 'scenarios/catalog.json'

PLAN_REVISION = 'd2c472e4a09543228bad62235e07a0dedfd7f48b'
MATRIX_SHA256 = 'e81b5fad1dfcc9bcb002111a17e7bd79117efa53cfc81b3198fbcb75b2dd04bd'
GATE_IDS = [f'QG-{i:02d}' for i in range(1, 15)]
INACTIVE_GATE = 'QG-02'
ALL_SCOPE_GATE = 'QG-14'
MODE = 'PREPARE_ONLY_UNTIL_INDEPENDENT_LEAD_DESIGNATED'
INACTIVE_STATUS = 'INACTIVE_MAX_AMOUNT_DEFERRED'
ORIGINS = {'qualification-repository', 'registry-builder-repository', 'descriptive-no-path'}
SCOPES = {'listed', 'all_canonical_scenarios'}
# A binding table records no execution result: these keys must not appear anywhere in it.
RESULT_KEYS = {'status', 'result', 'results', 'verdict', 'outcome', 'declared_status', 'computed_status', 'executed_cases', 'pass', 'fail'}
CLAIM_PHRASES = ('independently qualified', 'qualified by', 'certified', 'qualification verdict', 'tier 1 qualified')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def row_digest(row):
    return hashlib.sha256(json.dumps(row, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def _validate_requirements(doc):
    sys.path[:0] = [str(ROOT / 'tools')]
    import v1_validation  # importing it reads the committed freeze manifest only; no component checkout
    v1_validation.validate_requirements(doc)


def _walk_keys(node, path=''):
    if isinstance(node, dict):
        for key, value in node.items():
            yield f'{path}/{key}', key
            yield from _walk_keys(value, f'{path}/{key}')
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _walk_keys(value, f'{path}[{i}]')


def inventory_ids(root=ROOT):
    crosswalk = json.loads((root / CROSSWALK.relative_to(ROOT)).read_text(encoding='utf-8'))
    catalog = json.loads((root / CATALOG.relative_to(ROOT)).read_text(encoding='utf-8'))
    return {r['scenario_id'] for r in crosswalk} | {c['id'] for c in catalog['scenarios']}


def validate(table=None, root=ROOT, matrix_rows=None):
    """Raise ValueError on the first missing or inconsistent binding; return a summary dict otherwise."""
    if table is None:
        table = json.loads((root / TABLE.relative_to(ROOT)).read_text(encoding='utf-8'))
    require(table.get('schema') == 'ocs-registry-v1-gate-bindings' and table.get('version') == 'proposed.v1', 'Unknown schema or version')
    _validate_requirements(table)  # existing requirement-row model: ids, kinds, selectors
    rows = table['requirements']
    require([r['id'] for r in rows] == GATE_IDS, 'Gate rows must be exactly QG-01..QG-14 in order')

    plan = table.get('plan_source', {})
    require(plan.get('revision') == PLAN_REVISION and plan.get('matrix_sha256') == MATRIX_SHA256 and plan.get('gate_count') == 14, 'Plan source pin mismatch')
    for ref in table.get('contract_refs', []):
        require(all(ref.get(k) for k in ('repository', 'revision', 'path', 'role')), f'Incomplete contract reference {ref}')
        if ref['repository'] == 'cogno-us/cognous-stack-qualification':
            require((root / ref['path']).is_file(), f"Contract reference not found in this repository: {ref['path']}")
    require(len(table.get('contract_refs', [])) >= 5, 'Contract references missing')

    for path, key in _walk_keys(table):
        require(key.lower() not in RESULT_KEYS, f'Result-like key {path}: a binding table stores no execution result')
    text = json.dumps(table).lower()
    for phrase in CLAIM_PHRASES:
        require(phrase not in text, f'Qualification claim phrase {phrase!r} is not allowed')

    known = inventory_ids(root)
    active = 0
    for row in rows:
        gid, gate = row['id'], row.get('gate')
        require(isinstance(gate, dict), f'{gid}: missing gate binding')
        require(gate.get('qualification_mode') == MODE, f'{gid}: qualification_mode must be {MODE}')
        require(gate.get('qualified') is False, f'{gid}: qualified must be false')
        require(bool(gate.get('sprint')), f'{gid}: missing sprint')
        require(isinstance(gate.get('plan_row_sha256'), str) and len(gate['plan_row_sha256']) == 64, f'{gid}: missing plan row digest')
        require(isinstance(gate.get('predeclared_new_test_items'), int) and gate['predeclared_new_test_items'] >= 0, f'{gid}: bad new-item count')
        require(bool(gate.get('known_gaps')), f'{gid}: known_gaps must be recorded')
        if gid == INACTIVE_GATE:
            require(gate.get('v1_status') == INACTIVE_STATUS and row.get('mandatory') is False, 'QG-02 must be INACTIVE_MAX_AMOUNT_DEFERRED and not mandatory')
        else:
            require(gate.get('v1_status') == 'ACTIVE' and row.get('mandatory') is True, f'{gid}: every other gate must be ACTIVE and mandatory')
            active += 1
        scope = gate.get('scenario_scope')
        require(scope in SCOPES, f'{gid}: unknown scenario_scope')
        ids = [e['id'] for e in gate.get('scenario_ids', [])]
        require(len(ids) == len(set(ids)), f'{gid}: duplicate scenario id')
        if scope == 'all_canonical_scenarios':
            require(gid == ALL_SCOPE_GATE and not ids, f'{gid}: only QG-14 may bind all scenarios, with no listed ids')
        else:
            require(bool(ids), f'{gid}: no scenario ids bound')
        for sid in ids:
            require(sid in known, f'{gid}: scenario id {sid} does not resolve in the existing inventory')
        require(bool(gate.get('existing_test_refs')) or gid == ALL_SCOPE_GATE, f'{gid}: no existing test references')
        for ref in gate.get('existing_test_refs', []):
            require(ref.get('origin') in ORIGINS and bool(ref.get('ref')), f'{gid}: bad existing reference {ref}')
            if ref['origin'] == 'qualification-repository':
                require(ref.get('path') and (root / ref['path']).exists(), f"{gid}: referenced path not found in this repository: {ref.get('path')}")
            elif ref['origin'] == 'descriptive-no-path':
                require(ref.get('path') is None, f'{gid}: a descriptive reference carries no path')
    require(active == 13, 'Exactly 13 gates must be active')
    if matrix_rows is not None:
        compare_to_matrix(table, matrix_rows)
    return {'gates': len(rows), 'active': active, 'inactive': [INACTIVE_GATE]}


def compare_to_matrix(table, matrix_rows):
    """Optional drift check against a copy of the plan matrix supplied as data (not imported, not fetched)."""
    require([m['gate_id'] for m in matrix_rows] == GATE_IDS, 'Matrix gates differ from QG-01..QG-14')
    for row, m in zip(table['requirements'], matrix_rows):
        require(row['gate']['plan_row_sha256'] == row_digest(m), f"{row['id']}: plan row changed since the binding was written")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--matrix', help='optional copy of the plan qualification-gate-matrix.json for a digest check')
    args = parser.parse_args(argv)
    rows = None
    if args.matrix:
        raw = Path(args.matrix).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == MATRIX_SHA256, 'Matrix file digest differs from the pinned plan digest')
        rows = json.loads(raw)
    summary = validate(matrix_rows=rows)
    print(f"Valid: {summary['gates']} gate bindings, {summary['active']} active, {summary['inactive'][0]} INACTIVE. "
          'No scenarios executed. No result or verdict stored. No qualification claim.')


if __name__ == '__main__':
    main()
