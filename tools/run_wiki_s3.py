#!/usr/bin/env python3
"""One-shot, reproducible runner for the 41 previously BLOCKED Security Wiki tests against the generation-2 current-stack tuple.

SPDX-License-Identifier: Apache-2.0
PREPARED, NOT YET EXECUTED. Non-authorizing. Runs ONLY the node ids in the nodeids file, ONCE (no retries, no -x, one pytest process,
no xdist), with junit XML, a log and the observer-only plugin, and records environment, tool versions and SHA-256 of every artifact.

    python tools/run_wiki_s3.py --tuple TUPLE.json --components DIR --out NEWDIR [--hub DIR] [--dry-check]

TUPLE.json (schema cognous.wiki-s3-tuple/1):
    {"schema": "cognous.wiki-s3-tuple/1", "validation_id": "...", "profile": "process/security-runtime-....json",
     "exchange_compatibility_profile": "...",
     "control_plane": "<40-hex>", "runtime": ..., "replay": ..., "evidence_pack": ..., "odes": ..., "exchange": ..., "manifest": ...,
     "registry": "<40-hex>"}
DIR holds one pristine checkout per name (control_plane, runtime, replay, evidence_pack, odes, exchange, manifest, registry).
The registry checkout is verified and recorded, but the harness neither imports nor exercises it (it is not in COMPONENT_NAMES).

Refusals (exit 2, nothing executed): any value containing PLACEHOLDER / not a 40-hex SHA; a tuple that disagrees with the profile file or the
freeze manifest it names; a checkout whose HEAD != tuple SHA or that is not clean (tools/pristine_checkout.require_pristine); an existing
--out; a nodeids file that is not exactly the committed 41 (count and sorted-unique); collect-only not yielding exactly those ids.
REQUIRES approved patch /tmp/claude-0/sec/s3/cur-generation.patch (suite_generation 'cur'); refuses (symbol check) when it is not applied.
--dry-check performs every check including pytest --collect-only, executes no test and writes nothing under --out.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from pristine_checkout import require_pristine  # noqa: E402

SCHEMA = 'cognous.wiki-s3-tuple/1'
SHA_RE = re.compile(r'[0-9a-f]{40}')
HARNESS = ('control_plane', 'runtime', 'replay', 'evidence_pack', 'odes', 'exchange', 'manifest')
CHECKED = HARNESS + ('registry',)
# tuple key -> (profile components key, freeze-manifest components_subject key)
CFG_MAP = {'control_plane': ('control_plane', 'control_plane'), 'runtime': ('runtime', 'moltbot_safe'), 'replay': ('replay', 'replay_bundle'),
           'evidence_pack': ('evidence_pack', 'governance_evidence_pack'), 'odes': ('odes', 'odes'),
           'exchange': ('exchange', 'gax_imx_transport'), 'manifest': ('manifest', 'action_manifest')}
DEFAULT_NODEIDS = 'process/v1-validation/current-stack-S3-20261031/wiki41-nodeids.txt'  # rename with the directory when filled
OBSERVER = ROOT / 'tools' / 'wiki_exchange_observer.py'
EXPECTED_NODEIDS = 41


class Refuse(Exception):
    pass


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True, timeout=120).strip()


def walk_strings(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(k)
            yield from walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_strings(v)
    elif isinstance(obj, str):
        yield obj


def load_tuple(path):
    raw = json.loads(Path(path).read_text(encoding='utf-8'))
    if raw.get('schema') != SCHEMA:
        raise Refuse(f'tuple schema must be {SCHEMA}')
    for s in walk_strings(raw):
        if 'PLACEHOLDER' in s or 'TEMPLATE' in s:
            raise Refuse(f'tuple still contains a placeholder/template marker: {s[:80]!r}')
    for key in CHECKED:
        v = raw.get(key)
        if not isinstance(v, str) or not SHA_RE.fullmatch(v):
            raise Refuse(f'tuple.{key} must be a 40-character lowercase hex SHA (no branch, tag, prefix or "latest")')
    for key in ('validation_id', 'profile', 'exchange_compatibility_profile'):
        if not isinstance(raw.get(key), str) or not raw[key]:
            raise Refuse(f'tuple.{key} missing')
    return raw


def check_configs(t):
    """The tuple, the profile file and the freeze manifest the harness will read must say the same thing (pins resolved WITHOUT overlay)."""
    prof_path = (ROOT / t['profile']).resolve()
    prof_path.relative_to(ROOT)
    profile = json.loads(prof_path.read_text())
    man_path = ROOT / 'process' / 'v1-validation' / t['validation_id'] / 'freeze-manifest.json'
    manifest = json.loads(man_path.read_text())
    for s in list(walk_strings(profile)) + list(walk_strings(manifest)):
        if 'PLACEHOLDER' in s:
            raise Refuse(f'configuration still contains a placeholder: {s[:80]!r} ({prof_path.name} / {man_path.parent.name})')
    if manifest.get('validation_id') != t['validation_id']:
        raise Refuse('freeze-manifest validation_id != tuple validation_id')
    if (ROOT / 'process' / 'v1-validation' / t['validation_id'] / 'refreeze-log.json').exists():
        raise Refuse('a refreeze-log.json exists for this validation id; the tuple must equal the manifest pins without overlay')
    for key, (pk, mk) in CFG_MAP.items():
        if profile['components'][pk]['revision'] != t[key]:
            raise Refuse(f'profile {pk} revision != tuple.{key}')
        if manifest['components_subject'][mk]['sha'] != t[key]:
            raise Refuse(f'freeze-manifest {mk} sha != tuple.{key}')
    if profile.get('ocs_registry', {}).get('revision') != t['registry'] or manifest['components_lock_remainder']['ocs_registry']['sha'] != t['registry']:
        raise Refuse('registry SHA in profile/freeze-manifest != tuple.registry')
    if profile.get('exchange_compatibility_profile') != t['exchange_compatibility_profile'] or \
            manifest['profile']['exchange_compatibility_profile'] != t['exchange_compatibility_profile']:
        raise Refuse('exchange_compatibility_profile differs between tuple, profile and freeze-manifest')
    if profile.get('suite_generation') != 'cur':
        raise Refuse('profile suite_generation must be "cur" (p2 would stamp the historical 7a4bcd40/c5e97e87 labels = false provenance)')
    require_cur_patch()
    if any(profile.get(k) is not False for k in ('selected', 'reference_release_authorized', 'production_deployment_authorized')):
        raise Refuse('profile must stay nonselected and nonauthorizing')
    return prof_path, man_path


def require_cur_patch():
    """suite_generation 'cur' REQUIRES the approved patch /tmp/claude-0/sec/s3/cur-generation.patch (separate, unapplied by default).
    Detected by symbol presence: 'cur' in SUITE_GENERATIONS (tools/run_security_runtime.py) and the CONTROL_PLANE_CUR_REVISION import
    plus CUR_REVISIONS in the chain harness. Refuses otherwise (a p2 fallback would stamp false 7a4bcd40/c5e97e87 provenance)."""
    import ast
    ok_tool = False
    tree = ast.parse((ROOT / 'tools' / 'run_security_runtime.py').read_text())
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and any(getattr(t, 'id', None) == 'SUITE_GENERATIONS' for t in n.targets):
            ok_tool = any(isinstance(c, ast.Constant) and c.value == 'cur' for c in ast.walk(n.value))
    chain = (ROOT / 'suites' / 'security-runtime' / 'test_security_runtime_chain.py').read_text()
    if not (ok_tool and 'CONTROL_PLANE_CUR_REVISION' in chain and 'MOLTBOT_CUR_REVISION' in chain and 'CUR_REVISIONS' in chain):
        raise Refuse("suite_generation 'cur' requires the approved patch /tmp/claude-0/sec/s3/cur-generation.patch "
                     "(symbols 'cur' in SUITE_GENERATIONS, CONTROL_PLANE_CUR_REVISION, CUR_REVISIONS not found); not applied -> refusing")


def check_checkouts(base, t):
    out = {}
    for name in CHECKED:
        p = Path(base) / name
        if not p.is_dir():
            raise Refuse(f'missing checkout {p}')
        try:
            require_pristine(p, t[name], name)
        except ValueError as e:
            raise Refuse(str(e))
        out[name] = {'path': str(p.resolve()), 'head': t[name], 'tree': git(p, 'rev-parse', 'HEAD^{tree}')}
    return out


def read_nodeids(path):
    ids = [l for l in Path(path).read_text().splitlines() if l.strip()]
    if len(ids) != EXPECTED_NODEIDS or len(set(ids)) != EXPECTED_NODEIDS:
        raise Refuse(f'nodeids file must hold exactly {EXPECTED_NODEIDS} unique ids, has {len(ids)}/{len(set(ids))}')
    if any(not i.startswith('suites/wiki-derived/') for i in ids):
        raise Refuse('every node id must be under suites/wiki-derived/')
    return ids


def child_env(t, base, hub, obs_out):
    env = dict(os.environ)
    for k in [k for k in env if k.startswith(('PYTEST_', 'V1_', 'SCN_', 'OBS_', 'GAX_', 'COGNOUS_', 'MOLTBOT_', 'UPSTREAM_'))]:
        del env[k]
    env.update(PYTHONDONTWRITEBYTECODE='1', SCN_COMPONENTS_DIR=str(Path(base).resolve()), V1_VALIDATION_ID=t['validation_id'],
               V1_PROFILE=t['profile'], PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', OBS_OUT=str(obs_out),
               PYTHONPATH=str(ROOT / 'tools'))
    if hub:
        env['SCN_HUB_DIR'] = str(Path(hub).resolve())
    return env


def pytest_cmd(ids, extra):
    return [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-p', 'wiki_exchange_observer', '-o', 'junit_family=xunit1',
            '-rA', *extra, *ids]  # no -x, no --reruns, no -n: a single pytest process runs every id exactly once


def collect_only(ids, env):
    cmd = pytest_cmd(ids, ['--collect-only'])
    r = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=900)
    got = [l.strip() for l in r.stdout.splitlines() if '::' in l]
    if r.returncode != 0 or sorted(got) != sorted(ids):
        raise Refuse('collect-only did not yield exactly the 41 node ids '
                     f'(rc={r.returncode}, got {len(got)}, missing {sorted(set(ids) - set(got))[:3]}, extra {sorted(set(got) - set(ids))[:3]}): {r.stdout[-400:]} {r.stderr[-400:]}')
    return r.stdout, cmd


def tool_versions():
    v = {'python': sys.version, 'platform': platform.platform(), 'machine': platform.machine(), 'cpu_count': os.cpu_count(),
         'git': subprocess.check_output(['git', '--version'], text=True).strip()}
    try:
        v['pip_freeze'] = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True, timeout=120).splitlines()
    except Exception as e:  # recorded, not hidden
        v['pip_freeze'] = f'UNAVAILABLE: {type(e).__name__}'
    try:
        import pytest
        v['pytest'] = pytest.__version__
    except Exception:
        v['pytest'] = 'UNAVAILABLE'
    return v


def qual_status(exclude=None):
    rows = [l for l in git(ROOT, 'status', '--porcelain', '--untracked-files=all').splitlines() if l]
    if exclude:
        ex = Path(exclude).resolve()
        rows = [l for l in rows if not (ROOT / l[3:].strip('"')).resolve().is_relative_to(ex)]
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tuple', type=Path, required=True)
    ap.add_argument('--components', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--hub', type=Path, default=None, help='pristine hub checkout (optional; verified at the profile hub head if given)')
    ap.add_argument('--nodeids', type=Path, default=ROOT / DEFAULT_NODEIDS)
    ap.add_argument('--dry-check', action='store_true', help='every check incl. pytest --collect-only; no test runs; writes nothing')
    a = ap.parse_args(argv)
    try:
        t = load_tuple(a.tuple)
        prof_path, man_path = check_configs(t)
        if a.out.exists():
            raise Refuse('--out must be new (one-shot: evidence directories are never reused)')
        if qual_status() and not a.dry_check:  # a dry check only reports a dirty tree; a real run refuses
            raise Refuse('qualification worktree is not clean: ' + '; '.join(qual_status()[:5]))
        ids = read_nodeids(a.nodeids)
        checkouts = check_checkouts(a.components, t)
        if a.hub:
            hub_head = json.loads(man_path.read_text())['identities']['hub']['head']
            require_pristine(a.hub, hub_head, 'hub')
        obs = (a.out / 'raw' / 'obs.json') if not a.dry_check else Path(os.devnull)
        env = child_env(t, a.components, a.hub, obs)
        # S3 fix: the observer writes OBS_OUT at pytest sessionfinish, also for --collect-only; the real out/raw dir does not exist yet, so collect with a null sink (as --dry-check always did)
        listing, _ = collect_only(ids, child_env(t, a.components, a.hub, Path(os.devnull)))
    except Refuse as e:
        print('REFUSED:', e, file=sys.stderr)
        return 2
    except (ValueError, KeyError, OSError, subprocess.SubprocessError) as e:
        print(f'REFUSED: {type(e).__name__}: {e}', file=sys.stderr)
        return 2
    if a.dry_check:
        print(json.dumps({'dry_check': 'OK', 'collected': len(ids), 'executed': 0, 'checkouts': {k: v['head'] for k, v in checkouts.items()},
                          'qualification_dirty_rows': len(qual_status())}, indent=1))
        return 0

    raw = a.out / 'raw'
    raw.mkdir(parents=True)
    (raw / 'collect-only.txt').write_text(listing)
    (raw / 'nodeids-41.txt').write_text('\n'.join(ids) + '\n')
    (raw / 'tuple.json').write_text(Path(a.tuple).read_text())
    start = datetime.now(timezone.utc).isoformat()
    cmd = pytest_cmd(ids, [f'--junitxml={raw / "junit.xml"}', f'--basetemp={raw / "native"}'])
    with (raw / 'log.txt').open('w') as stream:
        rc = subprocess.run(cmd, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=7200).returncode
    end = datetime.now(timezone.utc).isoformat()
    problems = []
    for name in CHECKED:
        try:
            require_pristine(checkouts[name]['path'], t[name], name)
        except ValueError as e:
            problems.append(str(e))
    cases = list(ET.parse(raw / 'junit.xml').getroot().iter('testcase'))
    ran = sorted(f"{c.get('classname')}::{c.get('name')}" for c in cases)
    counts = {'testcase_elements': len(cases), **{k: sum(c.find(k) is not None for c in cases) for k in ('failure', 'error', 'skipped')}}
    record = {
        'label': 'Security Wiki S3 run record (generation-2 current-stack tuple); non-authorizing; verdicts are assigned by the analysis, not by pytest exit code',
        'tuple': t, 'pytest_command': cmd, 'pytest_returncode': rc, 'attempts': 1, 'retries': 0, 'workers': 1,
        'started_utc': start, 'finished_utc': end, 'junit_counts': counts, 'testcase_elements_expected': EXPECTED_NODEIDS,
        'checkouts_after_run_pristine': not problems, 'checkout_problems': problems, 'checkouts': checkouts,
        'qualification_head': git(ROOT, 'rev-parse', 'HEAD'), 'qualification_tree': git(ROOT, 'rev-parse', 'HEAD^{tree}'),
        'qualification_worktree_dirty_after': qual_status(exclude=a.out),
        'config_hashes': {str(p.relative_to(ROOT)): sha256(p) for p in (prof_path, man_path, man_path.parent / 'tuple.json', a.nodeids.resolve(), OBSERVER, Path(__file__).resolve())
                          if p.exists()},
        'harness_source_hashes': {str(p.relative_to(ROOT)): sha256(p) for p in sorted((ROOT / 'suites' / 'wiki-derived').glob('*.py')) + sorted((ROOT / 'suites' / 'v1-scenarios').glob('*.py')) + sorted((ROOT / 'suites' / 'security-runtime').glob('*.py')) + [ROOT / 'suites' / '_pins.py', ROOT / 'suites' / '_contract_matrix.py']},
        'environment': tool_versions(),
        'note': 'The registry checkout is verified pristine and recorded; no test in this run exercises it (see the separate registry probe).',
    }
    (raw / 'run.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
    sums = '\n'.join(f'{sha256(p)}  ./{p.relative_to(a.out).as_posix()}' for p in sorted(a.out.rglob('*')) if p.is_file() and p.name != 'SHA256SUMS')
    (a.out / 'SHA256SUMS').write_text(sums + '\n')
    print(json.dumps({'returncode': rc, 'junit_counts': counts, 'pristine_after': not problems, 'out': str(a.out)}, indent=1))
    return 0 if (not problems and len(cases) == EXPECTED_NODEIDS) else 1


if __name__ == '__main__':
    raise SystemExit(main())
