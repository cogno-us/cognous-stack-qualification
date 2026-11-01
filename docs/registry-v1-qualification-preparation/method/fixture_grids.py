#!/usr/bin/env python3
"""Deterministic synthetic fixture grids that need NO V1 code. Writes data/fixture-grids.json.

SPDX-License-Identifier: Apache-2.0
Usage: fixture_grids.py <PACKAGE_DIR>   (stdlib only; writes only <PACKAGE_DIR>/data/fixture-grids.json)

The grids are inputs plus the expected effective value derived from the CONTRACT formula alone
(allow-lists: effective = caller INTERSECT registry; ages: effective = min(caller, registry) after strict-integer
validation, floor 1, refusal of invalid values). They are not outputs of any implementation and are not results.
Ages above are bounded only by representability here; the upper bound AGE_MAX is an open decision (O-4) and is NOT assumed.
"""
import itertools, json, sys

P = sys.argv[1].rstrip('/') + '/'
UNIVERSE = ['a', 'b', 'c']          # synthetic, exact-string members; no case folding, no wildcard
FIELDS = ['allowed_actions', 'allowed_adapters', 'allowed_units', 'allowed_institutions', 'allowed_authority_domains']


def relation(caller, registry):
    c, r = set(caller), set(registry)
    if c == r: return 'equal'
    if not r: return 'registry_empty'
    if not c: return 'caller_empty'
    if r < c: return 'registry_strict_subset'
    if r > c: return 'registry_strict_superset'
    if not (r & c): return 'disjoint'
    return 'overlap'


def subsets(u):
    return [list(s) for n in range(len(u) + 1) for s in itertools.combinations(u, n)]


sets_grid = []
for caller in subsets(UNIVERSE):
    for registry in subsets(UNIVERSE):
        eff = sorted(set(caller) & set(registry))
        sets_grid.append({'caller': caller, 'registry': registry, 'relation': relation(caller, registry),
                          'expected_effective': eff,
                          'registry_outcome': 'DENY_ALL_PRECONSTRUCTION' if not eff else 'NARROWED_EFFECTIVE_SET',
                          'never_wider_than_caller': True})
# near-miss exact-string members (must not match): case, whitespace, prefix, unicode confusable
near_miss = [{'caller': ['refund'], 'registry': [v], 'expected_effective': [], 'why': w} for v, w in
             [('Refund', 'case differs'), ('refund ', 'trailing space'), ('refun', 'prefix'), ('refund*', 'wildcard is not special'), ('rеfund', 'cyrillic e')]]

AGE_VALID = [1, 2, 59, 60, 61, 300]
AGE_INVALID = [None, '60', 60.0, True, False, 0, -1, float('nan'), float('inf'), 10 ** 30]
ages = []
for caller, registry in itertools.product(AGE_VALID, AGE_VALID):
    eff = min(caller, registry)
    rel = 'registry_lt_caller' if registry < caller else ('equal' if registry == caller else 'registry_gt_caller')
    ages.append({'caller': caller, 'registry': registry, 'relation': rel, 'expected_effective': eff,
                 'registry_value_recorded_non_narrowing': registry > caller})
invalid = [{'which': w, 'value': repr(v), 'expected': 'REFUSED_NEVER_CLAMPED'} for w in ('caller', 'registry') for v in AGE_INVALID]

# boundary offsets for an age bound B and a tolerance T (seconds); observation age = offset relative to 'now'
boundary = []
for B in (1, 60):
    for T in (0, 5):
        for off in (-(T + 1), -T, -1, 0, B - 1, B, B + 1):
            # off>0 means observation is `off` seconds in the past; off<0 means in the future by -off seconds
            future = off < 0
            fresh = (-off <= T) if future else (off <= B)
            boundary.append({'bound': B, 'tolerance': T, 'age_seconds': off, 'future': future,
                             'expected_fresh_under_frozen_evaluator_rule': fresh})
# validity interval [valid_from, valid_until): half-open
interval = [{'t_minus_valid_from': d, 't_minus_valid_until': e, 'expected_in_interval': d >= 0 and e < 0}
            for d, e in ((-1, -2), (0, -1), (5, -1), (5, 0), (5, 1))]
# epochs: strict-greater activation
epochs = [{'high_water': h, 'incoming': i, 'expected': 'ACTIVATE' if i > h else 'REFUSE_STALE_OR_EQUAL_EPOCH'}
          for h, i in ((0, 1), (1, 1), (2, 1), (5, 6), (5, 5), (5, 4))]

checks = [
    ('sets grid size', len(sets_grid) == 64),
    ('every effective is a subset of caller', all(set(g['expected_effective']) <= set(g['caller']) for g in sets_grid)),
    ('empty effective => preconstruction deny-all', all((g['registry_outcome'] == 'DENY_ALL_PRECONSTRUCTION') == (not g['expected_effective']) for g in sets_grid)),
    ('ages effective <= caller', all(a['expected_effective'] <= a['caller'] for a in ages)),
    ('ages effective <= registry', all(a['expected_effective'] <= a['registry'] for a in ages)),
]
bad = [n for n, ok in checks if not ok]
if bad:
    print('FAIL', bad); sys.exit(1)
out = {'status': 'PREPARATION: inputs and contract-derived expectations only; no implementation output; no result',
       'basis': 'effective allow-list = caller INTERSECT registry (P1 plan doc 04, ADR-REG-TR01); ages = validated per-scalar min on strict integer seconds, floor >= 1, invalid refused (P1 docs 03, 10); freshness rule characterized at Control Plane 7a4bcd40 bounded.py:2017-2024; interval [valid_from, valid_until); strict-greater epoch',
       'fields_for_set_grid': FIELDS, 'universe': UNIVERSE, 'sets_grid': sets_grid, 'near_miss_members': near_miss,
       'ages_valid_pairs': ages, 'ages_invalid_inputs': invalid, 'age_boundary_grid': boundary,
       'validity_interval_grid': interval, 'epoch_grid': epochs,
       'open_items': ['AGE_MAX (O-4) not assumed', 'exact refusal code names are NEW_CODE_PROPOSED until the ADR records them']}
json.dump(out, open(P + 'data/fixture-grids.json', 'w'), indent=1, ensure_ascii=False)
print('OK', {k: len(v) for k, v in out.items() if isinstance(v, list)})
