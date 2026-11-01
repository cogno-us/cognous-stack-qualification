"""Run the verifier over the corpora and emit the ODES ``verification-report`` mutation-report shape.

Denominators are never pooled: one table per corpus (seed regression, generated held-out), per category, and per scenario;
the clean-trace false-rejection tables are separate per clean corpus. Every figure is ``k`` of ``n``. Nothing here gates anything.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import datetime as dt
import json
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

from . import contract
from .corpus import Seed, SeedCorpus, Slot, clean_corpus_digest, mutant_set_digest, mutant_set_size
from .jsonio import PROFILE, commitment
from .operators import CATEGORIES_WITHOUT_OPERATOR, NOT_APPLICABLE_CATEGORIES, categories_with_operator
from .runner import Outcome, Runner
from .trace import MEASURES, Trace, measures

HARNESS_VERSION = "1"
NON_CLAIMS = {
    "relative_to_pinned_controller": "The result is relative to the controller revision, contract draft versions and reason registry named in subject.pinned; it does not carry to any other revision.",
    "semantic_quality_not_certified": "No claim that a decision was correct, that a policy was adequate or that a grant was lawfully issued.",
    "receipt_source_bounded": "Destination ledger rows are executor-written, unsequenced and unsigned: no claim that the ledger is complete or unforged, or that an effect occurred in the world.",
    "self_consistent_forgery_not_detected": "A record rewritten with every affected commitment recomputed is accepted (category F); no external anchor exists.",
    "not_an_attestation": "This is a verification report. It is not an attestation, not an Index or BitRep signature and not an authorization; it grants and denies nothing and is never an input to a grant or decision.",
    "parse_strictness_is_refusal_not_repair": "An input refused at the wire level is reported as refused; neither the verifier nor this harness normalizes it and runs it again.",
    "no_v1_scope_claim": "Nothing here changes the V1 scope, the failure register, a profile, a pin or any qualified row; this report is report-only and gates nothing.",
    "differential_agreement_is_not_equivalence": "Agreement between verifier and controller on a corpus is not equivalence outside that corpus.",
    "no_imported_headline_numbers": "No figure from any paper is a target, baseline or expectation; the only numbers are counts from the corpora named here, each over its own denominator.",
    "seeds_are_regression_not_detection": "Seed corpora are regression checks (the ODES fixtures were written for rules the validators already implement); detection figures come only from the generated corpus.",
}
WITNESS_NON_CLAIM = ("witness_is_not_publication",
                     "A witness that matches the records shows only that match: not that it was published, published in time, held by a party independent of the "
                     "record keeper, or who published it (the witness record has no signer or proof member). Rows appended after the latest witness digest are "
                     "not covered, only list-valued run-record ledgers are covered (the destination ledger snapshot is not), and a record and witness rewritten "
                     "together to agree are accepted (category F). Witnessed populations are measured apart from unwitnessed ones and never pooled.")
CATEGORY_ORDER = ["W1", "W2", "W3", "W4", "W5", "B", "S1", "S2", "S3", "S4", "I1", "I2", "I3", "I4", "I5", "D1", "D2", "D3", "D4", "D5",
                  "J1", "J2", "J3", "T1", "A1", "A2", "R1", "R2", "R3", "R4", "R5", "R6", "X1", "L1", "F", "H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "Q"]
WITNESS_CATEGORIES = ("H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8")
WITNESS_REJECT = ("H1", "H2", "H3", "H4", "H5", "H6")


@dataclass
class Result:
    slot: Slot
    outcome: Outcome | None = None
    delta: dict[str, int] | None = None  # measures(mutant) - measures(clean); None when unavailable


@dataclass
class Run:
    """Everything observed: the raw material of the report."""
    clean: dict[str, Outcome] = field(default_factory=dict)
    results: list[Result] = field(default_factory=list)
    seed_invalid: list[tuple[Seed, Outcome]] = field(default_factory=list)
    seed_valid: list[tuple[Seed, Outcome]] = field(default_factory=list)


def _map(fn: Callable[[Any], Any], items: Sequence[Any], jobs: int) -> list[Any]:
    if jobs <= 1:
        return [fn(i) for i in items]
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        return list(pool.map(fn, items))


def execute(runner: Runner, traces: list[Trace], slots: list[Slot], seeds: SeedCorpus | None, jobs: int = 1) -> Run:
    run = Run()
    run.clean = dict(zip((t.trace_id for t in traces), _map(lambda t: runner.verify(t.files), traces, jobs)))
    effective = [s for s in slots if s.status == "effective"]
    outcomes = _map(lambda s: runner.verify(s.files or {}), effective, jobs)
    mine = {s.mutant_id: o for s, o in zip(effective, outcomes)}
    clean_measures = {t.trace_id: measures(t.files) for t in traces}
    for s in slots:
        r = Result(s, mine.get(s.mutant_id))
        if r.outcome is not None and r.outcome.verdict == "accept":
            before, after = clean_measures[s.trace_id], measures(s.files or {})
            r.delta = {m: after[m] - before[m] for m in MEASURES} if before and after else None
        run.results.append(r)
    if seeds is not None:
        for attr, source in (("seed_invalid", seeds.invalid), ("seed_valid", seeds.valid)):
            setattr(run, attr, list(zip(source, _map(lambda s: runner.verify(s.files), source, jobs))))
    return run


# ---------------------------------------------------------------------------------------------------------------- rows

def _frac(k: int | None, n: int) -> dict[str, Any]:
    return {"k": k, "n": n}


def _tally(outcomes: Sequence[Outcome]) -> dict[str, int]:
    c = Counter(o.verdict for o in outcomes)
    return {"reject": c["reject"], "accept": c["accept"], "abstain": c["abstain"], "error": c["error"]}


INPUT_ERROR_DETAIL = "exit 2, no report"  # the runner's detail for a run that exited 2 without a report


def _input_error_met(r: "Result") -> bool:
    """An input-error control (expected_outcome input_error) whose run exited 2 with no report: the expected outcome, not a runtime error."""
    return (r.slot.expected_outcome == "input_error" and r.outcome is not None and r.outcome.verdict == "error"
            and r.outcome.detail.startswith(INPUT_ERROR_DETAIL))


def _known_limit(r: "Result") -> bool:
    """A known-limit control: its category expects reject but the operator is outside what the verified profile covers (catalogue 3.2), so the expected outcome is accept."""
    return r.slot.expected_outcome == "accept" and r.slot.expected_verdict == "reject"


def _intended_hit(outcome: Outcome, intended: Sequence[str]) -> bool:
    return outcome.verdict == "reject" and bool(outcome.codes & set(intended))


def _impact(accepted: list[Result]) -> dict[str, Any]:
    n = len(accepted)
    if n == 0:
        return {"conditioned_on": "false_acceptance", "changed": _frac(None, 0), "deltas": []}
    avail = [r.delta for r in accepted if r.delta is not None]
    changed = sum(1 for d in avail if any(d.values()))
    deltas = []
    for m in MEASURES:
        vals = [d[m] for d in avail]
        nonzero = sum(1 for v in vals if v)
        if nonzero:
            deltas.append({"measure": m, "nonzero_mutants": nonzero, "min": min(vals), "max": max(vals)})
    out: dict[str, Any] = {"conditioned_on": "false_acceptance", "changed": _frac(changed, n), "deltas": deltas}
    if len(avail) != n:
        out["extensions"] = {"x-measures-unavailable": {"k": n - len(avail), "n": n, "reason": "the accepted mutant cannot be read by Python's own parser, so no figure can be derived"}}
    return out


def _generated_row(category: str, expected: str, results: list[Result]) -> dict[str, Any]:
    n_noop = sum(1 for r in results if r.slot.status == "noop")
    n_na = sum(1 for r in results if r.slot.status == "na")
    eff = [r for r in results if r.slot.status == "effective"]
    n_eff = len(eff)
    v = _tally([r.outcome for r in eff])  # type: ignore[misc]
    intended = sum(1 for r in eff if _intended_hit(r.outcome, r.slot.intended_codes))  # type: ignore[arg-type]
    return {
        "category": category, "expected_verdict": expected, "n_gen": len(results), "n_noop": n_noop, "n_na": n_na, "n_eff": n_eff, "verdicts": v,
        "detection": {"any_code": _frac(v["reject"], n_eff), "intended_code": _frac(intended, n_eff)}, "regression": None,
        "false_acceptance": _frac(v["accept"], n_eff), "abstained": _frac(v["abstain"], n_eff), "errored": _frac(v["error"], n_eff),
        "metric_impact": _impact([r for r in eff if r.outcome.verdict == "accept"]),  # type: ignore[union-attr]
    }


def _seed_row(category: str, pairs: list[tuple[Seed, Outcome]]) -> dict[str, Any]:
    n = len(pairs)
    v = _tally([o for _, o in pairs])
    hit = sum(1 for s, o in pairs if o.verdict == "reject" and s.hit(o.codes))
    return {
        "category": category, "expected_verdict": "reject", "n_gen": n, "n_noop": 0, "n_na": 0, "n_eff": n, "verdicts": v, "detection": None,
        "regression": {"refused_with_intended_code": _frac(hit, n)}, "false_acceptance": None, "abstained": None, "errored": None, "metric_impact": None,
    }


def _q_row() -> dict[str, Any]:
    return {"category": "Q", "expected_verdict": "not_applicable", "n_gen": 0, "n_noop": 0, "n_na": 0, "n_eff": 0,
            "verdicts": {"reject": 0, "accept": 0, "abstain": 0, "error": 0}, "detection": None, "regression": None, "false_acceptance": None,
            "abstained": None, "errored": None, "metric_impact": None}


def _ordered(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda r: CATEGORY_ORDER.index(r["category"]))


def _expected(category: str) -> str:
    from .operators import EXPECTED_ABSTAIN, EXPECTED_ACCEPT
    return "accept" if category in EXPECTED_ACCEPT else "abstain" if category in EXPECTED_ABSTAIN else "reject"


def generated_rows(results: list[Result], categories: Sequence[str] | None = None, include_q: bool = True) -> list[dict[str, Any]]:
    """One row per category with an operator; the witnessed population passes its own categories and no Q row (H, B and F only)."""
    by_cat: dict[str, list[Result]] = defaultdict(list)
    for r in results:
        by_cat[r.slot.category].append(r)
    rows = [_generated_row(c, _expected(c), by_cat[c]) for c in (categories if categories is not None else categories_with_operator()) if c in by_cat]
    return _ordered(rows + ([_q_row()] if include_q else []))


def clean_generated_rows(run: Run, categories: Sequence[str] | None = None) -> list[dict[str, Any]]:
    """Per category: of the clean traces on which the category's operators produced an effective mutant (the checks are active), those the verifier rejected.

    Benign (B) is the exception the design names: a rejected benign mutant is a false rejection, so its row counts benign mutants.
    """
    by_cat: dict[str, set[str]] = defaultdict(set)
    benign: list[Outcome] = []
    for r in run.results:
        if r.slot.status != "effective":
            continue
        if r.slot.category == "B":
            benign.append(r.outcome)  # type: ignore[arg-type]
        else:
            by_cat[r.slot.category].add(r.slot.trace_id)
    rows = []
    for c in (categories if categories is not None else categories_with_operator()):
        if c == "B":
            k = sum(1 for o in benign if o.verdict == "reject")
            rows.append({"category": c, "false_rejection": _frac(k, len(benign)),
                         "extensions": {"x-verdicts": _tally(benign), "x-counts": "benign mutants"}})
        else:
            active = sorted(by_cat[c])
            outs = [run.clean[t] for t in active]
            rows.append({"category": c, "false_rejection": _frac(sum(1 for o in outs if o.verdict == "reject"), len(outs)),
                         "extensions": {"x-verdicts": _tally(outs), "x-counts": "clean traces"}})
    return _ordered(rows)


def clean_seed_rows(seeds: SeedCorpus, run: Run) -> list[dict[str, Any]]:
    """Per category that has seeds: the valid fixtures of the contracts those seeds come from, those the verifier rejected."""
    contracts: dict[str, set[str]] = defaultdict(set)
    for s in seeds.invalid:
        if s.category:
            contracts[s.category].add(s.contract)
    rows = []
    for c in sorted(contracts, key=CATEGORY_ORDER.index):
        outs = [o for s, o in run.seed_valid if s.contract in contracts[c]]
        if not outs:
            continue
        rows.append({"category": c, "false_rejection": _frac(sum(1 for o in outs if o.verdict == "reject"), len(outs)),
                     "extensions": {"x-verdicts": _tally(outs), "x-contracts": sorted(contracts[c])}})
    return rows


# --------------------------------------------------------------------------------------------------------------- flags

def flags(run: Run, seeds: SeedCorpus | None) -> list[dict[str, Any]]:
    """Advisories that the verifier (or this harness's wiring of it) is not measuring anything. Report-only: they gate nothing."""
    out: list[dict[str, Any]] = []
    eff = [r for r in run.results if r.slot.status == "effective"]
    reject_cats = [r for r in eff if r.slot.expected_verdict == "reject"]
    if reject_cats and not any(r.outcome.verdict == "reject" for r in reject_cats):  # type: ignore[union-attr]
        out.append({"id": "no_detection_anywhere", "k": 0, "n": len(reject_cats),
                    "detail": "the verifier rejected none of the effective mutants whose expected verdict is reject"})
    if eff and all(r.outcome.verdict == "accept" for r in eff):  # type: ignore[union-attr]
        out.append({"id": "accepts_every_mutant", "k": len(eff), "n": len(eff), "detail": "every effective mutant was accepted"})
    if eff and all(r.outcome.verdict == "abstain" for r in eff):  # type: ignore[union-attr]
        out.append({"id": "abstains_on_every_mutant", "k": len(eff), "n": len(eff), "detail": "every effective mutant was abstained on"})
    clean = list(run.clean.values())
    if clean and all(o.verdict == "reject" for o in clean):
        out.append({"id": "rejects_every_clean_trace", "k": len(clean), "n": len(clean), "detail": "the verifier rejected every clean trace: its detection figures say nothing"})
    errors = sum(1 for o in clean if o.verdict == "error") + sum(1 for r in eff if r.outcome.verdict == "error" and not _input_error_met(r))  # type: ignore[union-attr]
    if errors:
        out.append({"id": "errors_present", "k": errors, "n": len(clean) + len(eff), "detail": "runs with no usable report (crash, time-out, invalid report); never counted as detection"})
    if seeds is not None and seeds.valid and all(o.verdict == "reject" for _, o in run.seed_valid):
        out.append({"id": "rejects_every_valid_seed", "k": len(run.seed_valid), "n": len(run.seed_valid), "detail": "the verifier rejected every valid ODES fixture"})
    return out


def input_error_controls(run: Run) -> list[dict[str, Any]]:
    """Per input-error control operator (ODES decision 30-A): effective slots, those that exited 2 with no report as expected, and the rest
    (any other outcome is a finding). Counted aside: these runs are in the category row's ``error`` count (the report contract has no row-level
    input_error), never in detection."""
    by: dict[str, list[Result]] = defaultdict(list)
    for r in run.results:
        if r.slot.expected_outcome == "input_error" and r.slot.status == "effective":
            by[r.slot.operator_id].append(r)
    return [{"operator_id": oid, "expected_outcome": "input_error", "n_eff": len(rs), "exit_2_no_report": sum(1 for r in rs if _input_error_met(r)),
             "other": sorted(f"{r.slot.mutant_id} -> {r.outcome.verdict}" for r in rs if not _input_error_met(r))}  # type: ignore[union-attr]
            for oid, rs in sorted(by.items())]


KNOWN_LIMIT_REASON = ("the witness profile (witness-digest/0.1) covers the run record's list-valued members, not destination.json, so a destination row "
                      "that nothing in the record corroborates is as undetectable with a witness as without (R6; ODES decision 30-A, ODES #89)")


def known_limit_controls(run: Run) -> list[dict[str, Any]]:
    """Per known-limit control operator (catalogue 3.2): effective slots, those accepted as expected, and the rest (any other outcome is a finding,
    for example a verifier that now rejects). Counted aside: the category row's own counts are unchanged (the report contract has no
    operator-level expectation), so an accepted known-limit mutant still shows in the row's ``accept`` count, labelled here, never as a missed detection."""
    by: dict[str, list[Result]] = defaultdict(list)
    for r in run.results:
        if _known_limit(r) and r.slot.status == "effective":
            by[r.slot.operator_id].append(r)
    return [{"operator_id": oid, "category": rs[0].slot.category, "expected_outcome": "accept", "label": "known limit, post-hoc", "reason": KNOWN_LIMIT_REASON,
             "n_eff": len(rs), "accepted_as_expected": sum(1 for r in rs if r.outcome.verdict == "accept"),  # type: ignore[union-attr]
             "other": sorted(f"{r.slot.mutant_id} -> {r.outcome.verdict}" for r in rs if r.outcome.verdict != "accept")}  # type: ignore[union-attr]
            for oid, rs in sorted(by.items())]


def witnessed_flags(run: Run) -> list[dict[str, Any]]:
    """The same advisories for the witnessed population, measured on its own (ids prefixed ``witnessed_``). Report-only."""
    out: list[dict[str, Any]] = []
    eff = [r for r in run.results if r.slot.status == "effective"]
    h_reject = [r for r in eff if r.slot.category in WITNESS_REJECT]
    if h_reject and not any(r.outcome.verdict == "reject" for r in h_reject):  # type: ignore[union-attr]
        out.append({"id": "witnessed_no_family_h_detection", "k": 0, "n": len(h_reject),
                    "detail": "the verifier rejected none of the effective H1 to H6 mutants (is it given the witness and inventory?)"})
    if eff and all(r.outcome.verdict == "accept" for r in eff):  # type: ignore[union-attr]
        out.append({"id": "witnessed_accepts_every_mutant", "k": len(eff), "n": len(eff), "detail": "every effective witnessed mutant was accepted"})
    controls = [r for r in eff if r.slot.category in ("H7", "H8") and r.slot.expected_outcome != "input_error"]
    if controls and not any(r.outcome.verdict == "abstain" for r in controls):  # type: ignore[union-attr]
        out.append({"id": "witnessed_controls_never_abstain", "k": 0, "n": len(controls),
                    "detail": "no H7 or H8 control was abstained on: the verifier confirms or rejects what it cannot check"})
    clean = list(run.clean.values())
    if clean and all(o.verdict == "reject" for o in clean):
        out.append({"id": "witnessed_rejects_every_clean_trace", "k": len(clean), "n": len(clean),
                    "detail": "the verifier rejected every witnessed clean trace: its family H figures say nothing"})
    errors = sum(1 for o in clean if o.verdict == "error") + sum(1 for r in eff if r.outcome.verdict == "error" and not _input_error_met(r))  # type: ignore[union-attr]
    if errors:
        out.append({"id": "witnessed_errors_present", "k": errors, "n": len(clean) + len(eff),
                    "detail": "witnessed runs with no usable report (crash, time-out, input error, invalid report); never counted as detection. Input-error controls that exited 2 with no report as expected are not counted here (see input_error_controls)"})
    return out


@dataclass
class Witnessed:
    """The witnessed population (catalogue version 3, family H): its own clean corpus, generated mutants and seeds, never pooled."""
    run: Run
    traces: list[Trace]
    slots: list[Slot]
    duplicates_dropped: int
    manifest: Mapping[str, Any]
    seeds: SeedCorpus | None = None
    seed_controls: list[tuple[Seed, Outcome]] = field(default_factory=list)


def _files_digest(traces: list[Trace], role: str) -> tuple[str, int] | None:
    entries = [{"trace_id": t.trace_id, "sha256": digest_of(t.files[role])} for t in sorted(traces, key=lambda t: t.trace_id) if role in t.files]
    if not entries:
        return None
    return commitment(entries), sum(len(t.files[role]) for t in traces if role in t.files)


def digest_of(data: bytes) -> str:
    from .jsonio import digest
    return digest(data)


# ------------------------------------------------------------------------------------------------------------ document

def build(run: Run, *, traces: list[Trace], slots: list[Slot], duplicates_dropped: int, seeds: SeedCorpus | None, clean_manifest: Mapping[str, Any],
          operator_set_bytes: bytes, operator_set_digest: str, seed: int, draws: int, frozen_revision: str, generated_at: str | None, command: str,
          verifier_hint: Mapping[str, str] | None = None, per_scenario: bool = True, family_s: list[dict[str, Any]] | None = None,
          witnessed: Witnessed | None = None) -> dict[str, Any]:
    clean_digest, clean_size = clean_corpus_digest(traces)
    gen_digest, gen_size = mutant_set_digest(slots), mutant_set_size(slots)
    inputs: list[dict[str, Any]] = [
        {"role": "operator_set", "name": "operators.json", "digest": operator_set_digest, "size_bytes": len(operator_set_bytes)},
        {"role": "corpus", "name": "clean-generated", "digest": clean_digest, "size_bytes": clean_size},
        {"role": "corpus", "name": "generated-mutants", "digest": gen_digest, "size_bytes": gen_size},
    ]
    family_t: list[dict[str, Any]] = []
    clean_tables: list[dict[str, Any]] = [{"corpus_id": "clean-generated", "provenance": "generated", "corpus_digest": clean_digest, "rows": clean_generated_rows(run)}]
    scenarios = None
    if per_scenario:
        by_scn: dict[str, list[Result]] = defaultdict(list)
        for r in run.results:
            by_scn[r.slot.scenario].append(r)
        scenarios = [{"scenario_id": sid, "categories": generated_rows(by_scn[sid])} for sid in sorted(by_scn)]
    if seeds is not None:
        (inv_digest, inv_size), (val_digest, val_size) = seeds.digests()
        inputs += [{"role": "corpus", "name": "odes-seed-invalid", "digest": inv_digest, "size_bytes": inv_size},
                   {"role": "corpus", "name": "odes-seed-valid", "digest": val_digest, "size_bytes": val_size}]
        by_cat: dict[str, list[tuple[Seed, Outcome]]] = defaultdict(list)
        for s, o in run.seed_invalid:
            if s.category:
                by_cat[s.category].append((s, o))
        family_t.append({"corpus_id": "t-seed-odes", "provenance": "seed", "corpus_digest": inv_digest,
                         "categories": _ordered([_seed_row(c, by_cat[c]) for c in by_cat]), "scenarios": None})
        clean_tables.append({"corpus_id": "clean-odes-valid", "provenance": "seed_valid_fixtures", "corpus_digest": val_digest, "rows": clean_seed_rows(seeds, run)})
    family_t.append({"corpus_id": "t-generated", "provenance": "generated", "corpus_digest": gen_digest, "categories": generated_rows(run.results), "scenarios": scenarios})
    witnessed_ext: dict[str, Any] | str = "not run"
    if witnessed is not None:
        from .witness_operators import witness_categories
        wcats = witness_categories()
        w = witnessed
        wclean_digest, wclean_size = clean_corpus_digest(w.traces)
        wgen_digest, wgen_size = mutant_set_digest(w.slots), mutant_set_size(w.slots)
        inputs += [{"role": "corpus", "name": "clean-generated-witnessed", "digest": wclean_digest, "size_bytes": wclean_size},
                   {"role": "corpus", "name": "generated-witnessed-mutants", "digest": wgen_digest, "size_bytes": wgen_size}]
        # tier V3 ran on these files: the contract ties V3 to a witness or holder-inventory input (v3_input_missing), so the witnessed clean
        # corpus's witness files and inventories are listed under their own roles (the mutants' files are in generated-witnessed-mutants)
        for role, name in (("witness", "clean-generated-witnessed-witness-files"), ("holder_inventory", "clean-generated-witnessed-holder-inventories")):
            fd = _files_digest(w.traces, role)
            if fd:
                inputs.append({"role": role, "name": name, "digest": fd[0], "size_bytes": fd[1]})
        wscen = None
        if per_scenario:
            by_wscn: dict[str, list[Result]] = defaultdict(list)
            for r in w.run.results:
                by_wscn[r.slot.scenario].append(r)
            wscen = [{"scenario_id": sid, "categories": generated_rows(by_wscn[sid], wcats, include_q=False)} for sid in sorted(by_wscn)]
        if w.seeds is not None:
            (winv_digest, winv_size), (wval_digest, wval_size) = w.seeds.digests()
            inputs += [{"role": "corpus", "name": "odes-witness-seed-invalid", "digest": winv_digest, "size_bytes": winv_size},
                       {"role": "corpus", "name": "odes-witness-seed-valid", "digest": wval_digest, "size_bytes": wval_size}]
            wby: dict[str, list[tuple[Seed, Outcome]]] = defaultdict(list)
            for s, o in w.run.seed_invalid:
                if s.category:
                    wby[s.category].append((s, o))
            family_t.append({"corpus_id": "t-seed-odes-witness", "provenance": "seed", "corpus_digest": winv_digest,
                             "categories": _ordered([_seed_row(c, wby[c]) for c in wby]), "scenarios": None})
        family_t.append({"corpus_id": "t-generated-witnessed", "provenance": "generated", "corpus_digest": wgen_digest,
                         "categories": generated_rows(w.run.results, wcats, include_q=False), "scenarios": wscen})
        clean_tables.append({"corpus_id": "clean-generated-witnessed", "provenance": "generated", "corpus_digest": wclean_digest,
                             "rows": clean_generated_rows(w.run, wcats)})
        if w.seeds is not None:
            clean_tables.append({"corpus_id": "clean-odes-witness-valid", "provenance": "seed_valid_fixtures", "corpus_digest": wval_digest,
                                 "rows": clean_seed_rows(w.seeds, w.run)})
        wnoop = sum(1 for s in w.slots if s.status == "noop")
        witnessed_ext = {
            "population": "witnessed (family H, with the B and F controls measured on the same witnessed traces); never pooled with the unwitnessed corpora",
            "duplicate_slots_dropped": w.duplicates_dropped,
            "slots": {"effective": sum(1 for s in w.slots if s.status == "effective"), "noop": wnoop, "na": sum(1 for s in w.slots if s.status == "na")},
            "clean_traces": {"n": len(w.traces), "verdicts": _tally(list(w.run.clean.values()))},
            "control_plane_revision": w.manifest.get("control_plane_revision"),
            "witness_producer": w.manifest.get("witness_producer"),
            "seed_corpus": ({"odes_revision": w.seeds.odes_revision, "invalid": len(w.seeds.invalid), "valid": len(w.seeds.valid),
                             "unclassified": len(w.seeds.unclassified()), "unclassified_fixtures": sorted(s.seed_id for s in w.seeds.unclassified())}
                            if w.seeds else "not run"),
            "seed_controls": [{"seed_id": s.seed_id, "expected_verdict": "abstain", "observed_verdict": o.verdict, "codes": sorted(o.codes)} for s, o in w.seed_controls],
            "flags": witnessed_flags(w.run),
            "input_error_controls": input_error_controls(w.run),
            "known_limit_controls": known_limit_controls(w.run),
        }
    inputs.sort(key=lambda i: (i["role"], i["name"], i["digest"]))

    verifier = next((o.verifier for o in [*run.clean.values(), *(r.outcome for r in run.results if r.outcome)] if o and o.verifier), None)
    hint = dict(verifier_hint or {})
    verifier_block = dict(verifier) if verifier else {"name": hint.get("name", "unknown"), "version": hint.get("version", "unknown"), "command": "cognous-verify",
                                                    "source_revision": hint.get("source_revision", "unknown"), "canonicalization_profile": PROFILE}
    every = [*run.clean.values(), *(r.outcome for r in run.results if r.outcome)]
    if witnessed is not None:
        every += [*witnessed.run.clean.values(), *(r.outcome for r in witnessed.run.results if r.outcome)]
    tiers = sorted({t for o in every if o for t in o.tiers})
    if "V3" not in tiers and any(i["role"] in ("witness", "holder_inventory") for i in inputs):
        inputs = [i for i in inputs if i["role"] not in ("witness", "holder_inventory")]  # V3 never ran: no V3 input either
    noop_n = sum(1 for s in slots if s.status == "noop")
    harness = {
        "harness_version": HARNESS_VERSION, "verifier_command": command, "draws_per_variant": draws, "duplicate_slots_dropped": duplicates_dropped,
        "slots": {"effective": sum(1 for s in slots if s.status == "effective"), "noop": noop_n, "na": sum(1 for s in slots if s.status == "na")},
        "categories_without_operator": [c for c in CATEGORIES_WITHOUT_OPERATOR if c not in NOT_APPLICABLE_CATEGORIES],
        "clean_traces": {"n": len(traces), "verdicts": _tally(list(run.clean.values()))},
        "control_plane_revision": clean_manifest.get("control_plane_revision"),
        "seed_corpus": ({"odes_revision": seeds.odes_revision, "invalid": len(seeds.invalid), "valid": len(seeds.valid), "unclassified": len(seeds.unclassified()),
                         "unclassified_codes": sorted({s.expected_code for s in seeds.unclassified() if s.expected_code})} if seeds else "not run"),
        "definitions": {
            "noop": "the mutant's files are byte-identical to the clean trace's (a structural operator is also noop when its files are canonically equal); the design's wording 'byte-equal after canonicalization' is not used for text operators because a duplicate member or NaN reads as the clean document under Python's parser",
            "clean_false_rejection": "per category, clean traces on which that category's operators produced an effective mutant, rejected by the verifier; benign (B) counts benign mutants",
            "metric_impact": "measures are derived by this harness from the mutant's files (the verifier does not expose them); unavailable for a mutant Python's parser cannot read",
            "intended_code": "the operator's frozen intended codes; a different but correct verifier code counts in any_code only. Catalogue version 2: intended codes frozen post-hoc after run 1 (703cdde1), so intended_code figures are not held-out; any_code detection is the primary figure. Catalogue version 3 (family H): operators written after the verifier's tier V3 existed, intended codes frozen post-hoc from its emitted codes; any_code detection is the primary figure",
            "known_limit": "H4.destination-row-dropped-uncorroborated is a known-limit control (catalogue 3.2): expected accept, labelled post-hoc, because the witness profile does not cover destination.json (ODES decision 30-A, ODES #89). It stays in the H4 row's accept count (the contract has no operator-level expectation) and is listed apart under witnessed.known_limit_controls; it is not a missed detection and is not in per-operator not_rejected.",
            "expected_abstain": "H7 and H8 are controls with expected verdict abstain (the verifier says could_not_check); an accept there is a false acceptance (counted in false_acceptance), a reject a false rejection (it shows as reject in verdicts and detection.any_code, which for these rows is not detection). Exception (catalogue 3.1, ODES decision 30-A): H8.witness-file-absent is an input-error control, expected exit 2 and no report; those runs sit in the row's error count (the contract has no row-level input_error) and are listed apart under witnessed.input_error_controls",
        },
        "intended_codes_status": json.loads(operator_set_bytes).get("intended_codes", {}).get("status", "frozen with the operator set before the run"),
        "operator_version": json.loads(operator_set_bytes).get("operator_version"),
        "flags": flags(run, seeds),
        "witnessed": witnessed_ext,
    }
    mutation_report = {
        "report_only": True, "operator_set_digest": operator_set_digest, "seed": seed, "frozen_revision": frozen_revision,
        "family_t": family_t, "family_s": family_s or [], "clean": clean_tables, "extensions": {"x-qualification-harness": harness},
    }
    body = {"operator_set": operator_set_digest, "seed": seed, "corpora": [i["digest"] for i in inputs]}
    return {
        "contract": "verification-report", "contract_version": "0.1.0-draft", "profile": "verification-report/0.1", "report_kind": "verification_report",
        "report_id": "mutation-" + commitment(body)[7:19],
        "generated_at": generated_at or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "verifier": verifier_block,
        "subject": {"canonicalization_profile": PROFILE, "inputs": inputs, "inputs_digest": commitment(inputs),
                    "pinned": {"controller_revision": str(clean_manifest["control_plane_revision"]),
                               "contract_versions": {**dict(clean_manifest["contract_versions"]), **(dict(witnessed.manifest["contract_versions"]) if witnessed is not None else {})},
                               "reason_registry_digest": clean_manifest["reason_registry_digest"]}},
        "scope": {"semantic_quality": "not_assessed", "tiers_run": tiers},
        "checks": [], "summary": {"checks": 0, "confirmed": 0, "could_not_check": 0, "refuted": 0},
        "does_not_prove": [{"id": k, "statement": v} for k, v in NON_CLAIMS.items()] + ([{"id": WITNESS_NON_CLAIM[0], "statement": WITNESS_NON_CLAIM[1]}] if witnessed is not None else []),
        "mutation_report": mutation_report,
    }


def per_operator(run: Run, population: str) -> list[dict[str, Any]]:
    """Per operator: slot statuses, verdicts over the effective slots, and the refusal codes seen (a breakdown of the category rows for
    reading misses; its counts sum to the category rows of the report and add no figure of their own)."""
    by: dict[str, list[Result]] = defaultdict(list)
    for r in run.results:
        by[r.slot.operator_id].append(r)
    out = []
    for oid in sorted(by):
        rs = by[oid]
        eff = [r for r in rs if r.slot.status == "effective"]
        codes: Counter[str] = Counter(c for r in eff if r.outcome and r.outcome.verdict == "reject" for c in r.outcome.codes)
        out.append({
            "population": population, "operator_id": oid, "category": rs[0].slot.category, "expected_verdict": rs[0].slot.expected_verdict,
            "expected_outcome": rs[0].slot.expected_outcome or rs[0].slot.expected_verdict,
            "slots": dict(Counter(r.slot.status for r in rs)), "verdicts": _tally([r.outcome for r in eff]),  # type: ignore[misc]
            "intended_code_hits": sum(1 for r in eff if _intended_hit(r.outcome, r.slot.intended_codes)),  # type: ignore[arg-type]
            "codes": dict(sorted(codes.items())),
            "not_rejected": sorted(f"{r.slot.mutant_id} -> {r.outcome.verdict}" + (f" ({r.outcome.detail})" if r.outcome.detail else "")  # type: ignore[union-attr]
                                   for r in eff if r.slot.expected_verdict == "reject" and r.outcome.verdict != "reject" and not _known_limit(r)),  # type: ignore[union-attr]
            "unexpected": sorted(f"{r.slot.mutant_id} -> {r.outcome.verdict} {sorted(r.outcome.codes)}"  # type: ignore[union-attr]
                                 for r in eff if ((r.slot.expected_verdict != "reject" and r.outcome.verdict != r.slot.expected_verdict)
                                                  or (_known_limit(r) and r.outcome.verdict != "accept"))
                                 and not _input_error_met(r)),  # type: ignore[union-attr]
        })
    return out


def validate(doc: dict[str, Any], contract_dir: Any = None) -> list[Any]:
    return contract.load(contract_dir).validate(doc)


def render_fraction(f: Mapping[str, Any]) -> str:
    return contract.load().render_fraction(f)
