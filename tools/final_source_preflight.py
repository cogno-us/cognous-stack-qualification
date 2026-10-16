"""Inspect actual merged-source admission without changing compatibility mappings.

SPDX-License-Identifier: Apache-2.0
This is a preflight, not scenario execution, qualification, or release selection.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pristine_checkout import require_pristine


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    profile = json.loads(args.profile.read_text())
    if profile['selected'] is not False or any(profile[k] is not False for k in (
        'reference_release_authorized', 'production_deployment_authorized'
    )):
        raise ValueError('Source probe must remain nonselected and nonauthorizing')
    if args.out.exists():
        raise ValueError('Refusing to replace retained evidence')
    work = args.work.resolve()
    pins = {}
    for name, spec in profile['components'].items():
        path = work/name
        actual = require_pristine(path, spec['sha'], f'Unclean or mismatched source: {name}')
        pins[name] = {'repository': spec['repository'], 'sha': actual,
                      'tree': git(path, 'rev-parse', 'HEAD^{tree}')}
    for relative in ('control_plane/src', 'moltbot_safe', 'replay_bundle/src',
                     'odes/src', 'governance_evidence_pack/src', 'gax_imx_transport'):
        sys.path.insert(0, str(work/relative))
    os.environ.update(
        GAX_RUNTIME_COMPATIBILITY_PROFILE=profile['runtime_profile'],
        MOLTBOT_SAFE_CONTROL_PLANE_ROOT=str(work/'control_plane'),
        MOLTBOT_SAFE_ROOT=str(work/'moltbot_safe'),
        UPSTREAM_MANIFEST_EXAMPLE=str(work/'action_manifest/examples/refund_integration_v1_1.manifest.json'),
    )
    modules = {}
    for name in ('agent_replay_bundle.importers', 'odes.common',
                 'agent_governance_evidence_pack.importer',
                 'experiments.odex_gax_imx_reference.gax_ref_runtime'):
        module = importlib.import_module(name)
        path = Path(module.__file__).resolve()
        if not path.is_relative_to(work):
            raise ValueError('Import escaped pinned source checkouts: '+name)
        modules[name] = module
    replay = modules['agent_replay_bundle.importers']
    odes = modules['odes.common']
    pack = modules['agent_governance_evidence_pack.importer']
    exchange = modules['experiments.odex_gax_imx_reference.gax_ref_runtime']
    expected = dict(control_plane=exchange.CP_REVISION, moltbot_safe=exchange.MOLTBOT_REVISION,
                    replay_bundle=exchange.REPLAY_REVISION, odes=exchange.ODES_REVISION,
                    governance_evidence_pack=exchange.EVIDENCE_PACK_REVISION,
                    action_manifest=exchange.MANIFEST_REVISION)
    checks = []
    for name, required in expected.items():
        checks.append({'check': 'exchange_exact_source/'+name,
                       'expected_revision': required, 'observed_revision': pins[name]['sha'],
                       'passed': pins[name]['sha'] == required})
    cp = pins['control_plane']['sha']
    for name, supported in (
        ('replay_control_plane_admission', [replay.CONTROL_PLANE_REVISION, *replay.CONTROL_PLANE_SUPPORTED_V2_REVISIONS]),
        ('odes_control_plane_admission', [odes.PINNED_REVISIONS['control_plane'], *odes.ALL_V2_CONTROL_PLANE_REVISIONS]),
        ('evidence_pack_control_plane_admission', [pack.CONTROL_PLANE_REVISION, *pack.ALL_CONTROL_PLANE_V2_REVISIONS]),
    ):
        checks.append({'check': name, 'observed_revision': cp,
                       'supported_revisions': supported, 'passed': cp in supported})
    invocations = []
    for name, operation in (
        ('exchange_load_executor_runtime', exchange.load_executor_runtime),
        ('replay_current_control_plane', lambda: replay.import_bounded_workflow({}, control_plane_revision=cp)),
    ):
        try:
            operation()
        except (RuntimeError, ValueError) as error:
            invocations.append({'operation': name, 'exception': type(error).__name__, 'message': str(error)})
        else:
            invocations.append({'operation': name, 'exception': None, 'message': 'No admission exception'})
    result = {
        'schema': 'cognous.final-source-preflight/1',
        'profile_sha256': digest(args.profile), 'runner_sha256': digest(Path(__file__)),
        'python': sys.version, 'pins': pins,
        'loaded_sources': {name: {'path': str(Path(m.__file__).resolve().relative_to(work)),
                                 'sha256': digest(Path(m.__file__))} for name, m in modules.items()},
        'checks': checks, 'invocations': invocations,
        'source_admission_passed': all(c['passed'] for c in checks),
        'scenario_execution': 'NOT RUN: source admission prerequisite fails',
        'actual_effects_executed': False,
        'selected': False, 'reference_release_authorized': False,
        'production_deployment_authorized': False,
        'limitations': [
            'Admission mapping inspection and two actual API refusals only; no scenario success is asserted.',
            'The empty Replay record probes revision rejection before payload parsing; it is not a valid execution fixture.',
            'No compatibility constants, source revisions, tests or validation rules were patched.',
        ],
    }
    for name, spec in profile['components'].items():
        if git(work/name, 'rev-parse', 'HEAD') != spec['sha'] or git(work/name, 'status', '--porcelain', '--untracked-files=all'):
            raise ValueError('Source changed during preflight: '+name)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'source_admission_passed': result['source_admission_passed'],
                      'checks': len(checks), 'failed': sum(not c['passed'] for c in checks),
                      'scenario_execution': result['scenario_execution']}))
    return 0 if result['source_admission_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
