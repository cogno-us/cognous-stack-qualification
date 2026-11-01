"""Regenerate ``verifier-code-names.json`` from a verifier source tree (the authoritative way to refresh it).

The vocabulary is every string literal under the verifier's ``src`` that is shaped like a code name: lowercase words joined by
underscores (``^[a-z][a-z0-9]*(_[a-z0-9]+)+$``), read from the Python syntax tree. It is a superset of the codes the verifier can emit.
The same rule reproduces the file pinned at 07c2eb8 exactly (246 names), so a refresh adds names and never silently changes the rule.
Reads source with git (``git show REV:path``), so it needs a verifier clone but runs nothing from it.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path
from typing import Any

PATTERN = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)+$")
REPOSITORY = "cogno-us/cognous-open-control-stack-verifier"
WHAT = ("every string literal in the verifier's Python source shaped like a code name (lowercase words joined by underscores): a superset of the codes it "
        "can emit, used only to check that no operator's intended code is a name the verifier never had")


def _git(checkout: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(checkout), *args], capture_output=True, text=True, check=True).stdout


def names_at(checkout: Path, revision: str) -> tuple[str, list[str]]:
    full = _git(checkout, "rev-parse", "--verify", f"{revision}^{{commit}}").strip()
    found: set[str] = set()
    for path in _git(checkout, "ls-tree", "-r", "--name-only", full, "src").split():
        if not path.endswith(".py"):
            continue
        tree = ast.parse(_git(checkout, "show", f"{full}:{path}"))
        found.update(n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and PATTERN.match(n.value))
    return full, sorted(found)


def vocabulary_doc(checkout: Path, revision: str) -> dict[str, Any]:
    full, names = names_at(checkout, revision)
    return {"kind": "verifier-code-names", "verifier_repository": REPOSITORY, "verifier_revision": full, "what": WHAT, "names": names}


def vocabulary_bytes(doc: dict[str, Any]) -> bytes:
    return (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
