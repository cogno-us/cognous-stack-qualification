"""Family T mutation operators: deterministic, seeded, standard library only, each tagged with one category of the design.

An operator *variant* is a function ``fn(ctx)`` that damages a deep copy of the trace's parsed files (or, for textual damage, the
bytes) and sets what it intended; it raises ``NotApplicable`` when the trace lacks what the mutation needs (the slot is then
counted as ``n_na``, never dropped). Randomness comes only from ``ctx.rng``, seeded per (seed, trace, operator, draw).

Categories follow the catalogue of INDEPENDENT-VERIFIER-DESIGN.md section 4.3 (36 values in the ODES contract). No operator exists
for ``Q`` (semantic quality, not applicable, reported as n/a) or ``L1`` (outcome-label join, stage S6, not a trace mutation).
``intended_codes`` are the refusal codes the operator expects (ODES contract codes where one exists, the verifier's ``wire_*``
codes for wire damage, working names elsewhere). They are frozen with the operator set, before the verifier runs: a verifier that
refuses with a different but correct code is counted in ``any_code`` and not in ``intended_code``.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import copy
import hashlib
import random
from dataclasses import dataclass, field
from typing import Any, Callable

from .jsonio import Pairs, Raw, commitment, dump_file_bytes, dumps
from .trace import FILENAMES, ROLES, Trace

OPERATOR_VERSION = "1"
EXPECTED_ACCEPT = ("B", "F", "R6")
CATEGORIES_WITHOUT_OPERATOR = ("L1", "Q")
NOT_APPLICABLE_CATEGORIES = ("Q",)


class NotApplicable(Exception):
    """The trace does not meet the operator's precondition."""


@dataclass
class Ctx:
    trace: Trace
    rng: random.Random
    peers: list[Trace]
    docs: dict[str, Any] = field(default_factory=dict)
    touched: set[str] = field(default_factory=set)
    raw: dict[str, bytes] = field(default_factory=dict)

    def doc(self, role: str) -> Any:
        if role not in self.trace.files:
            raise NotApplicable(f"no {role} in the trace")
        if role not in self.docs:
            self.docs[role] = copy.deepcopy(self.trace.doc(role))
        self.touched.add(role)
        return self.docs[role]

    def has(self, role: str) -> bool:
        return role in self.trace.files


@dataclass(frozen=True)
class Operator:
    operator_id: str
    category: str
    variant: str
    intended_codes: tuple[str, ...]
    roles: tuple[str, ...]
    description: str
    fn: Callable[[Ctx], None]

    @property
    def expected_verdict(self) -> str:
        return "accept" if self.category in EXPECTED_ACCEPT else "reject"


OPERATORS: list[Operator] = []


def op(category: str, variant: str, codes: tuple[str, ...], roles: tuple[str, ...] = ("run_record",)):
    def deco(fn: Callable[[Ctx], None]) -> Callable[[Ctx], None]:
        OPERATORS.append(Operator(f"{category}.{variant}", category, variant, codes, roles, (fn.__doc__ or "").strip(), fn))
        return fn

    return deco


# ----------------------------------------------------------------------------------------------------------------- helpers

def _digest(rng: random.Random) -> str:
    return "sha256:%064x" % rng.getrandbits(256)


def _decisions(ctx: Ctx, *, result: str | None = None, binding: bool | None = None) -> list[dict[str, Any]]:
    out = [d for d in ctx.doc("run_record")["decisions"]
           if (result is None or d.get("result") == result) and (binding is None or (d.get("binding") is not None) == binding)]
    if not out:
        raise NotApplicable("no decision with the required shape")
    return out


def _rows(ctx: Ctx, key: str) -> list[dict[str, Any]]:
    rows = ctx.doc("run_record").get(key) or []
    if not rows:
        raise NotApplicable(f"no {key} in the record")
    return rows


def _events(ctx: Ctx) -> list[dict[str, Any]]:
    return _rows(ctx, "check_events")


def _ledger_rows(ctx: Ctx) -> dict[str, dict[str, Any]]:
    rows = ctx.doc("destination_ledger").get("effects") or {}
    if not rows:
        raise NotApplicable("no ledger rows")
    return rows


def _replace_member(obj: dict[str, Any], key: str, pairs_for: Callable[[Any], list[tuple[str, Any]]]) -> Pairs:
    out: list[tuple[str, Any]] = []
    for k, v in obj.items():
        out.extend(pairs_for(v) if k == key else [(k, v)])
    return Pairs(out)


def _walk(value: Any):
    yield value
    if isinstance(value, dict):
        for v in value.values():
            yield from _walk(v)
    elif isinstance(value, list):
        for v in value:
            yield from _walk(v)


def _string_leaves(value: Any, path: str = "$"):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from _string_leaves(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from _string_leaves(v, f"{path}[{i}]")
    elif isinstance(value, str):
        yield path, value


def _extension(ctx: Ctx, name: str, value: Any) -> None:
    """Add a free ``x-`` member to the record's top-level ``extensions`` (declared, preserved): isolates a wire defect."""
    rr = ctx.doc("run_record")
    rr.setdefault("extensions", {})[name] = value


# --------------------------------------------------------------------------------------------------- W: wire and text

@op("W1", "dup-result", ("wire_duplicate_member",))
def w1_dup_result(c: Ctx) -> None:
    """A second ``result`` member (the opposite value) written before the real one in a decision, so a last-wins parser reads the original."""
    rr = c.doc("run_record")
    i = c.rng.randrange(len(_decisions(c)))
    d = rr["decisions"][i]
    other = "hold" if d["result"] == "authorized" else "authorized"
    rr["decisions"][i] = _replace_member(d, "result", lambda v: [("result", other), ("result", v)])


@op("W1", "dup-effect-id", ("wire_duplicate_member",))
def w1_dup_effect(c: Ctx) -> None:
    """A second ``effect_id`` member with a different digest written before the real one."""
    rr = c.doc("run_record")
    i = c.rng.randrange(len(_decisions(c)))
    other = _digest(c.rng)
    rr["decisions"][i] = _replace_member(rr["decisions"][i], "effect_id", lambda v: [("effect_id", other), ("effect_id", v)])


@op("W1", "dup-run-id", ("wire_duplicate_member",))
def w1_dup_run(c: Ctx) -> None:
    """A second top-level ``run_id`` member written first."""
    rr = c.doc("run_record")
    other = "run-" + _digest(c.rng)[7:15]
    c.docs["run_record"] = _replace_member(rr, "run_id", lambda v: [("run_id", other), ("run_id", v)])


@op("W2", "nan-in-extension", ("wire_nonfinite_constant",))
def w2_nan_ext(c: Ctx) -> None:
    """``NaN`` as a numeric value inside a declared ``x-`` extension."""
    _extension(c, "x-measure", Raw(c.rng.choice(("NaN", "Infinity", "-Infinity"))))


@op("W2", "nan-proposal-amount", ("wire_nonfinite_constant",), ("proposal_export",))
def w2_nan_proposal(c: Ctx) -> None:
    """A non-JSON constant as the proposal export's ``amount``."""
    c.doc("proposal_export")["amount"] = Raw(c.rng.choice(("NaN", "Infinity", "-Infinity")))


@op("W2", "nonfinite-binding-amount", ("wire_nonfinite_constant",))
def w2_nan_binding(c: Ctx) -> None:
    """A non-JSON constant as a decision binding's ``amount``."""
    d = c.rng.choice(_decisions(c, binding=True))
    d["binding"]["amount"] = Raw(c.rng.choice(("NaN", "Infinity", "-Infinity")))


@op("W2", "nonfinite-ledger-amount", ("wire_nonfinite_constant",), ("destination_ledger",))
def w2_nan_ledger(c: Ctx) -> None:
    """A non-JSON constant as a destination ledger row's ``amount``."""
    row = c.rng.choice(sorted(_ledger_rows(c).items()))[1]
    row["amount"] = Raw(c.rng.choice(("NaN", "Infinity", "-Infinity")))


def _amount_forms(value: float) -> list[str]:
    whole = int(value)
    return [str(whole), f"{whole}.00", f"{whole // 10}e1" if whole % 10 == 0 and whole else f"{whole}e0", f"{whole}.0e0"]


@op("W3", "binding-amount-form", ("wire_number_form_drift", "proposal_commitment_mismatch", "invalid_effect_identity", "profile_ambiguous"))
def w3_binding(c: Ctx) -> None:
    """A binding's ``amount`` written in another number form (``50`` or ``50.00`` or ``5e1`` for ``50.0``): a different canonical byte string."""
    d = c.rng.choice(_decisions(c, binding=True))
    d["binding"]["amount"] = Raw(c.rng.choice(_amount_forms(float(d["binding"]["amount"]))))


@op("W3", "proposal-amount-form", ("wire_number_form_drift", "proposal_commitment_mismatch", "invalid_effect_identity", "profile_ambiguous"), ("proposal_export",))
def w3_proposal(c: Ctx) -> None:
    """The proposal export's ``amount`` written in another number form: its commitment no longer matches the record's."""
    p = c.doc("proposal_export")
    p["amount"] = Raw(c.rng.choice(_amount_forms(float(p["amount"]))))


@op("W3", "ledger-amount-form", ("wire_number_form_drift", "ledger_row_mismatch", "profile_ambiguous"), ("destination_ledger",))
def w3_ledger(c: Ctx) -> None:
    """A ledger row's ``amount`` written in another number form."""
    row = c.rng.choice(sorted(_ledger_rows(c).items()))[1]
    row["amount"] = Raw(c.rng.choice(_amount_forms(float(row["amount"]))))


@op("W4", "lone-surrogate", ("wire_lone_surrogate",))
def w4_surrogate(c: Ctx) -> None:
    """A lone UTF-16 surrogate escape inside a string in a declared ``x-`` extension."""
    _extension(c, "x-note", Raw('"abc\\ud800def"'))


@op("W4", "decomposed-letter", ("proposal_commitment_mismatch", "invalid_effect_identity", "wire_unicode_normalization", "profile_ambiguous"))
def w4_nfd(c: Ctx) -> None:
    """One letter in a string of a decision binding replaced by the letter plus a combining accent (NFD form): different bytes, same look."""
    d = c.rng.choice(_decisions(c, binding=True))
    keys = [k for k in ("target", "actor", "principal", "action_id") if isinstance(d["binding"].get(k), str)]
    key = c.rng.choice(keys)
    text = d["binding"][key]
    spots = [i for i, ch in enumerate(text) if ch in "aeiou"]
    if not spots:
        raise NotApplicable("no vowel to decompose")
    i = c.rng.choice(spots)
    d["binding"][key] = text[: i + 1] + "́" + text[i + 1:]


@op("W5", "byte-order-mark", ("wire_bom",))
def w5_bom(c: Ctx) -> None:
    """A UTF-8 byte-order mark in front of the run record."""
    c.raw["run_record"] = b"\xef\xbb\xbf" + c.trace.files["run_record"]


@op("W5", "trailing-data", ("wire_trailing_data",))
def w5_trailing(c: Ctx) -> None:
    """A second JSON value after the run record."""
    c.raw["run_record"] = c.trace.files["run_record"].rstrip() + b"\n" + c.rng.choice((b"{}", b"[]", b"0")) + b"\n"


@op("W5", "nesting-depth", ("wire_depth",))
def w5_depth(c: Ctx) -> None:
    """A very deeply nested array inside a declared ``x-`` extension."""
    n = c.rng.choice((600, 1200, 5000))
    _extension(c, "x-deep", Raw("[" * n + "]" * n))


# ----------------------------------------------------------------------------------------------------- B: benign (accept)

def _reorder(value: Any, rng: random.Random) -> Any:
    if isinstance(value, dict):
        keys = list(value)
        rng.shuffle(keys)
        return {k: _reorder(value[k], rng) for k in keys}
    if isinstance(value, list):
        return [_reorder(v, rng) for v in value]
    return value


def _touch_all(c: Ctx) -> None:
    for role in ROLES:
        if c.has(role):
            c.doc(role)


@op("B", "key-reorder", ())
def b_reorder(c: Ctx) -> None:
    """Every object's members written in a different order (the pinned profile sorts keys, so the content is the same)."""
    _touch_all(c)
    for role in list(c.docs):
        c.raw[role] = dump_file_bytes(_reorder(c.docs[role], c.rng))


@op("B", "compact-whitespace", ())
def b_compact(c: Ctx) -> None:
    """All insignificant whitespace removed."""
    _touch_all(c)
    for role, doc in c.docs.items():
        c.raw[role] = (dumps(doc, indent=None)).encode("utf-8")


@op("B", "crlf-wide-indent", ())
def b_crlf(c: Ctx) -> None:
    """Four-space indentation with CRLF line ends (valid JSON whitespace)."""
    _touch_all(c)
    for role, doc in c.docs.items():
        c.raw[role] = (dumps(doc, indent=4).replace("\n", "\r\n") + "\r\n").encode("utf-8")


def _escape_some(value: Any, rng: random.Random) -> Any:
    if isinstance(value, dict):
        return {k: _escape_some(v, rng) for k, v in value.items()}
    if isinstance(value, list):
        return [_escape_some(v, rng) for v in value]
    if isinstance(value, str) and value and "\\" not in value and '"' not in value and all(32 <= ord(ch) < 127 for ch in value):
        body = "".join("\\u%04x" % ord(ch) if ch.isalnum() and rng.random() < 0.3 else ch for ch in value)
        return Raw('"' + body + '"')
    return value


@op("B", "unicode-escapes", ())
def b_escapes(c: Ctx) -> None:
    """Some letters and digits inside string values written as ``\\uXXXX`` escapes (same strings, other text)."""
    _touch_all(c)
    for role in list(c.docs):
        c.raw[role] = dump_file_bytes(_escape_some(c.docs[role], c.rng))


# -------------------------------------------------------------------------------------------------- S: structure (V1)

@op("S1", "undeclared-in-decision", ("undeclared_member",))
def s1_decision(c: Ctx) -> None:
    """A member the contract does not declare, on a decision."""
    c.rng.choice(_decisions(c))[c.rng.choice(("surprise", "note", "score"))] = c.rng.randrange(1000)


@op("S1", "undeclared-top-level", ("undeclared_member",))
def s1_top(c: Ctx) -> None:
    """A member the contract does not declare, at the top level."""
    c.doc("run_record")[c.rng.choice(("attestation", "trace_score", "extra"))] = True


@op("S1", "undeclared-in-attempt", ("undeclared_member",))
def s1_attempt(c: Ctx) -> None:
    """A member the contract does not declare, on an attempt row."""
    c.rng.choice(_rows(c, "attempts"))["verified"] = True


@op("S2", "decision-result-unknown", ("unknown_enum_value",))
def s2_result(c: Ctx) -> None:
    """A decision ``result`` outside the closed set (``deny``, ``safe_to_retry``, ``approved``)."""
    c.rng.choice(_decisions(c))["result"] = c.rng.choice(("deny", "safe_to_retry", "approved"))


@op("S2", "reconciliation-result-unknown", ("unknown_enum_value",))
def s2_recon(c: Ctx) -> None:
    """A reconciliation ``result`` outside the closed set."""
    c.rng.choice(_rows(c, "reconciliations"))["result"] = c.rng.choice(("safe_to_retry", "done"))


@op("S2", "attempt-status-unknown", ("unknown_enum_value",))
def s2_attempt(c: Ctx) -> None:
    """An attempt ``status`` outside the closed set."""
    c.rng.choice(_rows(c, "attempts"))["status"] = c.rng.choice(("in_flight", "succeeded"))


@op("S3", "drop-decision-member", ("schema_violation",))
def s3_decision(c: Ctx) -> None:
    """A required decision member removed."""
    d = c.rng.choice(_decisions(c))
    del d[c.rng.choice(("decided_at", "reasons", "time_source", "operation_horizon", "decision_id"))]


@op("S3", "drop-collection", ("schema_violation",))
def s3_collection(c: Ctx) -> None:
    """A required top-level collection removed."""
    rr = c.doc("run_record")
    del rr[c.rng.choice(("closeouts", "refusals", "observations", "reconciliations", "resolution_checks"))]


@op("S3", "drop-attempt-member", ("schema_violation",))
def s3_attempt(c: Ctx) -> None:
    """A required attempt member removed."""
    del c.rng.choice(_rows(c, "attempts"))[c.rng.choice(("started_at", "effect_id", "decision_id"))]


@op("S4", "extension-key-no-prefix", ("invalid_extension_key",))
def s4_top(c: Ctx) -> None:
    """An ``extensions`` member whose name lacks the ``x-`` prefix."""
    c.doc("run_record").setdefault("extensions", {})[c.rng.choice(("note", "score", "trust"))] = 1


@op("S4", "extension-key-no-prefix-decision", ("invalid_extension_key",))
def s4_decision(c: Ctx) -> None:
    """An ``extensions`` member without the ``x-`` prefix on a decision."""
    c.rng.choice(_decisions(c)).setdefault("extensions", {})[c.rng.choice(("note", "tag"))] = 1


# ------------------------------------------------------------------------------------------------ I: identity (V2)

IDENTITY = ("invalid_effect_identity", "proposal_commitment_mismatch", "payload_commitment_mismatch", "manifest_digest_mismatch", "horizon_binding_mismatch", "binding_mismatch")


@op("I1", "effect-id-in-decision", ("invalid_effect_identity", "effect_id_mismatch"))
def i1_decision(c: Ctx) -> None:
    """A decision's ``effect_id`` replaced by another digest (rows that name the effect keep the original)."""
    c.rng.choice(_decisions(c))["effect_id"] = _digest(c.rng)


@op("I1", "effect-id-everywhere", ("invalid_effect_identity",), ("run_record", "destination_ledger"))
def i1_everywhere(c: Ctx) -> None:
    """The ``effect_id`` replaced consistently in every row and in the ledger: only the recomputed identity can show it."""
    d = c.rng.choice(_decisions(c, result="authorized"))
    old, new = d["effect_id"], _digest(c.rng)
    for role in ROLES:
        if role in ("run_record", "destination_ledger") and c.has(role):
            c.raw[role] = c.trace.files[role].replace(old.encode(), new.encode())
    if old.encode() not in c.trace.files["run_record"]:
        raise NotApplicable("effect id not found")


@op("I2", "edit-proposal-amount", IDENTITY, ("run_record", "proposal_export"))
def i2_amount(c: Ctx) -> None:
    """The proposal export's ``amount`` changed while the record's binding is not."""
    p = c.doc("proposal_export")
    p["amount"] = float(p["amount"]) + c.rng.choice((1, 5, 50))


@op("I2", "edit-proposal-target", IDENTITY, ("run_record", "proposal_export"))
def i2_target(c: Ctx) -> None:
    """The proposal export's ``target`` changed while the record's binding is not."""
    p = c.doc("proposal_export")
    p["target"] = p["target"] + "-x"


@op("I2", "edit-proposal-payload", IDENTITY, ("run_record", "proposal_export"))
def i2_payload(c: Ctx) -> None:
    """The proposal export's ``payload`` changed while the record's binding and payload commitment are not."""
    c.doc("proposal_export")["payload"]["refund_reason"] = c.rng.choice(("fraud", "goodwill", "other"))


@op("I3", "horizon-other-proposal", ("horizon_binding_mismatch",))
def i3_horizon(c: Ctx) -> None:
    """A decision's operation horizon commits to a different proposal."""
    c.rng.choice(_decisions(c))["operation_horizon"]["proposal_commitment"] = _digest(c.rng)


@op("I4", "input-commitment-altered", ("record_commitment_mismatch", "journal_unbound_completion", "resolution_check_mismatch"))
def i4_altered(c: Ctx) -> None:
    """One resolution input's ``record_commitment`` altered in the decision (the resolution check keeps the original)."""
    d = c.rng.choice(_decisions(c, result="authorized"))
    c.rng.choice(d["resolution_inputs"])["record_commitment"] = _digest(c.rng)


@op("I4", "missing-input-claims-commitment", ("missing_input_commitment",))
def i4_missing(c: Ctx) -> None:
    """An input marked ``missing`` that still carries a record commitment."""
    d = c.rng.choice(_decisions(c, result="authorized"))
    c.rng.choice([i for i in d["resolution_inputs"] if i["record_commitment"]])["missing"] = True


@op("I5", "payload-commitment-altered", ("payload_commitment_mismatch", "binding_mismatch"))
def i5_payload(c: Ctx) -> None:
    """A binding's ``payload_commitment`` replaced."""
    c.rng.choice(_decisions(c, binding=True))["binding"]["payload_commitment"] = _digest(c.rng)


@op("I5", "manifest-digest-altered", ("manifest_digest_mismatch", "binding_mismatch"))
def i5_manifest_digest(c: Ctx) -> None:
    """A binding's ``manifest_digest`` replaced."""
    c.rng.choice(_decisions(c, binding=True))["binding"]["manifest_digest"] = _digest(c.rng)


@op("I5", "manifest-body-edited", ("manifest_digest_mismatch",), ("run_record", "manifest"))
def i5_manifest_body(c: Ctx) -> None:
    """The manifest file edited while the digests that commit to it are not."""
    m = c.doc("manifest")
    key = c.rng.choice(sorted(k for k, v in m.items() if isinstance(v, str)))
    m[key] = m[key] + "-edited"


# -------------------------------------------------------------------------------------------------- D: decision rules

RECOMPUTE = ("decision_result_inconsistent", "expected_observed_mismatch", "grant_revoked_but_authorized", "input_contradicts_result")


@op("D1", "reasons-on-authorized", ("decision_result_inconsistent",))
def d1_reasons(c: Ctx) -> None:
    """An authorized decision that carries reasons."""
    c.rng.choice(_decisions(c, result="authorized"))["reasons"] = [c.rng.choice(("grant_not_active", "approval_missing", "policy_inactive"))]


@op("D1", "hold-flipped-to-authorized", ("decision_result_inconsistent",))
def d1_flip(c: Ctx) -> None:
    """A held decision whose ``result`` is flipped to authorized while its reasons stay."""
    d = c.rng.choice(_decisions(c, result="hold"))
    if not d.get("reasons"):
        raise NotApplicable("held decision without reasons")
    d["result"] = "authorized"


@op("D2", "binding-stripped", ("decision_result_inconsistent",))
def d2_strip(c: Ctx) -> None:
    """An authorized decision with its binding removed (``null``)."""
    c.rng.choice(_decisions(c, result="authorized", binding=True))["binding"] = None


@op("D3", "grant-observed-contradicts-expected", RECOMPUTE)
def d3_grant(c: Ctx) -> None:
    """The grant input's observed status contradicts its expected status under an authorized result."""
    d = c.rng.choice(_decisions(c, result="authorized"))
    grants = [i for i in d["resolution_inputs"] if i["input_type"] == "grant" and "status" in i.get("observed", {})]
    if not grants:
        raise NotApplicable("no grant input with a status")
    c.rng.choice(grants)["observed"]["status"] = c.rng.choice(("suspended", "expired", "superseded"))


@op("D3", "policy-version-contradicts-expected", RECOMPUTE)
def d3_policy(c: Ctx) -> None:
    """The policy input's observed version contradicts its expected version under an authorized result."""
    d = c.rng.choice(_decisions(c, result="authorized"))
    items = [i for i in d["resolution_inputs"] if i["input_type"] == "policy" and "version" in i.get("observed", {})]
    if not items:
        raise NotApplicable("no policy input with a version")
    c.rng.choice(items)["observed"]["version"] = "0.9"


@op("D4", "unregistered-reason-code", ("reason_code_unregistered", "unknown_reason_code"))
def d4_reason(c: Ctx) -> None:
    """A held decision whose reason is not in the pinned reason registry."""
    d = c.rng.choice(_decisions(c, result="hold"))
    if not d.get("reasons"):
        raise NotApplicable("held decision without reasons")
    d["reasons"][0] = c.rng.choice(("made_up_reason", "grant_probably_fine", "reason_0000"))


@op("D4", "vocabulary-version-removed", ("vocabulary_version_missing",))
def d4_vocab(c: Ctx) -> None:
    """A journal-mode decision with its reason vocabulary version removed."""
    ds = [d for d in _decisions(c) if "reason_vocabulary_version" in d]
    if not ds:
        raise NotApplicable("not journal mode")
    del c.rng.choice(ds)["reason_vocabulary_version"]


@op("D5", "grant-revoked-but-authorized", RECOMPUTE)
def d5_revoked(c: Ctx) -> None:
    """The grant input observed as ``revoked`` while the decision stays authorized (the one recomputable reason code)."""
    d = c.rng.choice(_decisions(c, result="authorized"))
    grants = [i for i in d["resolution_inputs"] if i["input_type"] == "grant" and "status" in i.get("observed", {})]
    if not grants:
        raise NotApplicable("no grant input with a status")
    c.rng.choice(grants)["observed"]["status"] = "revoked"


# ----------------------------------------------------------------------------------------------------- J: journal

@op("J1", "drop-opened-event", ("journal_protocol", "journal_lineage_mismatch"))
def j1_drop(c: Ctx) -> None:
    """A check's ``opened`` journal event removed."""
    ev = _events(c)
    del ev[c.rng.choice([i for i, e in enumerate(ev) if e["phase"] == "opened"])]


@op("J1", "duplicate-opened-event", ("journal_protocol",))
def j1_dup(c: Ctx) -> None:
    """A check's ``opened`` journal event written twice."""
    ev = _events(c)
    i = c.rng.choice([i for i, e in enumerate(ev) if e["phase"] == "opened"])
    ev.insert(i + 1, copy.deepcopy(ev[i]))


@op("J2", "completed-matches-no-resolution-check", ("journal_unbound_completion",))
def j2_unbound(c: Ctx) -> None:
    """A resolution check's id changed so a completed journal check matches no resolution check."""
    if not _events(c):
        raise NotApplicable("not journal mode")
    c.rng.choice(_rows(c, "resolution_checks"))["check_id"] = "00000000-0000-4000-8000-%012x" % c.rng.getrandbits(48)


@op("J2", "resolution-checks-reordered", ("resolution_checks_out_of_order",))
def j2_reorder(c: Ctx) -> None:
    """Two resolution checks listed in the reverse of their order."""
    rows = _rows(c, "resolution_checks")
    if len(rows) < 2:
        raise NotApplicable("fewer than two resolution checks")
    rows.reverse()


@op("J3", "completed-rewritten-as-interrupted", ("journal_protocol", "journal_unbound_completion"))
def j3_interrupted(c: Ctx) -> None:
    """A completed check's journal event rewritten as ``interrupted`` while its resolution check stays (the inverse of the design's rewrite: no real clean trace holds an interrupted check)."""
    ev = _events(c)
    c.rng.choice([e for e in ev if e["phase"] == "completed"])["phase"] = "interrupted"


@op("J3", "completed-event-dropped", ("journal_protocol", "journal_unbound_completion"))
def j3_dropped(c: Ctx) -> None:
    """A check left opened-only (its ``completed`` event removed) while its resolution check stays."""
    ev = _events(c)
    del ev[c.rng.choice([i for i, e in enumerate(ev) if e["phase"] == "completed"])]


# ---------------------------------------------------------------------------------------------------------- T: times

def _strip_offset(text: str) -> str:
    return text.replace("+00:00", "").replace("Z", "")


@op("T1", "naive-decided-at", ("timestamp_invalid",))
def t1_naive(c: Ctx) -> None:
    """A decision time written without a UTC offset."""
    d = c.rng.choice(_decisions(c))
    d["decided_at"] = _strip_offset(d["decided_at"])


@op("T1", "naive-input-time-floor", ("timestamp_invalid",))
def t1_floor(c: Ctx) -> None:
    """An input time floor written without a UTC offset."""
    floors = c.doc("run_record").get("input_time_floors") or {}
    if not floors:
        raise NotApplicable("no input time floors")
    k = c.rng.choice(sorted(floors))
    floors[k] = _strip_offset(floors[k])


def _retime_observation(c: Ctx, new_time: str) -> None:
    rr = c.doc("run_record")
    obs = rr.get("observations") or []
    accepted = [o for o in obs if o.get("state") in ("applied", "absent", "partial")]
    if not accepted:
        raise NotApplicable("no observation")
    target = c.rng.choice(accepted)
    old = target["observed_at"]
    for node in _walk([rr["observations"], rr["reconciliations"], rr["closeouts"]]):
        if isinstance(node, dict) and node.get("observed_at") == old and node.get("effect_id") == target["effect_id"]:
            node["observed_at"] = new_time


@op("T1", "observation-from-the-future", ("observation_time_future",))
def t1_future(c: Ctx) -> None:
    """An observation (in every row that carries it) stamped after the evaluation time."""
    _retime_observation(c, "2027-01-01T00:00:00+00:00")


@op("T1", "stale-observation", ("observation_stale",))
def t1_stale(c: Ctx) -> None:
    """An observation (in every row that carries it) stamped long before the evaluation time."""
    _retime_observation(c, "2026-01-01T00:00:00+00:00")


# ------------------------------------------------------------------------------------------------------ A: attempts

@op("A1", "drop-start-record", ("missing_start_record",))
def a1_start(c: Ctx) -> None:
    """The ``attempted`` start row of an attempt removed."""
    rows = _rows(c, "attempts")
    starts = [i for i, a in enumerate(rows) if a["status"] == "attempted"]
    if not starts or len(rows) < 2:
        raise NotApplicable("no attempt with a start row and later rows")
    del rows[c.rng.choice(starts)]


@op("A1", "second-attempt-for-effect", ("second_attempt_for_effect",))
def a1_second(c: Ctx) -> None:
    """A second attempt lifecycle started for an effect that already has one."""
    rows = _rows(c, "attempts")
    start = copy.deepcopy(c.rng.choice([a for a in rows if a["status"] == "attempted"] or rows))
    start["attempt_id"] = "00000000-0000-4000-8000-%012x" % c.rng.getrandbits(48)
    start["status"] = "attempted"
    start["acknowledgement"] = {}
    start["error"] = None
    rows.append(start)


@op("A1", "attempt-on-held-decision", ("attempt_on_unauthorized_decision",))
def a1_held(c: Ctx) -> None:
    """An attempt row written against a held decision."""
    d = c.rng.choice(_decisions(c, result="hold"))
    c.doc("run_record")["attempts"].append({
        "attempt_id": "00000000-0000-4000-8000-%012x" % c.rng.getrandbits(48), "effect_id": d["effect_id"], "decision_id": d["decision_id"],
        "started_at": d["decided_at"], "time_source": d["time_source"], "status": "attempted", "acknowledgement": {}, "error": None})


@op("A2", "drop-closeouts", ("closeout_missing",))
def a2_drop(c: Ctx) -> None:
    """The closeouts of uncertain attempts removed."""
    rr = c.doc("run_record")
    if not rr.get("closeouts") or not any(a["status"] == "unknown" for a in rr["attempts"]):
        raise NotApplicable("no uncertain attempt with a closeout")
    rr["closeouts"] = []


@op("A2", "closeout-observation-mismatch", ("closeout_observation_missing",))
def a2_obs(c: Ctx) -> None:
    """A closeout that names an observation time no accepted observation has."""
    row = c.rng.choice(_rows(c, "closeouts"))
    row["observed_at"] = "2026-10-05T18:30:00+00:00"


# ----------------------------------------------------------------------------------------------------- R: receipts (V4)

@op("R1", "unauthorized-ledger-effect", ("ledger_effect_without_decision", "unauthorized_effect"), ("run_record", "destination_ledger"))
def r1_inject(c: Ctx) -> None:
    """A ledger effect row for an effect no decision names (an injected unauthorized effect)."""
    ledger = c.doc("destination_ledger")
    rows = ledger.setdefault("effects", {})
    c.doc("run_record")
    template = copy.deepcopy(rows[sorted(rows)[0]]) if rows else {"amount": 50.0, "grant_id": "urn:cognous:grant:routine-1", "payload": {}, "state": "applied", "target": "urn:cognous:synthetic-account:customer-001", "unit": "USD"}
    eid = _digest(c.rng)
    template["effect_id"] = eid
    rows[eid] = template
    counts = ledger.setdefault("grant_effect_counts", {})
    counts[template["grant_id"]] = counts.get(template["grant_id"], 0) + 1


@op("R2", "ledger-effect-for-held-decision", ("ledger_effect_for_held_decision", "unauthorized_effect"), ("run_record", "destination_ledger"))
def r2_held(c: Ctx) -> None:
    """A ledger effect row for an effect whose decision is a hold."""
    d = c.rng.choice(_decisions(c, result="hold"))
    ledger = c.doc("destination_ledger")
    rows = ledger.setdefault("effects", {})
    rows[d["effect_id"]] = {"amount": 50.0, "effect_id": d["effect_id"], "grant_id": "urn:cognous:grant:routine-1", "payload": {}, "state": "applied",
                            "target": "urn:cognous:synthetic-account:customer-001", "unit": "USD"}
    counts = ledger.setdefault("grant_effect_counts", {})
    counts["urn:cognous:grant:routine-1"] = counts.get("urn:cognous:grant:routine-1", 0) + 1


@op("R3", "ledger-amount-differs", ("ledger_row_mismatch", "ledger_binding_mismatch"), ("run_record", "destination_ledger"))
def r3_amount(c: Ctx) -> None:
    """A ledger row whose amount differs from the decision's binding."""
    row = c.rng.choice(sorted(_ledger_rows(c).items()))[1]
    row["amount"] = float(row["amount"]) + c.rng.choice((1.0, 10.0, 100.0))


@op("R3", "ledger-target-differs", ("ledger_row_mismatch", "ledger_binding_mismatch"), ("run_record", "destination_ledger"))
def r3_target(c: Ctx) -> None:
    """A ledger row whose target differs from the decision's binding."""
    row = c.rng.choice(sorted(_ledger_rows(c).items()))[1]
    row["target"] = row["target"] + "-x"


@op("R3", "ledger-grant-differs", ("ledger_row_mismatch", "ledger_binding_mismatch"), ("run_record", "destination_ledger"))
def r3_grant(c: Ctx) -> None:
    """A ledger row that names a different grant than the decision's binding."""
    row = c.rng.choice(sorted(_ledger_rows(c).items()))[1]
    row["grant_id"] = "urn:cognous:grant:other-%d" % c.rng.randrange(100)


@op("R4", "second-ledger-row", ("excess_duplicate_effect", "ledger_duplicate_effect"), ("run_record", "destination_ledger"))
def r4_second(c: Ctx) -> None:
    """A second ledger row (under another key) for one effect, with the grant's effect count raised."""
    ledger = c.doc("destination_ledger")
    rows = _ledger_rows(c)
    key, row = c.rng.choice(sorted(rows.items()))
    rows[key + "-dup"] = copy.deepcopy(row)
    counts = ledger.setdefault("grant_effect_counts", {})
    counts[row["grant_id"]] = counts.get(row["grant_id"], 0) + 1


@op("R4", "duplicate-attempt-acknowledgement", ("excess_duplicate_effect", "second_attempt_for_effect"), ("run_record",))
def r4_ack(c: Ctx) -> None:
    """An acknowledged attempt row written twice."""
    rows = _rows(c, "attempts")
    acks = [a for a in rows if a["status"] == "acknowledged"]
    if not acks:
        raise NotApplicable("no acknowledged attempt")
    rows.append(copy.deepcopy(c.rng.choice(acks)))


@op("R5", "drop-ledger-row", ("acknowledged_attempt_without_ledger_row", "ledger_row_missing"), ("run_record", "destination_ledger"))
def r5_drop(c: Ctx) -> None:
    """The ledger row of an acknowledged attempt removed (a dropped receipt)."""
    rr = c.doc("run_record")
    acked = {a["effect_id"] for a in rr["attempts"] if a["status"] == "acknowledged"}
    ledger = c.doc("destination_ledger")
    rows = _ledger_rows(c)
    hit = sorted(k for k, r in rows.items() if r.get("effect_id") in acked)
    if not hit:
        raise NotApplicable("no acknowledged attempt with a ledger row")
    row = rows.pop(c.rng.choice(hit))
    counts = ledger.get("grant_effect_counts", {})
    if counts.get(row["grant_id"], 0) > 0:
        counts[row["grant_id"]] -= 1


@op("R6", "truncate-ledger-tail", ("ledger_row_missing",), ("run_record", "destination_ledger"))
def r6_tail(c: Ctx) -> None:
    """The ledger row of an effect whose acknowledgement was lost removed (a truncated tail; expected accepted: there is no sequence or chain)."""
    rr = c.doc("run_record")
    uncertain = {a["effect_id"] for a in rr["attempts"] if a["status"] == "unknown"}
    ledger = c.doc("destination_ledger")
    rows = _ledger_rows(c)
    hit = sorted(k for k, r in rows.items() if r.get("effect_id") in uncertain)
    if not hit:
        raise NotApplicable("no uncertain attempt with a ledger row")
    row = rows.pop(hit[-1])
    counts = ledger.get("grant_effect_counts", {})
    if counts.get(row["grant_id"], 0) > 0:
        counts[row["grant_id"]] -= 1


# ------------------------------------------------------------------------------- X: transplant, F: forgery bound

def _peer(c: Ctx, role: str) -> Trace:
    options = [p for p in c.peers if p.trace_id != c.trace.trace_id and role in p.files and p.files[role] != c.trace.files.get(role)]
    if not options or role not in c.trace.files:
        raise NotApplicable(f"no peer trace with a different {role}")
    return c.rng.choice(options)


@op("X1", "decision-from-another-run", ("effect_id_mismatch", "invalid_effect_identity", "transplanted_record"))
def x1_decision(c: Ctx) -> None:
    """A decision copied from another run in place of this run's decision."""
    peer = _peer(c, "run_record")
    rr = c.doc("run_record")
    rr["decisions"][c.rng.randrange(len(_decisions(c)))] = copy.deepcopy(peer.doc("run_record")["decisions"][0])


@op("X1", "proposal-from-another-run", ("proposal_commitment_mismatch", "invalid_effect_identity", "transplanted_record"), ("run_record", "proposal_export"))
def x1_proposal(c: Ctx) -> None:
    """The proposal export of another run supplied with this run's record."""
    c.raw["proposal_export"] = _peer(c, "proposal_export").files["proposal_export"]


@op("X1", "ledger-from-another-run", ("ledger_effect_without_decision", "transplanted_record"), ("run_record", "destination_ledger"))
def x1_ledger(c: Ctx) -> None:
    """The destination ledger of another run supplied with this run's record."""
    c.raw["destination_ledger"] = _peer(c, "destination_ledger").files["destination_ledger"]


@op("F", "reseal-amount-change", (), ("run_record", "proposal_export", "destination_ledger"))
def f_reseal(c: Ctx) -> None:
    """The proposal amount changed and every commitment that depends on it recomputed (proposal, effect id, rows, ledger): self-consistent, so expected accepted."""
    if not (c.has("proposal_export") and c.has("run_record")):
        raise NotApplicable("needs a proposal export")
    p = c.doc("proposal_export")
    rr = c.doc("run_record")
    ds = [d for d in rr["decisions"] if d.get("result") == "authorized" and d.get("binding")]
    if len(ds) != 1:
        raise NotApplicable("needs exactly one authorized decision")
    d = ds[0]
    b = d["binding"]
    old_pc = commitment(c.trace.doc("proposal_export"))
    old_eid = commitment({"proposal": old_pc, "grant_id": b["grant_id"], "grant_revision": b["grant_revision"]})
    if old_pc != b["proposal_commitment"] or old_eid != d["effect_id"]:
        raise NotApplicable("the recipe does not reproduce this record's commitments")
    old_amount = p["amount"]
    new_amount = float(old_amount) + 10.0
    p["amount"] = new_amount
    new_pc = commitment(p)
    new_eid = commitment({"proposal": new_pc, "grant_id": b["grant_id"], "grant_revision": b["grant_revision"]})
    texts = {}
    for role in ("run_record", "destination_ledger"):
        if c.has(role):
            doc = c.doc(role)
            for node in _walk(doc):
                if isinstance(node, dict) and node.get("amount") == old_amount and ("effect_id" in node or "grant_id" in node):
                    node["amount"] = new_amount
            texts[role] = dumps(doc).replace(old_pc, new_pc).replace(old_eid, new_eid)
    for role, text in texts.items():
        c.raw[role] = (text + "\n").encode("utf-8")
    if c.has("destination_ledger"):
        c.touched.add("destination_ledger")


# --------------------------------------------------------------------------------------------------------- build / API

def build_files(trace: Trace, ctx: Ctx) -> dict[str, bytes]:
    files = dict(trace.files)
    for role in ctx.touched:
        if role in ctx.docs:
            files[role] = dump_file_bytes(ctx.docs[role])
    files.update(ctx.raw)
    return files


def rng_for(seed: int, trace_id: str, operator_id: str, draw: int) -> random.Random:
    material = f"{seed}|{trace_id}|{operator_id}|{draw}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest()[:16], "big"))


def operator_catalogue() -> list[dict[str, Any]]:
    """The operator set as data (the frozen file ``operators.json`` is this list plus the seed, draws and the source digest)."""
    out = []
    for o in sorted(OPERATORS, key=lambda x: x.operator_id):
        out.append({
            "operator_id": o.operator_id, "category": o.category, "variant": o.variant, "expected_verdict": o.expected_verdict,
            "intended_codes": list(o.intended_codes), "roles": list(o.roles), "description": o.description,
        })
    return out


def categories_with_operator() -> list[str]:
    return sorted({o.category for o in OPERATORS})


assert all(r in FILENAMES for r in ROLES)
