#!/usr/bin/env python3
"""Pre-flight guard for the Security Wiki S3 run (OCS-254-S3). Non-authorizing; read-only; stdlib only.

SPDX-License-Identifier: Apache-2.0
Why it exists: s3/run_wiki_s3.py checks that tuple, profile file and freeze manifest AGREE WITH EACH OTHER and that every checkout
equals the tuple, but it does not know WHICH tuple is the intended one. A consistently wrong Exchange profile name or a consistently
mixed-generation set (e.g. Replay 40012b8c in all three files and in the checkout) passes `run_wiki_s3.py --dry-check`
(recorded in results/security-wiki-s3-20261031/run-41-merged-tuple-controls/). This guard pins the intended final tuple and refuses
any deviation. The runner itself is NOT modified (cur-patch verification A-J relies on that).

    python3 s3/s3_tuple_guard.py --tuple process/v1-validation/current-stack-S3-20261031/runner-tuple.json --components DIR

Exit 0 only if everything equals EXPECTED; exit 2 with REFUSED on stderr otherwise. The CLI writes nothing.

MANDATORY PREFLIGHT (OCS-254-S3 closeout, D5): s3/run_wiki_s3.py calls run_guard() as its FIRST step for every execution, --dry-check included,
and there is no flag, environment variable or option that skips it. run_guard() returns a guard-result record (schema
cognous.wiki-s3-guard-result/1) with `preflight_guard: passed|refused`, the guard file sha256, the tuple sha256, inputs, a per-check result
list and the UTC time; the runner retains it (raw/guard-result.json for a real run, <out>-REFUSED/guard-result.json for a refused real run).
The C1 run (freeze b48675b7) pre-dates this integration; see results/security-wiki-s3-20261031/GUARD-NOTE.md.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATION_ID = 'current-stack-S3-20261031'
EXCHANGE_PROFILE = 'security-runtime-current-20261031-r2'
# name -> (commit, tree), lead-verified on GitHub/git 2026-10-31
EXPECTED = {
    'control_plane': ('b19c47ddd020409d24e52e70b11359c46265edbb', '039219b5aba7a157fff79781c716067fad7ed985'),
    'runtime': ('f7a55e2a8494801e49193f9f46935f0a971c248d', '97da8323368bb5a573fd157b11a9c1dda1178a10'),
    'replay': ('d395e37c443fedf1bf6b9a4651338b7b7de4a553', '0bdee3eacd650ecb0e99781635a972e68cbe2853'),
    'evidence_pack': ('96f5f2e126a9c27a75716658d4d2e85baf94b40b', '2fc26d4c86e65b22bdffedf1090a15e7167440d3'),
    'odes': ('77fd7a1cb1dd7a2dbc9ac3c02538a617056688ae', 'd8b33261de975fc504ff8f0ac30a8f47e8ebd43f'),
    'exchange': ('746378d74bff59314bdcf8f0b50b19ab94679ba9', 'dcbe909f96d7c83e6281c5679283bd65cf19dbdb'),
    'manifest': ('fa170815ef96a54c233d0dd9da821b60debabf8b', '3b0e3772e944aa668c8f4b879588c7cc3e2c32be'),
    'registry': ('6b96a9a658923954433dc1a4c13626fa5145b9c7', '38d50602ae725e208f010baba05bbf7b908e76ac'),
}
# tuple key -> (profile components key, freeze-manifest components_subject key)
CFG = {'control_plane': ('control_plane', 'control_plane'), 'runtime': ('runtime', 'moltbot_safe'), 'replay': ('replay', 'replay_bundle'),
       'evidence_pack': ('evidence_pack', 'governance_evidence_pack'), 'odes': ('odes', 'odes'),
       'exchange': ('exchange', 'gax_imx_transport'), 'manifest': ('manifest', 'action_manifest')}
# Exchange constant -> tuple key it must equal inside the r2 profile block
EXCHANGE_CONSTANTS = {'CP_REVISION': 'control_plane', 'MOLTBOT_REVISION': 'runtime', 'MANIFEST_REVISION': 'manifest',
                      'REPLAY_REVISION': 'replay', 'ODES_REVISION': 'odes', 'EVIDENCE_PACK_REVISION': 'evidence_pack'}


RESULT_SCHEMA = 'cognous.wiki-s3-guard-result/1'
SHA_RE = re.compile(r'[0-9a-f]{40}')


class Refuse(Exception):
    pass


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True, timeout=120).strip()


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


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


def exchange_block(src, profile):
    m = re.search(r'RUNTIME_COMPATIBILITY_PROFILE\s*==\s*"%s":(.*?)(?=\nelif |\nelse:|\nif )' % re.escape(profile), src, re.S)
    if not m:
        raise Refuse(f'Exchange source does not define profile {profile!r}')
    consts = dict(re.findall(r'^\s+([A-Z_]+_REVISION)\s*=\s*"([0-9a-f]{40})"', m.group(1), re.M))
    return consts


def run_guard(tuple_path, components, root=ROOT):
    """Run every check; stop at the first failure. Returns the guard-result record (never raises for a refusal). Read-only."""
    tuple_path, components, root = Path(tuple_path), Path(components), Path(root)
    checks = []
    inputs = {'tuple_path': str(tuple_path), 'components_dir': str(components), 'root': str(root)}
    result = {'schema': RESULT_SCHEMA, 'label': 'S3 mandatory preflight tuple guard result; non-authorizing',
              'preflight_guard': 'refused', 'refusal_reason': None, 'validation_id': VALIDATION_ID, 'exchange_profile_required': EXCHANGE_PROFILE,
              'guard_file': {'path': 's3/s3_tuple_guard.py', 'sha256': sha256_file(__file__)},
              'tuple_sha256': None, 'inputs': inputs, 'checks': checks,
              'expected': {k: {'commit': v[0], 'tree': v[1]} for k, v in EXPECTED.items()}, 'utc_time': None}

    def need(cid, cond, msg):
        checks.append({'check': cid, 'result': 'pass' if cond else 'fail', **({} if cond else {'reason': msg})})
        if not cond:
            raise Refuse(msg)

    try:
        raw = tuple_path.read_bytes()
        result['tuple_sha256'] = hashlib.sha256(raw).hexdigest()
        t = json.loads(raw.decode('utf-8'))
        need('tuple_is_object', isinstance(t, dict), 'tuple is not a JSON object')
        bad = [s for s in walk_strings(t) if 'PLACEHOLDER' in s or 'TEMPLATE' in s]
        need('tuple_no_placeholder', not bad, f'unresolved placeholder/template marker in tuple: {bad[:1]!r}')
        need('tuple_validation_id', t.get('validation_id') == VALIDATION_ID, f'validation_id != {VALIDATION_ID}')
        need('tuple_exchange_profile', t.get('exchange_compatibility_profile') == EXCHANGE_PROFILE,
             f'wrong Exchange profile in tuple: {t.get("exchange_compatibility_profile")!r} (required {EXCHANGE_PROFILE!r})')
        for k in EXPECTED:
            v = t.get(k)
            need(f'tuple_sha_format.{k}', isinstance(v, str) and bool(SHA_RE.fullmatch(v)), f'tuple.{k} is not a 40-hex SHA: {v!r}')
        for k, (sha, _) in EXPECTED.items():
            need(f'tuple_pin.{k}', t.get(k) == sha, f'tuple.{k} {t.get(k)!r} != intended {sha} (mixed-generation or substituted component)')
        profile_path, man_path = root / t['profile'], root / 'process' / 'v1-validation' / VALIDATION_ID / 'freeze-manifest.json'
        profile_raw, man_raw = profile_path.read_bytes(), man_path.read_bytes()
        inputs.update(profile_path=str(profile_path), profile_sha256=hashlib.sha256(profile_raw).hexdigest(),
                      freeze_manifest_path=str(man_path), freeze_manifest_sha256=hashlib.sha256(man_raw).hexdigest())
        profile, man = json.loads(profile_raw), json.loads(man_raw)
        bad = [s for s in list(walk_strings(profile)) + list(walk_strings(man)) if 'PLACEHOLDER' in s or 'TEMPLATE' in s]
        need('config_no_placeholder', not bad, f'unresolved placeholder/template marker in profile/freeze-manifest: {bad[:1]!r}')
        need('profile_exchange_profile', profile.get('exchange_compatibility_profile') == EXCHANGE_PROFILE, 'profile file: wrong Exchange profile')
        need('manifest_exchange_profile', man['profile']['exchange_compatibility_profile'] == EXCHANGE_PROFILE, 'freeze-manifest: wrong Exchange profile')
        need('profile_suite_generation', profile.get('suite_generation') == 'cur', 'profile suite_generation != cur')
        for k, (pk, mk) in CFG.items():
            need(f'profile_pin.{k}', profile['components'][pk]['revision'] == EXPECTED[k][0], f'profile.{pk} revision != intended')
            need(f'manifest_pin.{k}', man['components_subject'][mk]['sha'] == EXPECTED[k][0], f'freeze-manifest.{mk} sha != intended')
        need('config_pin.registry', profile['ocs_registry']['revision'] == EXPECTED['registry'][0], 'profile registry != intended')
        need('manifest_tree.exchange', man['verified_trees']['trees'].get('exchange') == EXPECTED['exchange'][1], 'freeze-manifest exchange tree != intended')
        for k, (sha, tree) in EXPECTED.items():
            p = components / k
            need(f'checkout_present.{k}', p.is_dir(), f'missing checkout {p}')
            need(f'checkout_head.{k}', git(p, 'rev-parse', 'HEAD') == sha, f'{k}: checkout HEAD != intended {sha}')
            need(f'checkout_tree.{k}', git(p, 'rev-parse', 'HEAD^{tree}') == tree, f'{k}: checkout tree != intended {tree}')
            need(f'checkout_pristine.{k}', not git(p, 'status', '--porcelain', '--untracked-files=all', '--ignored'), f'{k}: checkout is not pristine')
        src = (components / 'exchange' / 'experiments' / 'odex_gax_imx_reference' / 'gax_ref_runtime.py').read_text()
        consts = exchange_block(src, EXCHANGE_PROFILE)
        for c, k in EXCHANGE_CONSTANTS.items():
            need(f'exchange_constant.{c}', consts.get(c) == EXPECTED[k][0], f'Exchange profile {EXCHANGE_PROFILE} constant {c}={consts.get(c)!r} != tuple {k} {EXPECTED[k][0]}')
        result['preflight_guard'] = 'passed'
    except Refuse as e:
        result['refusal_reason'] = str(e)
    except (KeyError, OSError, ValueError, TypeError, AttributeError, subprocess.SubprocessError) as e:
        result['refusal_reason'] = f'{type(e).__name__}: {e}'
        checks.append({'check': 'guard_input_error', 'result': 'fail', 'reason': result['refusal_reason']})
    result['utc_time'] = datetime.now(timezone.utc).isoformat()
    return result


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--tuple', type=Path, required=True)
    ap.add_argument('--components', type=Path, required=True)
    a = ap.parse_args(argv)
    r = run_guard(a.tuple, a.components)
    if r['preflight_guard'] != 'passed':
        print('REFUSED:', r['refusal_reason'], file=sys.stderr)
        return 2
    print(json.dumps({'tuple_guard': 'OK', 'validation_id': VALIDATION_ID, 'exchange_profile': EXCHANGE_PROFILE,
                      'checked': {k: {'commit': v[0], 'tree': v[1]} for k, v in EXPECTED.items()}}, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
