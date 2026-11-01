"""Run the verifier as an external process on one trace and reduce what it printed to a verdict.

The verifier is a black box: a command template, a temporary directory holding the trace's files, a time limit. Its standard
output must be one ODES ``verification-report`` document. The harness validates it with the ODES validator and derives the
trace verdict with ``overall_verdict`` (``reject`` if any check is refuted, ``abstain`` if none is refuted and some could not be
checked or there is none, ``accept`` if every check is confirmed). A crash, a time-out, output that is not JSON and a report the
validator refuses are all ``error``: never a verdict and never detection. The exit status is not read as a verdict.

Template: ``cognous-verify --run-record {run_record} [--proposal {proposal_export}] [--ledger {destination_ledger}] [--witness {witness}]
[--holder-inventory {holder_inventory}]``. A bracketed
group is included only when every placeholder inside it has a file; an unbracketed placeholder must be ``{run_record}``.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from . import contract
from .trace import ABSENT_FILE, FILENAMES, ROLES

PLACEHOLDER = re.compile(r"\{(" + "|".join(ROLES) + r")\}")
VERDICTS = ("reject", "accept", "abstain", "error")


@dataclass(frozen=True)
class Outcome:
    verdict: str
    codes: frozenset[str] = frozenset()
    detail: str = ""
    verifier: Mapping[str, Any] | None = None
    tiers: frozenset[str] = frozenset()
    checks: int = 0


@dataclass(frozen=True)
class Template:
    required: tuple[str, ...]  # tokens always present
    groups: tuple[tuple[tuple[str, ...], frozenset[str]], ...]  # (tokens, roles needed)

    def expand(self, paths: Mapping[str, Path]) -> list[str]:
        out = [self._fill(t, paths) for t in self.required]
        for tokens, roles in self.groups:
            if roles <= set(paths):
                out.extend(self._fill(t, paths) for t in tokens)
        return out

    @staticmethod
    def _fill(token: str, paths: Mapping[str, Path]) -> str:
        return PLACEHOLDER.sub(lambda m: str(paths[m.group(1)]), token)


def parse_template(text: str) -> Template:
    tokens = shlex.split(text)
    required: list[str] = []
    groups: list[tuple[tuple[str, ...], frozenset[str]]] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.startswith("["):
            grp: list[str] = []
            first = True
            while True:
                if i >= len(tokens):
                    raise ValueError("unterminated [...] group in the verifier command")
                t = tokens[i][1:] if first else tokens[i]
                first = False
                if t.endswith("]"):
                    grp.append(t[:-1])
                    break
                grp.append(t)
                i += 1
            roles = frozenset(m.group(1) for t in grp for m in PLACEHOLDER.finditer(t))
            groups.append((tuple(t for t in grp if t), roles))
        else:
            required.append(tok)
        i += 1
    for tok in required:
        for m in PLACEHOLDER.finditer(tok):
            if m.group(1) != "run_record":
                raise ValueError(f"{{{m.group(1)}}} must be inside a [...] group: traces do not always carry it")
    if not any("{run_record}" in t for t in required):
        raise ValueError("the verifier command must contain {run_record}")
    return Template(tuple(required), tuple(groups))


def _clip(text: str, n: int = 240) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 3] + "..."


def reduce_report(stdout: bytes, validator: Any) -> Outcome:
    try:
        doc = json.loads(stdout.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, RecursionError):
        return Outcome("error", detail="standard output is not JSON")
    violations = validator.validate(doc)
    if violations:
        return Outcome("error", detail="report refused by the ODES validator: " + ", ".join(sorted({v.code for v in violations})))
    if doc.get("mutation_report") is not None:
        return Outcome("error", detail="a trace report must not carry a mutation report")
    codes = frozenset(f["code"] for c in doc["checks"] if c["verdict"] == "refuted" for f in c["findings"])
    return Outcome(validator.overall_verdict(doc), codes, verifier=doc["verifier"], tiers=frozenset(doc["scope"]["tiers_run"]), checks=len(doc["checks"]))


@dataclass
class Runner:
    command: str
    timeout: float = 60.0
    contract_dir: Path | None = None
    calls: int = 0
    _template: Template = field(init=False)

    def __post_init__(self) -> None:
        self._template = parse_template(self.command)

    def verify(self, files: Mapping[str, bytes]) -> Outcome:
        self.calls += 1
        if "run_record" not in files:
            return Outcome("error", detail="trace has no run record")
        validator = contract.load(self.contract_dir)
        with tempfile.TemporaryDirectory(prefix="vm-trace-") as tmp:
            paths = {}
            for role, data in files.items():
                path = Path(tmp) / FILENAMES[role]
                if data != ABSENT_FILE:  # family H8: the path is passed, no file exists there
                    path.write_bytes(data)
                paths[role] = path
            env = {k: v for k, v in os.environ.items() if k in ("PATH", "HOME", "LANG", "LC_ALL", "SYSTEMROOT", "VIRTUAL_ENV", "PYTHONPATH")}
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            try:
                done = subprocess.run(self._template.expand(paths), capture_output=True, timeout=self.timeout, cwd=tmp, env=env, check=False)
            except subprocess.TimeoutExpired:
                return Outcome("error", detail=f"timed out after {self.timeout:g}s")
            except OSError as exc:
                return Outcome("error", detail=f"could not start the verifier: {type(exc).__name__}")
        outcome = reduce_report(done.stdout, validator)
        if outcome.verdict == "error" and done.returncode != 0 and not done.stdout.strip():
            return Outcome("error", detail=_clip(f"exit {done.returncode}, no report: " + done.stderr.decode("utf-8", "replace")))
        return outcome
