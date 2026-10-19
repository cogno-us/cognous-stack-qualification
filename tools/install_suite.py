"""Assemble relocated test files into a disposable owning-repository checkout.

SPDX-License-Identifier: Apache-2.0
Never changes production code, dependency pins or test assertions. Both Git
identities and overlay hashes must accompany any resulting evidence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'migrations/cross-component-2026-10-15.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def checked_path(root, relative):
    parts = PurePosixPath(relative)
    if parts.is_absolute() or '..' in parts.parts or '.git' in parts.parts:
        raise ValueError('Unsafe migration path: ' + relative)
    path = root.joinpath(*parts.parts)
    current = root
    for part in parts.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('Symlink in migration target: ' + str(current))
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Escaping migration path')
    return path


def install(suite, source_root, *, evidence, historical_only=False, manifest=MANIFEST, qualification_root=ROOT):
    source_root = source_root.resolve()
    if source_root == qualification_root.resolve():
        raise ValueError('Refusing to overlay the canonical qualification checkout')
    if Path(git(source_root, 'rev-parse', '--show-toplevel')).resolve() != source_root:
        raise ValueError('Source root must be a Git checkout root')
    data = json.loads(manifest.read_text())
    spec = data['repositories'][suite]
    source_head = git(source_root, 'rev-parse', 'HEAD')
    suite_head = git(qualification_root, 'rev-parse', 'HEAD')
    planned = []
    for row in spec['files']:
        original = checked_path(qualification_root, row['destination_path'])
        if digest(original) != row['destination_sha256']:
            raise ValueError('Canonical suite file differs from migration record: ' + row['destination_path'])
        if historical_only:
            continue
        target = checked_path(source_root, row['source_path'])
        accepted_sources={row['source_sha256'],*(entry['sha256'] for entry in row.get('reconciled_sources',[]))}
        if target.exists() and digest(target) not in accepted_sources:
            # Source CI stubs deliberately replace original workflows, never test implementations.
            wrapper = (row['action'] == 'delegate' and target.read_text().startswith('# Cross-component suite delegated to its canonical testing repository.\n'))
            if not wrapper:
                raise ValueError('Source file advanced after inventory; refusing to overwrite: ' + row['source_path'])
        planned.append((original, target, row))
    if evidence.exists():
        raise ValueError('Relocation evidence already exists; use a fresh run directory')
    report = {'schema_version':'1.0.0', 'owning_repository':spec['repository'],
              'owning_source_commit':source_head, 'migration_origin_commit':spec['source_commit'],
              'qualification_repository':'cogno-us/cognous-stack-qualification',
              'qualification_commit':suite_head, 'qualification_worktree_dirty':bool(git(qualification_root,'status','--porcelain','--untracked-files=all')), 'migration_manifest_sha256':digest(manifest),
              'historical_frozen_source':historical_only, 'overlay':[],
              'qualification_claim':'NONE: assembly is not execution or acceptance',
              'source_status_before_assembly':git(source_root,'status','--porcelain','--untracked-files=all')}
    for original, target, row in planned:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(original.read_bytes())
        target.chmod(0o755 if row.get('source_mode')=='100755' else 0o644)
        report['overlay'].append({'path':row['source_path'], 'sha256':digest(target), 'source_url':row['source_url'], 'license':row['license']})
    report['source_status_after_assembly'] = git(source_root,'status','--porcelain','--untracked-files=all')
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps(report,indent=2)+'\n')
    return report


def provision_dependency_locks(source_root, qualification_root=ROOT):
    """Make the qualification repository's hash-locked dependency sets available to the workflows' install steps.

    The delegating workflows install with ``pip install --require-hashes -r .github/locks/<set>.txt`` relative to the checkout
    they run in. A source repository has no such directory, so the sets are copied beside the overlaid suite files, byte for
    byte, and recorded. Nothing is generated and no dependency is chosen here; an existing file with different bytes is refused.
    """
    source_root = source_root.resolve()
    origin = qualification_root / '.github/locks'
    if not origin.is_dir():
        return []
    destination = checked_path(source_root, '.github/locks')
    destination.mkdir(parents=True, exist_ok=True)
    copied = []
    for path in sorted(origin.iterdir()):
        if not path.is_file() or path.suffix not in {'.txt', '.in'}:
            continue
        target = checked_path(source_root, '.github/locks/' + path.name)
        if target.exists() and digest(target) != digest(path):
            raise ValueError('Dependency lock differs from the qualification lock; refusing to overwrite: ' + path.name)
        target.write_bytes(path.read_bytes())
        target.chmod(0o644)
        copied.append({'path': '.github/locks/' + path.name, 'sha256': digest(target)})
    return copied


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', required=True)
    parser.add_argument('--source-root', required=True, type=Path)
    parser.add_argument('--evidence', required=True, type=Path)
    parser.add_argument('--historical-only', action='store_true')
    args = parser.parse_args()
    result = install(args.suite, args.source_root, evidence=args.evidence, historical_only=args.historical_only)
    if not args.historical_only:
        result['dependency_locks'] = provision_dependency_locks(args.source_root)
        args.evidence.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'source_commit':result['owning_source_commit'], 'qualification_commit':result['qualification_commit'], 'installed_files':len(result['overlay']), 'qualification_claim':'NONE'}))


if __name__ == '__main__':
    main()
