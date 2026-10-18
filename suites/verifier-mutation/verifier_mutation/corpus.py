"""Mutant generation (generated corpus) and the seed corpus (ODES fixtures).

Generated corpus: every (trace, operator) pair and draw is one slot. A slot is ``effective`` (the operator changed the trace),
``noop`` (the mutant is identical to the clean trace: byte-identical, or for a structural operator, canonically equal) or ``na``
(the precondition was not met). Identical mutants of one trace and operator are dropped and counted, never counted twice. Noop
is decided on the files, not on a lenient re-parse, so a damaged text that Python reads as the clean document (a duplicate
member, ``NaN``) is effective.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from .jsonio import Pairs, Raw, canonical_bytes, commitment, digest, dump_file_bytes, wire_text_bytes
from .operators import OPERATORS, Ctx, NotApplicable, Operator, build_files, rng_for
from .trace import Trace

DEFAULT_SEED = 20261018
DEFAULT_DRAWS = 2
SEED_CONTRACTS = ("control-plane-journal", "execution-attempt-lifecycle")


@dataclass(frozen=True)
class Slot:
    mutant_id: str
    trace_id: str
    scenario: str
    operator_id: str
    category: str
    draw: int
    status: str  # effective | noop | na
    reason: str = ""
    files: Mapping[str, bytes] | None = None
    intended_codes: tuple[str, ...] = ()
    expected_verdict: str = "reject"
    expected_outcome: str = ""  # "" = the expected verdict; "input_error" = exit 2, no report (not part of the mutant-set digest)


def _has_text_damage(value: Any) -> bool:
    stack = [value]
    while stack:
        v = stack.pop()
        if isinstance(v, (Raw, Pairs)):
            return True
        if isinstance(v, dict):
            stack.extend(v.values())
        elif isinstance(v, list):
            stack.extend(v)
    return False


def _canonically_equal(a: bytes, b: bytes) -> bool:
    if a == b:  # catalogue v3: identical bytes are equal (a JSON-lines witness file is not one JSON document)
        return True
    try:
        return canonical_bytes(json.loads(a.decode("utf-8"))) == canonical_bytes(json.loads(b.decode("utf-8")))
    except (ValueError, UnicodeDecodeError, RecursionError):
        return False


def generate(traces: list[Trace], seed: int = DEFAULT_SEED, draws: int = DEFAULT_DRAWS,
             operators: Iterable[Operator] | None = None) -> tuple[list[Slot], int]:
    """Return (slots, duplicates_dropped). Deterministic for a given corpus, seed and draw count."""
    ops = sorted(operators if operators is not None else OPERATORS, key=lambda o: o.operator_id)
    slots: list[Slot] = []
    dropped = 0
    for trace in sorted(traces, key=lambda t: t.trace_id):
        peers = [t for t in sorted(traces, key=lambda t: t.trace_id) if t.trace_id != trace.trace_id]
        for operator in ops:
            seen: set[str] = set()
            for draw in range(draws):
                mutant_id = f"{trace.trace_id}:{operator.operator_id}:{draw}"
                base = dict(trace_id=trace.trace_id, scenario=trace.scenario, operator_id=operator.operator_id, category=operator.category,
                            draw=draw, mutant_id=mutant_id, intended_codes=operator.intended_codes, expected_verdict=operator.expected_verdict, expected_outcome=operator.expected_outcome)
                ctx = Ctx(trace=trace, rng=rng_for(seed, trace.trace_id, operator.operator_id, draw), peers=peers)
                try:
                    operator.fn(ctx)
                except (NotApplicable, KeyError, IndexError, TypeError, ValueError) as exc:
                    # NotApplicable, or a precondition the operator did not guard: the slot is not applicable, counted once per operator
                    reason = str(exc) if isinstance(exc, NotApplicable) else f"precondition not met ({type(exc).__name__})"
                    if "na:" + reason in seen:
                        dropped += 1
                    else:
                        seen.add("na:" + reason)
                        slots.append(Slot(status="na", reason=reason, **base))
                    continue
                files = build_files(trace, ctx)
                key = commitment({role: digest(data) for role, data in sorted(files.items())})
                if key in seen:
                    dropped += 1
                    continue
                seen.add(key)
                same_bytes = all(files[r] == trace.files[r] for r in trace.files) and set(files) == set(trace.files)
                structural_only = not ctx.raw and not any(_has_text_damage(ctx.docs[r]) for r in ctx.touched if r in ctx.docs)
                canon_same = structural_only and all(
                    _canonically_equal(files[r], trace.files[r]) for r in trace.files) and set(files) == set(trace.files)
                slots.append(Slot(status="noop" if same_bytes or canon_same else "effective", files=files, **base))
    return slots, dropped


def mutant_set_digest(slots: list[Slot]) -> str:
    entries = []
    for s in sorted(slots, key=lambda x: x.mutant_id):
        entry: dict[str, Any] = {"mutant_id": s.mutant_id, "status": s.status}
        if s.files is not None:
            entry["files"] = {r: digest(d) for r, d in sorted(s.files.items())}
        entries.append(entry)
    return commitment(entries)


def mutant_set_size(slots: list[Slot]) -> int:
    return sum(len(d) for s in slots if s.files for d in s.files.values())


def clean_corpus_digest(traces: list[Trace]) -> tuple[str, int]:
    entries = [{"trace_id": t.trace_id, "files": {r: digest(d) for r, d in sorted(t.files.items())}} for t in sorted(traces, key=lambda t: t.trace_id)]
    return commitment(entries), sum(len(d) for t in traces for d in t.files.values())


# ------------------------------------------------------------------------------------------------------------ seeds

@dataclass(frozen=True)
class Seed:
    seed_id: str
    contract: str
    category: str | None
    expected_code: str | None
    valid: bool
    files: Mapping[str, bytes]
    intended_codes: tuple[str, ...] = ()  # catalogue v3 witness seeds: the fixture's ODES code plus the verifier's names for the same rule

    def hit(self, codes: frozenset[str]) -> bool:
        return (self.expected_code in codes) or bool(set(self.intended_codes) & codes)


@dataclass
class SeedCorpus:
    odes_revision: str
    invalid: list[Seed] = field(default_factory=list)
    valid: list[Seed] = field(default_factory=list)

    def digests(self) -> tuple[tuple[str, int], tuple[str, int]]:
        def one(seeds: list[Seed]) -> tuple[str, int]:
            entries = []
            for s in sorted(seeds, key=lambda x: x.seed_id):
                e: dict[str, Any] = {"seed_id": s.seed_id, "category": s.category, "expected_refusal": s.expected_code, "sha256": digest(s.files["run_record"])}
                if set(s.files) != {"run_record"}:  # witness seeds also bind every file (unwitnessed seed digests are unchanged)
                    e["files"] = {r: digest(d) for r, d in sorted(s.files.items())}
                entries.append(e)
            return commitment(entries), sum(len(d) for s in seeds for d in s.files.values())
        return one(self.invalid), one(self.valid)

    def unclassified(self) -> list[Seed]:
        return [s for s in self.invalid if s.category is None]


def load_seed_map(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_seed_corpus(odes_dir: Path, seed_map: Mapping[str, Any], odes_revision: str) -> SeedCorpus:
    by_code = {code: cat for cat, codes in seed_map["by_code"].items() for code in codes}
    corpus = SeedCorpus(odes_revision)
    for contract in SEED_CONTRACTS:
        base = odes_dir / "contracts" / contract / "fixtures"
        for kind in ("invalid", "valid"):
            for path in sorted((base / kind).glob("*.json")):
                fx = json.loads(path.read_text(encoding="utf-8"))
                data = dump_file_bytes(fx["document"])
                code = fx.get("expected_refusal") if kind == "invalid" else None
                key = f"{contract}/{fx['fixture_id']}"
                category = seed_map["by_fixture"].get(key) or by_code.get(code) if kind == "invalid" else None
                intended = tuple(seed_map.get("intended_codes_by_fixture", {}).get(key, ())) if kind == "invalid" else ()
                seed = Seed(key, contract, category, code, kind == "valid", {"run_record": data}, intended)
                (corpus.valid if kind == "valid" else corpus.invalid).append(seed)
    return corpus


# ------------------------------------------------------------------------------------------ witness seeds (catalogue v3)

WITNESS_SEED_CONTRACTS = ("witness-digest", "holder-inventory")


def witness_lines(document: Any) -> bytes:
    """A witness-digest fixture document (a JSON array of records, oldest first) as the JSON-lines file the producer writes; a bare object is one line."""
    records = document if isinstance(document, list) else [document]
    return b"".join(wire_text_bytes(json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n") for r in records)


def load_witness_seed_corpus(odes_dir: Path, seed_map: Mapping[str, Any], odes_revision: str) -> SeedCorpus:
    """Seeds from the ODES ``witness-digest`` and ``holder-inventory`` fixtures (regression only, never detection).

    A witness fixture with a ``record`` is run with that record; one without is carried by the record of the fixture named in the map's
    ``carrier.witness-digest`` (the capture most invalid fixtures were mutated from): the file rules stop before the record rules, so the
    carrier matters only for a file the verifier lets through. A holder-inventory fixture is run with the record and witness of the fixture
    named in ``carrier.holder-inventory``. Intended codes are the fixture's ODES code plus the verifier's names for the category's rule
    (``seed-map`` ``intended_codes``; the shape codes differ by name, see the ODES drafts' Divergences)."""
    corpus = SeedCorpus(odes_revision)
    base = odes_dir / "contracts"

    def fixture(contract: str, kind: str, fid: str) -> dict[str, Any]:
        return json.loads((base / contract / "fixtures" / kind / f"{fid}.json").read_text(encoding="utf-8"))

    carrier_w = fixture("witness-digest", "valid", seed_map["carrier"]["witness-digest"])
    carrier_i = fixture("witness-digest", "valid", seed_map["carrier"]["holder-inventory"])
    for contract in WITNESS_SEED_CONTRACTS:
        for kind in ("invalid", "valid"):
            for path in sorted((base / contract / "fixtures" / kind).glob("*.json")):
                fx = json.loads(path.read_text(encoding="utf-8"))
                key = f"{contract}/{fx['fixture_id']}"
                if contract == "witness-digest":
                    files = {"run_record": dump_file_bytes(fx["record"] if "record" in fx else carrier_w["record"]), "witness": witness_lines(fx["document"])}
                else:
                    files = {"run_record": dump_file_bytes(carrier_i["record"]), "witness": witness_lines(carrier_i["document"]),
                             "holder_inventory": dump_file_bytes(fx["document"])}
                code = fx.get("expected_refusal") if kind == "invalid" else None
                category = seed_map["by_fixture"].get(key) if kind == "invalid" else None
                intended = tuple(seed_map["intended_codes"].get(category, ())) if category else ()
                seed = Seed(key, contract, category, code, kind == "valid", files, intended)
                (corpus.valid if kind == "valid" else corpus.invalid).append(seed)
    return corpus
