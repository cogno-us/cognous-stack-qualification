"""Shared refusal of non-pristine source checkouts before their code is executed.

SPDX-License-Identifier: Apache-2.0
A HEAD comparison alone does not bind executed bytes: modified, untracked or
ignored files, and index flags that hide modifications, can all shadow the
pinned tree. Local runners therefore require fresh runner-owned clones.
This check does not authenticate a compromised host or exclude concurrent writers.
"""
from __future__ import annotations
from pathlib import Path
import subprocess


def _git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True, timeout=60)


def require_pristine(path, revision, label=None):
    """Return HEAD of ``path`` or raise ValueError unless it is exactly ``revision`` with nothing extra."""
    path = Path(path)
    label = label or path.name
    if _git(path, 'rev-parse', 'HEAD').strip() != revision:
        raise ValueError(f'{label}: source revision mismatch')
    # Modified, staged, untracked and ignored files (including bytecode) all count.
    if _git(path, 'status', '--porcelain', '--untracked-files=all', '--ignored'):
        raise ValueError(f'{label}: checkout is not pristine (modified, untracked or ignored files); use a fresh runner-owned clone')
    # git status trusts index flags: assume-unchanged (lowercase tag) and skip-worktree (S) hide edits.
    for row in _git(path, 'ls-files', '-v', '-z').split('\0'):
        if row and (row[0].islower() or row[0] == 'S'):
            raise ValueError(f'{label}: assume-unchanged or skip-worktree entries hide modifications; use a fresh runner-owned clone')
    return revision
