#!/usr/bin/env python3
"""Pre-flight guard for the Security Wiki S3 run (OCS-254-S3). Non-authorizing; read-only; stdlib only.

SPDX-License-Identifier: Apache-2.0
Why it exists: s3/run_wiki_s3.py checks that tuple, profile file and freeze manifest AGREE WITH EACH OTHER and that every checkout
equals the tuple, but it does not know WHICH tuple is the intended one. A consistently wrong Exchange profile name or a consistently
mixed-generation set (e.g. Replay 40012b8c in all three files and in the checkout) passes `run_wiki_s3.py --dry-check`
(recorded in results/security-wiki-s3-20261031/run-41-merged-tuple-controls/). This guard pins the intended final tuple and refuses
any deviation. The runner itself is NOT modified (cur-patch verification A-J relies on that).

    python3 s3/s3_tuple_guard.py --tuple process/v1-validation/current-stack-S3-20261031/runner-tuple.json --components DIR

Exit 0 only if everything equals EXPECTED; exit 2 with REFUSED on stderr otherwise. Writes nothing.
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
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


class Refuse(Exception):
    pass


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True, timeout=120).strip()


def need(cond, msg):
    if not cond:
        raise Refuse(msg)


def exchange_block(src, profile):
    m = re.search(r'RUNTIME_COMPATIBILITY_PROFILE\s*==\s*"%s":(.*?)(?=\nelif |\nelse:|\nif )' % re.escape(profile), src, re.S)
    need(m, f'Exchange source does not define profile {profile!r}')
    consts = dict(re.findall(r'^\s+([A-Z_]+_REVISION)\s*=\s*"([0-9a-f]{40})"', m.group(1), re.M))
    return consts


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--tuple', type=Path, required=True)
    ap.add_argument('--components', type=Path, required=True)
    a = ap.parse_args(argv)
    try:
        t = json.loads(a.tuple.read_text())
        need(t.get('validation_id') == VALIDATION_ID, f'validation_id != {VALIDATION_ID}')
        need(t.get('exchange_compatibility_profile') == EXCHANGE_PROFILE, f'wrong Exchange profile in tuple: {t.get("exchange_compatibility_profile")!r} (required {EXCHANGE_PROFILE!r})')
        for k, (sha, _) in EXPECTED.items():
            need(t.get(k) == sha, f'tuple.{k} {t.get(k)!r} != intended {sha} (mixed-generation or substituted component)')
        profile = json.loads((ROOT / t['profile']).read_text())
        man = json.loads((ROOT / 'process' / 'v1-validation' / VALIDATION_ID / 'freeze-manifest.json').read_text())
        need(profile.get('exchange_compatibility_profile') == EXCHANGE_PROFILE, 'profile file: wrong Exchange profile')
        need(man['profile']['exchange_compatibility_profile'] == EXCHANGE_PROFILE, 'freeze-manifest: wrong Exchange profile')
        need(profile.get('suite_generation') == 'cur', 'profile suite_generation != cur')
        for k, (pk, mk) in CFG.items():
            need(profile['components'][pk]['revision'] == EXPECTED[k][0], f'profile.{pk} revision != intended')
            need(man['components_subject'][mk]['sha'] == EXPECTED[k][0], f'freeze-manifest.{mk} sha != intended')
        need(profile['ocs_registry']['revision'] == EXPECTED['registry'][0], 'profile registry != intended')
        need(man['verified_trees']['trees'].get('exchange') == EXPECTED['exchange'][1], 'freeze-manifest exchange tree != intended')
        for k, (sha, tree) in EXPECTED.items():
            p = a.components / k
            need(p.is_dir(), f'missing checkout {p}')
            need(git(p, 'rev-parse', 'HEAD') == sha, f'{k}: checkout HEAD != intended {sha}')
            need(git(p, 'rev-parse', 'HEAD^{tree}') == tree, f'{k}: checkout tree != intended {tree}')
            need(not git(p, 'status', '--porcelain', '--untracked-files=all', '--ignored'), f'{k}: checkout is not pristine')
        src = (a.components / 'exchange' / 'experiments' / 'odex_gax_imx_reference' / 'gax_ref_runtime.py').read_text()
        consts = exchange_block(src, EXCHANGE_PROFILE)
        for c, k in EXCHANGE_CONSTANTS.items():
            need(consts.get(c) == EXPECTED[k][0], f'Exchange profile {EXCHANGE_PROFILE} constant {c}={consts.get(c)!r} != tuple {k} {EXPECTED[k][0]}')
    except Refuse as e:
        print('REFUSED:', e, file=sys.stderr)
        return 2
    except (KeyError, OSError, ValueError, subprocess.SubprocessError) as e:
        print(f'REFUSED: {type(e).__name__}: {e}', file=sys.stderr)
        return 2
    print(json.dumps({'tuple_guard': 'OK', 'validation_id': VALIDATION_ID, 'exchange_profile': EXCHANGE_PROFILE,
                      'checked': {k: {'commit': v[0], 'tree': v[1]} for k, v in EXPECTED.items()}}, indent=1))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
