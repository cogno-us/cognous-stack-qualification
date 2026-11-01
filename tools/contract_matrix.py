#!/usr/bin/env python3
"""Print or check the contract-version compatibility matrix for a set of component checkouts.

SPDX-License-Identifier: Apache-2.0

    python tools/contract_matrix.py check --components DIR [--matrix FILE] [--json]

DIR holds the component checkouts by profile name (control_plane, runtime, replay, ...), the layout
``tools/run_security_runtime.py --prepare-work`` builds. Exit status 0 when every boundary conforms, 1 otherwise.
The check reads each component's vendored ``tests/contracts/<contract>/CONTRACT.json``; it does not run any component code
and does not establish that a component behaves as it declares (see docs/contract-matrix.md).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'suites'))
import _contract_matrix as M  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='cmd', required=True)
    check = sub.add_parser('check', help='evaluate every boundary against the checkouts in --components')
    check.add_argument('--components', type=Path, required=True)
    check.add_argument('--matrix', type=Path, default=None)
    check.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    matrix = M.load_matrix(args.matrix)
    names = M.governed_components(matrix)
    rows = M.evaluate({n: args.components / n for n in names if (args.components / n).is_dir()}, matrix)
    if args.json:
        print(json.dumps({'boundaries': rows, 'sha_pin_gate': matrix.get('sha_pin_gate')}, indent=1, sort_keys=True))
    else:
        for r in rows:
            p, c = r['producer'], r['consumer']
            print(f"{r['boundary']}: {r['status']}  {r['contract']}  producer {p['component']} {p['contract_version']}/{p['conformance_level']}"
                  f"  consumer {c['component']} {c['contract_version']}/{c['conformance_level']}")
            for reason in r['reasons']:
                print(f'    - {reason}')
        print('sha-pin gate (no declared contract): ' + ', '.join(M.sha_pinned_components(matrix)))
    return 0 if all(r['status'] == M.CONFORMS for r in rows) else 1


if __name__ == '__main__':
    sys.exit(main())
