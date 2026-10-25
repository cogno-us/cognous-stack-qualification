#!/usr/bin/env python3
"""Replaces {{T_*}} placeholders in the assessment documents with the tables in data/tables.json.
Usage: fill_docs.py <DOC_DIR>. Runs once on the template documents; the published documents are the filled output.

SPDX-License-Identifier: Apache-2.0
"""
import json, re, sys, glob
D = sys.argv[1].rstrip('/') + '/'
T = json.load(open(D + 'data/tables.json'))
for f in sorted(glob.glob(D + '*.md')):
    s = open(f).read(); n = 0
    def r(m):
        global n; n += 1; return T[m.group(1)].rstrip('\n')
    s2 = re.sub(r'\{\{(T_[A-Z0-9_]+)\}\}', r, s)
    if n: open(f, 'w').write(s2); print(f.split('/')[-1], n, 'tables')
