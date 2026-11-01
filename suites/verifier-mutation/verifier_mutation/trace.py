"""Traces (the files one run exported), the clean corpus loader and the harness's own downstream measures.

A trace has up to four files, named by role (the ODES verification-report input roles): ``run_record`` (the native bounded run
record), ``proposal_export`` (the full proposal model dump, nulls included), ``manifest`` and ``destination_ledger`` (the
destination file as the control plane's local destination wrote it). A witnessed trace (catalogue version 3, family H) also has
``witness`` (the ``witness-digest/0.1`` JSON-lines file ``acp witness publish`` wrote) and may have ``holder_inventory``; it can carry
extra files (an earlier snapshot of the record and the destination taken at an earlier publication) that no verifier is given.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .jsonio import digest, parse_lenient

ROLES = ("run_record", "proposal_export", "manifest", "destination_ledger", "witness", "holder_inventory")
FILENAMES = {
    "run_record": "bounded-run-record.json",
    "proposal_export": "proposal.json",
    "manifest": "manifest.json",
    "destination_ledger": "destination.json",
    "witness": "witness.jsonl",
    "holder_inventory": "holder-inventory.json",
}
#: extra files of a witnessed trace (operator material only, never given to the verifier)
EXTRA_FILENAMES = {
    "earlier_run_record": "earlier-bounded-run-record.json",
    "earlier_destination_ledger": "earlier-destination.json",
}
#: a role whose content is this marker is passed to the verifier as a path that does not exist (family H8, witness file absent)
ABSENT_FILE = b"\x00verifier-mutation:absent-file\x00"
MEASURES = ("unauthorized_effects", "excess_duplicate_effects", "authorized_count", "held_count")


@dataclass(frozen=True)
class Trace:
    trace_id: str
    scenario: str
    files: Mapping[str, bytes]
    description: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict)

    def doc(self, role: str) -> Any:
        return parse_lenient(self.files[role])


def load_clean_corpus(root: Path) -> tuple[dict[str, Any], list[Trace]]:
    """Read ``root/manifest.json`` and the trace directories it lists, checking every recorded SHA-256."""
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    traces: list[Trace] = []
    for entry in manifest["traces"]:
        directory = root / entry["trace_id"]
        files: dict[str, bytes] = {}
        for role, recorded in sorted(entry["files"].items()):
            data = (directory / FILENAMES[role]).read_bytes()
            if digest(data) != recorded:
                raise ValueError(f"{entry['trace_id']}/{FILENAMES[role]}: digest differs from the corpus manifest")
            files[role] = data
        extra: dict[str, bytes] = {}
        for name, recorded in sorted(entry.get("extra_files", {}).items()):
            data = (directory / EXTRA_FILENAMES[name]).read_bytes()
            if digest(data) != recorded:
                raise ValueError(f"{entry['trace_id']}/{EXTRA_FILENAMES[name]}: digest differs from the corpus manifest")
            extra[name] = data
        traces.append(Trace(entry["trace_id"], entry["scenario"], files, entry.get("description", ""), extra))
    ids = [t.trace_id for t in traces]
    if ids != sorted(ids) or len(set(ids)) != len(ids):
        raise ValueError("corpus manifest traces must be unique and sorted by trace_id")
    return manifest, traces


def measures(files: Mapping[str, bytes]) -> dict[str, int] | None:
    """The downstream figures the design's metric impact is conditioned on, derived by the harness from the files.

    This is the harness's own derivation (the verifier does not yet expose one): ``authorized_count`` and ``held_count`` count
    decisions by result; ``unauthorized_effects`` counts ledger rows whose effect has no authorized decision;
    ``excess_duplicate_effects`` counts ledger rows beyond one per effect plus effect counts beyond the rows. ``None`` when the
    files cannot be read by Python's own parser (the figure is then unavailable, never zero).
    """
    try:
        record = parse_lenient(files["run_record"])
        decisions = record["decisions"]
        authorized = {d["effect_id"] for d in decisions if d.get("result") == "authorized"}
        held = sum(1 for d in decisions if d.get("result") == "hold")
        unauthorized = excess = 0
        if "destination_ledger" in files:
            ledger = parse_lenient(files["destination_ledger"])
            rows = list(ledger.get("effects", {}).values())
            ids = [r.get("effect_id") for r in rows]
            unauthorized = sum(1 for i in ids if i not in authorized)
            excess = (len(ids) - len(set(ids))) + max(0, sum(ledger.get("grant_effect_counts", {}).values()) - len(rows))
        return {
            "unauthorized_effects": unauthorized,
            "excess_duplicate_effects": excess,
            "authorized_count": len(authorized),
            "held_count": held,
        }
    except (KeyError, TypeError, ValueError, AttributeError, RecursionError, UnicodeDecodeError):
        return None
