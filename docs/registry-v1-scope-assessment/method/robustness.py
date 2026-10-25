#!/usr/bin/env python3
"""Perturbation check of the manually assigned scores (D, E) and the lane-D complexity (F): 5000 seeded draws, each manual score moved by -1/0/+1 (clamped 1..5).

SPDX-License-Identifier: Apache-2.0
Reports how often each family stays in the top 5 under each weighting. Usage: robustness.py <DATA_DIR>"""
import json, random, sys
D = sys.argv[1].rstrip('/') + '/'
m = json.load(open(D + 'family-metrics-and-scores.json')); S, W = m['scores'], m['weights']
random.seed(7); FAMS = list(S); N = 5000
cnt = {w: {f: 0 for f in FAMS} for w in W}; first = {w: {f: 0 for f in FAMS} for w in W}
cl = lambda x: max(1, min(5, x))
for _ in range(N):
    P = {f: dict(S[f]) for f in FAMS}
    for f in FAMS:
        for k in ('D_enforcement_maturity', 'E_incremental_capability', 'F_ease'):
            P[f][k] = cl(P[f][k] + random.choice((-1, 0, 1)))
    for w, wt in W.items():
        comp = {f: sum(wt[k] * P[f][k] for k in wt) for f in FAMS}
        order = sorted(FAMS, key=lambda f: (-comp[f], f))
        for f in order[:5]: cnt[w][f] += 1
        first[w][order[0]] += 1
out = {w: {f: round(100 * cnt[w][f] / N, 1) for f in FAMS} for w in W}
json.dump({'draws': N, 'seed': 7, 'pct_in_top5': out, 'pct_rank1': {w: {f: round(100 * first[w][f] / N, 1) for f in FAMS} for w in W}}, open(D + 'robustness.json', 'w'), indent=1)
for w in W: print(w, {f: v for f, v in out[w].items() if v >= 1})
