#!/usr/bin/env python3
"""Plumbing-only check on renamed development twins (freeze rule: runs on twins whose output is reduced to the exit
status and the error text).

Each selected scenario of the plan is copied under a mechanical id (twin-1, twin-2, ...) and driven once through the
pinned runner's run_case on each comparator application with ADAPTERS replaced. The returned verdict is deleted
inside this script: no pass or fail is printed, stored or counted. Only 'executed' versus 'raised' is reported, with
the exception text. Outcomes are scored later, at the registered run, and not here.

Usage: SCN_HUB_DIR=<hub> SCN_OPA=<opa> python3 plumbing_twin.py --only TC-L06-011-S1,TC-L02-011-S3 [plan.json]
       (--only is required: this tool is not a way to run the whole plan)
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

PKG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PKG.parents[1]))
from comparators.wiki.harness import _base  # noqa: E402
from comparators.wiki.harness.registered_sets import wiki_adapters_opa_only, wiki_adapters_langgraph  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', required=True, help='comma-separated scenario ids to drive as twins')
    ap.add_argument('plan', nargs='?', default=str(PKG / 'plans' / 'wiki-subset-plan.json'))
    args = ap.parse_args(argv)
    wanted = args.only.split(',')
    plan = json.loads(Path(args.plan).read_text())
    by_id = {c['id']: c for c in plan['cases']}
    unknown = [w for w in wanted if w not in by_id]
    if unknown:
        raise SystemExit('not an executable scenario of the plan: ' + ', '.join(unknown))
    runner = _base.pinned_runner()
    adapters = {**wiki_adapters_opa_only(), **wiki_adapters_langgraph()}
    runner.ADAPTERS = adapters                       # the loader mechanism: replace the module global only
    opa = os.environ['SCN_OPA']
    tmp = Path(tempfile.mkdtemp(prefix='twin-'))
    raised = []
    for n, sid in enumerate(wanted, 1):
        twin = {k: v for k, v in by_id[sid].items() if k in ('steps', 'expected_statuses', 'expected_effects', 'allowed_effect_ids', 'expected_payload')}
        twin['id'] = 'twin-%d' % n
        for profile, cls in adapters.items():
            try:
                verdict = runner.run_case(cls, twin, tmp / profile / twin['id'], opa)
                del verdict                          # discarded on purpose
            except Exception as exc:  # noqa: BLE001
                raised.append((twin['id'], profile, type(exc).__name__, str(exc)[:200]))
    shutil.rmtree(tmp, ignore_errors=True)
    print('twins driven: %d on %d applications; raised: %d' % (len(wanted), len(adapters), len(raised)))
    for r in raised:
        print('  RAISED', *r)
    return 1 if raised else 0


if __name__ == '__main__':
    sys.exit(main())
