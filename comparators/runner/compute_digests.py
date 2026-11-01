#!/usr/bin/env python3
"""Digests of the files of the comparison runner (sha256, repository-relative paths). The file digests.json lists every file under
comparators/runner except itself, test caches and compiled files.

  python3 comparators/runner/compute_digests.py          write digests.json
  python3 comparators/runner/compute_digests.py --check  list differences, unlisted files and missing files (exit status 1 if any)
"""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / 'digests.json'


def files():
    return sorted(p for p in HERE.rglob('*') if p.is_file() and p != OUT and '__pycache__' not in p.parts and p.suffix != '.pyc')


def compute():
    return {p.relative_to(REPO).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files()}


def check():
    listed = json.loads(OUT.read_text())['files']
    now = compute()
    problems = ['differs: ' + k for k in listed if k in now and now[k] != listed[k]]
    problems += ['missing: ' + k for k in listed if k not in now]
    problems += ['unlisted: ' + k for k in now if k not in listed]
    return problems


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if '--check' in argv:
        problems = check()
        print('\n'.join(problems) or 'digests current')
        return 1 if problems else 0
    OUT.write_text(json.dumps(dict(schema='cognous.comparators-runner-digests/1', files=compute()), indent=1) + '\n')
    print('wrote %s (%d files)' % (OUT.relative_to(REPO), len(compute())))
    return 0


if __name__ == '__main__':
    sys.exit(main())
