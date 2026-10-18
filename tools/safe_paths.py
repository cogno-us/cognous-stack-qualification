"""Path-safety helpers for evidence export (kept out of trajectory_contract.py, whose bytes retained evidence commits to).

SPDX-License-Identifier: Apache-2.0
"""
import os
from pathlib import Path
import stat


def safe_relative_name(name):
    """A source or artifact name must be a plain relative path with no traversal."""
    if not isinstance(name, str) or not name or '\x00' in name or '\\' in name:
        raise ValueError('Unsafe name: '+repr(name))
    pure = Path(name)
    if pure.is_absolute() or name.startswith('/') or any(part in ('', '.', '..') for part in name.split('/')):
        raise ValueError('Unsafe name: '+repr(name))
    return pure


def resolve_regular_file(root, name):
    """Resolve name inside root and require a regular, non-symlink file (lstat; every component)."""
    pure = safe_relative_name(name)
    base = Path(root)
    current = base
    for part in pure.parts:
        current = current/part
        mode = os.lstat(current).st_mode
        if stat.S_ISLNK(mode):
            raise ValueError('Symlink refused: '+name)
    if not stat.S_ISREG(os.lstat(current).st_mode):
        raise ValueError('Not a regular file: '+name)
    if not current.resolve().is_relative_to(base.resolve()):
        raise ValueError('Name escapes root: '+name)
    return current


def assert_plain_tree(root):
    """Walk with lstat: only regular files and directories may exist below root."""
    root = Path(root)
    if stat.S_ISLNK(os.lstat(root).st_mode):
        raise ValueError('Symlinked root refused')
    for directory, dirs, files in os.walk(root, followlinks=False):
        for entry in dirs+files:
            mode = os.lstat(Path(directory)/entry).st_mode
            if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                raise ValueError('Symlink or special file refused: '+str((Path(directory)/entry).relative_to(root)))
