"""Validate the V1 failure register and back-fill closure-evidence labels (C12).

SPDX-License-Identifier: Apache-2.0

``closure_evidence`` is an optional per-entry object ``{label, owner}``. It records HOW a closure was established
(machine-asserted, independently-checked or human-validated) and who owns that claim. It is metadata only: this tool never
reads, derives or changes a ``status``, a verdict or any other field of an entry.

Rules checked by ``validate``:
  * label is one of the three values and owner is a non-empty string;
  * the literal owner ``unassigned`` is allowed only with ``machine-asserted``;
  * only a closed entry (``VERIFIED``) or an owner-decided entry (``WONTFIX-OWNER-DECISION``) may carry a label;
    ``OPEN``, ``REMEDIATION-PR`` and ``FIXED-UNVERIFIED`` entries carry none (a fix that has not been verified has no closure to label).

``backfill`` adds ``{label: machine-asserted, owner: unassigned}`` to every VERIFIED entry that has none, and nothing else.
It is the conservative default: it claims no independent or human check. The file keeps the register format
(``json.dumps(indent=1, ensure_ascii=False)`` and a trailing newline).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'process/v1-validation/v1-2026-10-16-a/failure-register.json'
LABELS = ('machine-asserted', 'independently-checked', 'human-validated')
LABELLABLE = ('VERIFIED', 'WONTFIX-OWNER-DECISION')
UNASSIGNED = 'unassigned'
BACKFILL = {'label': 'machine-asserted', 'owner': UNASSIGNED}


def dumps(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + '\n'


def validate(doc) -> list[str]:
    errors = []
    statuses = set(doc.get('statuses', []))
    seen = set()
    for entry in doc.get('entries', []):
        eid = entry.get('id', '?')
        if eid in seen:
            errors.append(f'{eid}: duplicate id')
        seen.add(eid)
        if entry.get('status') not in statuses:
            errors.append(f'{eid}: status {entry.get("status")!r} is not a register status')
        if 'closure_evidence' not in entry:
            continue
        ce = entry['closure_evidence']
        if not isinstance(ce, dict) or set(ce) != {'label', 'owner'}:
            errors.append(f'{eid}: closure_evidence must be exactly {{label, owner}}')
            continue
        if ce['label'] not in LABELS:
            errors.append(f'{eid}: closure_evidence.label {ce["label"]!r} not in {LABELS}')
        if not isinstance(ce['owner'], str) or not ce['owner'].strip():
            errors.append(f'{eid}: closure_evidence.owner must be a named owner')
        elif ce['owner'] == UNASSIGNED and ce['label'] != 'machine-asserted':
            errors.append(f'{eid}: only machine-asserted may have owner {UNASSIGNED!r}')
        if entry.get('status') not in LABELLABLE:
            errors.append(f'{eid}: status {entry.get("status")} may not carry a closure label')
    return errors


def backfill(doc) -> list[str]:
    """Mutates ``doc`` in place; returns the ids that received the conservative label."""
    added = []
    for entry in doc['entries']:
        if entry.get('status') == 'VERIFIED' and 'closure_evidence' not in entry:
            entry['closure_evidence'] = dict(BACKFILL)
            added.append(entry['id'])
    return added


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('command', choices=['validate', 'backfill'])
    ap.add_argument('--register', type=Path, default=DEFAULT)
    ap.add_argument('--write', action='store_true', help='backfill: write the file (default is a dry run)')
    args = ap.parse_args()
    doc = json.loads(args.register.read_text(encoding='utf-8'))
    if args.command == 'backfill':
        added = backfill(doc)
        print(f'backfill: {len(added)} VERIFIED entries labelled machine-asserted / unassigned: {", ".join(added) or "none"}')
        if args.write and added:
            args.register.write_text(dumps(doc), encoding='utf-8')
    errors = validate(doc)
    for e in errors:
        print('ERROR', e)
    if errors:
        raise SystemExit(1)
    counts = {}
    for entry in doc['entries']:
        label = entry.get('closure_evidence', {}).get('label', '(none)')
        counts[(entry['status'], label)] = counts.get((entry['status'], label), 0) + 1
    for (status, label), n in sorted(counts.items()):
        print(f'{status:24} {label:22} {n}')


if __name__ == '__main__':
    main()
