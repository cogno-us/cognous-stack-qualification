"""Family H mutation operators (catalogue version 3): damage to the outside-held witness and the holder inventory, over witnessed traces.

Categories H1 to H8 of INDEPENDENT-VERIFIER-DESIGN.md section 4.3 (revision of 2026-10-18, decision 28), plus the two controls that the
ODES verification-report contract admits in a witnessed population: B (benign, expected accept) and F (forgery bound, expected accept).
H7 and H8 are controls with expected verdict ``abstain``. Deterministic, seeded, standard library only; randomness only from ``ctx.rng``.

Independence note. These operators were written from the ODES design (family H rows, section 4.4, the non-claims), the ODES
``witness-digest``, ``holder-inventory`` and ``verification-report`` drafts, and the control plane's producer code
(``agent_control_plane/witness.py``: ``make_record``, ``head_digest``, ``check_witness_chain``, ``verify_against_witness``,
``LocalFileWitness``, ``acp witness publish``). The verifier's own damage tests and witness test fixtures were NOT read. The witness
re-derivation below (ledger heads, record digest) is this harness's own implementation of the profile text. They were written after
the verifier's tier V3 existed and its documentation (``docs/tiers.md``) and CLI help had been read, so they are not held-out; the
intended codes were frozen post-hoc from the codes the verifier emits (see the suite README, catalogue version 3).

A witness file is JSON lines (``acp witness publish`` writes one sorted compact object per line). Operators that change a witness
record and say "re-chained" or "digest recomputed" recompute exactly the members named so that only the stated defect remains.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import copy
import json
from typing import Any, Callable

from .jsonio import Pairs, Raw, commitment, dump_file_bytes, dumps
from .operators import Ctx, NotApplicable, Operator, _drop_row_of_uncertain, f_reseal
from .trace import ABSENT_FILE, ROLES

WITNESS_OPERATORS: list[Operator] = []
GENESIS = "sha256:" + "0" * 64
VERSION = "witness-digest/0.1"

C_CHAIN = "witness_chain_invalid"
C_RUN = "witness_run_mismatch"
C_SHAPE = "witness_record_shape"
C_VERSION = "witness_version_unsupported"
C_SHRUNK = "witness_ledger_shrunk"
C_HEAD = "witness_ledger_head_mismatch"
C_INV = "holder_inventory_shape"


def hop(category: str, variant: str, codes: tuple[str, ...], roles: tuple[str, ...] = ("run_record", "witness"), expected_outcome: str = ""):
    def deco(fn: Callable[[Ctx], None]) -> Callable[[Ctx], None]:
        # one line, whitespace collapsed: Python 3.13 dedents docstrings at compile time and 3.12 does not, and operators.json must not depend on it
        WITNESS_OPERATORS.append(Operator(f"{category}.{variant}", category, variant, codes, roles, " ".join((fn.__doc__ or "").split()), fn, expected_outcome))
        return fn

    return deco


# ----------------------------------------------------------------------------------------------- profile re-derivation

def _line(record: Any) -> bytes:
    return (json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def ledgers(doc: dict[str, Any]) -> dict[str, list[Any]]:
    """Every list-valued top-level member of the record document, in name order (the profile's ledger definition)."""
    return {k: v for k, v in sorted(doc.items()) if isinstance(v, list)}


def head(rows: list[Any]) -> str:
    h = GENESIS
    for row in rows:
        h = commitment({"prev": h, "row": commitment(row)})
    return h


def head_digest(doc: dict[str, Any], counts: dict[str, int] | None = None) -> dict[str, dict[str, Any]]:
    """Per-ledger ``{count, head}``; with ``counts`` only those ledgers, each over its first ``count`` rows (empty ledgers omitted)."""
    out = {}
    for name, rows in ledgers(doc).items():
        n = len(rows) if counts is None else counts.get(name, 0)
        if n > 0 and n <= len(rows):
            out[name] = {"count": n, "head": head(rows[:n])}
    return out


def redigest(record: dict[str, Any]) -> dict[str, Any]:
    record["digest"] = commitment({k: v for k, v in record.items() if k != "digest"})
    return record


def rechain(records: list[dict[str, Any]], start: int = 0) -> list[dict[str, Any]]:
    prev = None
    for i, r in enumerate(records):
        r["sequence"] = start + i
        r["previous_digest"] = prev
        redigest(r)
        prev = r["digest"]
    return records


def make_record(doc: dict[str, Any], run_id: str, counts: dict[str, int] | None = None) -> dict[str, Any]:
    return {"version": VERSION, "run_id": run_id, "sequence": 0, "previous_digest": None, "ledgers": head_digest(doc, counts)}


# ------------------------------------------------------------------------------------------------------- ctx helpers

def wit(c: Ctx) -> list[dict[str, Any]]:
    """A deep copy of the trace's witness records (oldest first)."""
    if not c.has("witness"):
        raise NotApplicable("no witness in the trace")
    text = c.trace.files["witness"].decode("utf-8")
    records = [json.loads(line) for line in text.splitlines() if line.strip()]
    if not records:
        raise NotApplicable("the witness holds no record")
    return records


def put(c: Ctx, records: list[Any]) -> None:
    c.raw["witness"] = b"".join(_line(r) for r in records)


def put_text(c: Ctx, lines: list[str]) -> None:
    c.raw["witness"] = "".join(line + "\n" for line in lines).encode("utf-8")


def rec(c: Ctx) -> dict[str, Any]:
    """The run record document (a working copy; saved when the operator returns)."""
    return c.doc("run_record")


def covered(c: Ctx, records: list[dict[str, Any]], min_count: int = 1) -> list[str]:
    names = sorted(n for n, e in records[-1]["ledgers"].items() if e["count"] >= min_count)
    if not names:
        raise NotApplicable("the latest witness record covers no ledger with enough rows")
    return names


def need_records(records: list[Any], n: int) -> None:
    if len(records) < n:
        raise NotApplicable(f"the witness holds fewer than {n} records")


def _rand_digest(c: Ctx) -> str:
    return "sha256:%064x" % c.rng.getrandbits(256)


def _peer_witness(c: Ctx, same_run_id: bool | None) -> bytes:
    mine = wit(c)[-1]["run_id"]
    options = []
    for p in c.peers:
        if "witness" not in p.files or p.files["witness"] == c.trace.files["witness"]:
            continue
        theirs = json.loads(p.files["witness"].decode("utf-8").splitlines()[0])["run_id"]
        if same_run_id is None or (theirs == mine) == same_run_id:
            options.append(p)
    if not options:
        raise NotApplicable("no peer witness of the required kind")
    return c.rng.choice(options).files["witness"]


def _differing_pair(rows: list[Any], c: Ctx) -> tuple[int, int]:
    pairs = [(i, j) for i in range(len(rows)) for j in range(i + 1, len(rows)) if commitment(rows[i]) != commitment(rows[j])]
    if not pairs:
        raise NotApplicable("no two distinct rows")
    return c.rng.choice(pairs)


def _ledger_with(c: Ctx, records: list[dict[str, Any]], min_rows: int) -> str:
    doc = rec(c)
    names = [n for n in covered(c, records) if len(doc.get(n, [])) >= min_rows and records[-1]["ledgers"][n]["count"] >= min_rows]
    if not names:
        raise NotApplicable(f"no covered ledger with {min_rows} or more covered rows")
    return c.rng.choice(names)


def _string_paths(value: Any, path: tuple = ()) -> list[tuple]:
    out = []
    if isinstance(value, dict):
        for k in sorted(value):
            out += _string_paths(value[k], path + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            out += _string_paths(v, path + (i,))
    elif isinstance(value, str) and value:
        out.append(path)
    return out


def _set(obj: Any, path: tuple, value: Any) -> None:
    for k in path[:-1]:
        obj = obj[k]
    obj[path[-1]] = value


def _get(obj: Any, path: tuple) -> Any:
    for k in path:
        obj = obj[k]
    return obj


# ============================================================================ H1: witness chain break (expected reject)

@hop("H1", "previous-digest-relinked", (C_CHAIN,))
def h1_prev(c: Ctx) -> None:
    """A later record's ``previous_digest`` pointed at another digest, the record's own ``digest`` recomputed (only the link is broken)."""
    rs = wit(c)
    need_records(rs, 2)
    i = c.rng.randrange(1, len(rs))
    rs[i]["previous_digest"] = _rand_digest(c)
    redigest(rs[i])
    put(c, rs)


@hop("H1", "first-record-gains-previous-digest", (C_CHAIN,))
def h1_first_prev(c: Ctx) -> None:
    """The first record given a ``previous_digest`` (it claims a predecessor the file does not hold), digest recomputed."""
    rs = wit(c)
    rs[0]["previous_digest"] = _rand_digest(c)
    redigest(rs[0])
    put(c, rs)


@hop("H1", "sequence-shifted", (C_CHAIN,))
def h1_seq(c: Ctx) -> None:
    """One record's ``sequence`` no longer its index (shifted by 1 to 3), digest recomputed."""
    rs = wit(c)
    i = c.rng.randrange(len(rs))
    rs[i]["sequence"] = rs[i]["sequence"] + c.rng.randint(1, 3)
    redigest(rs[i])
    put(c, rs)


@hop("H1", "rechained-from-one", (C_CHAIN,))
def h1_from_one(c: Ctx) -> None:
    """The whole chain re-chained with sequences starting at 1: links and digests consistent, sequence is not the index."""
    rs = wit(c)
    put(c, rechain(rs, start=1))


@hop("H1", "digest-replaced", (C_CHAIN,))
def h1_digest(c: Ctx) -> None:
    """One record's ``digest`` replaced by another well-formed digest (not recomputed)."""
    rs = wit(c)
    rs[c.rng.randrange(len(rs))]["digest"] = _rand_digest(c)
    put(c, rs)


@hop("H1", "head-edited-digest-stale", (C_CHAIN, C_HEAD))
def h1_stale(c: Ctx) -> None:
    """A held ledger head edited without recomputing the record's ``digest`` (the record no longer recomputes)."""
    rs = wit(c)
    i = c.rng.randrange(len(rs))
    names = sorted(rs[i]["ledgers"])
    if not names:
        raise NotApplicable("record covers no ledger")
    rs[i]["ledgers"][c.rng.choice(names)]["head"] = _rand_digest(c)
    put(c, rs)


@hop("H1", "record-removed", (C_CHAIN,))
def h1_removed(c: Ctx) -> None:
    """A record other than the latest removed from the chain, nothing re-chained (removing the latest is the H7 tail truncation)."""
    rs = wit(c)
    need_records(rs, 2)
    del rs[c.rng.randrange(len(rs) - 1)]
    put(c, rs)


@hop("H1", "digest-line-duplicated", (C_CHAIN,))
def h1_dup_line(c: Ctx) -> None:
    """One witness line written twice in a row (a duplicated digest line)."""
    rs = wit(c)
    i = c.rng.randrange(len(rs))
    put(c, rs[: i + 1] + [copy.deepcopy(rs[i])] + rs[i + 1:])


@hop("H1", "lines-reordered", (C_CHAIN,))
def h1_reorder(c: Ctx) -> None:
    """Two witness lines swapped (each record unchanged)."""
    rs = wit(c)
    need_records(rs, 2)
    i, j = sorted(c.rng.sample(range(len(rs)), 2))
    rs[i], rs[j] = rs[j], rs[i]
    put(c, rs)


@hop("H1", "forged-record-inserted", (C_CHAIN,))
def h1_inserted(c: Ctx) -> None:
    """A forged record (a copy of an existing one, digest recomputed) inserted before the latest record without re-chaining what follows."""
    rs = wit(c)
    i = c.rng.randrange(len(rs))
    forged = copy.deepcopy(rs[i])
    redigest(forged)
    rs.insert(i, forged)
    put(c, rs)


@hop("H1", "spliced-with-another-run", (C_CHAIN, C_RUN, C_HEAD, C_SHRUNK))
def h1_splice(c: Ctx) -> None:
    """A record of another run's witness spliced onto this chain as its newest record, re-linked (sequence, previous digest, digest recomputed)."""
    rs = wit(c)
    other = [json.loads(line) for line in _peer_witness(c, None).decode("utf-8").splitlines() if line.strip()]
    donor = copy.deepcopy(c.rng.choice(other))
    donor["sequence"] = len(rs)
    donor["previous_digest"] = rs[-1]["digest"]
    redigest(donor)
    put(c, rs + [donor])


# ============================================================================ H2: witness run-id mismatch (expected reject)

@hop("H2", "witness-of-another-run-id", (C_RUN,))
def h2_other(c: Ctx) -> None:
    """The witness file of another run (whose records name a different ``run_id``) supplied with this run's record."""
    c.raw["witness"] = _peer_witness(c, False)


@hop("H2", "witness-of-another-run-same-run-id", (C_RUN, C_SHRUNK, C_HEAD))
def h2_same_name(c: Ctx) -> None:
    """The witness file of another run that uses the same ``run_id`` string (the producers here name most runs ``run-1``): the run id
    cannot tell the runs apart, only the heads can."""
    c.raw["witness"] = _peer_witness(c, True)


def _rename_run(c: Ctx, fn: Callable[[str], str]) -> None:
    rs = wit(c)
    new = fn(rs[0]["run_id"])
    if new == rs[0]["run_id"]:
        raise NotApplicable("the renaming leaves the run id unchanged")
    for r in rs:
        r["run_id"] = new
    put(c, rechain(rs))


@hop("H2", "run-id-rewritten-rechained", (C_RUN,))
def h2_rewritten(c: Ctx) -> None:
    """Every record's ``run_id`` replaced by another run id, chain re-computed (internally consistent, wrong run)."""
    _rename_run(c, lambda old: "run-" + _rand_digest(c)[7:15])


@hop("H2", "run-id-case-changed", (C_RUN,))
def h2_case(c: Ctx) -> None:
    """The run id upper-cased in every record, chain re-computed (a different string that reads alike)."""
    _rename_run(c, lambda old: old.upper())


@hop("H2", "run-id-trailing-space", (C_RUN,))
def h2_space(c: Ctx) -> None:
    """A trailing space appended to the run id in every record, chain re-computed."""
    _rename_run(c, lambda old: old + " ")


@hop("H2", "run-id-lookalike-hyphen", (C_RUN,))
def h2_lookalike(c: Ctx) -> None:
    """The ASCII hyphen in the run id replaced by U+2010 HYPHEN in every record, chain re-computed (looks identical)."""
    _rename_run(c, lambda old: old.replace("-", "‐"))


@hop("H2", "record-run-id-changed", (C_RUN, "run_id_mismatch"))
def h2_record(c: Ctx) -> None:
    """The run record's top-level ``run_id`` changed; the witness unchanged (the witness now covers another run than the record)."""
    doc = rec(c)
    if not isinstance(doc.get("run_id"), str):
        raise NotApplicable("record has no run id")
    doc["run_id"] = doc["run_id"] + "-" + _rand_digest(c)[7:11]


# ============================================================================ H3: witness version or shape damage (expected reject)

def _one(c: Ctx) -> tuple[list[dict[str, Any]], int]:
    rs = wit(c)
    return rs, c.rng.randrange(len(rs))


@hop("H3", "version-next-minor", (C_VERSION,))
def h3_v02(c: Ctx) -> None:
    """``version`` of one record set to ``witness-digest/0.2``, digest recomputed."""
    rs, i = _one(c)
    rs[i]["version"] = "witness-digest/0.2"
    redigest(rs[i])
    put(c, rs)


@hop("H3", "version-other-profile", (C_VERSION,))
def h3_other_profile(c: Ctx) -> None:
    """``version`` of one record set to another profile's name (``holder-inventory/0.1``), digest recomputed."""
    rs, i = _one(c)
    rs[i]["version"] = "holder-inventory/0.1"
    redigest(rs[i])
    put(c, rs)


@hop("H3", "version-not-a-string", (C_VERSION, C_SHAPE))
def h3_version_number(c: Ctx) -> None:
    """``version`` of one record written as the number ``0.1``, digest recomputed."""
    rs, i = _one(c)
    rs[i]["version"] = 0.1
    redigest(rs[i])
    put(c, rs)


@hop("H3", "version-trailing-space", (C_VERSION,))
def h3_version_space(c: Ctx) -> None:
    """``version`` with a trailing space, digest recomputed."""
    rs, i = _one(c)
    rs[i]["version"] = VERSION + " "
    redigest(rs[i])
    put(c, rs)


@hop("H3", "member-missing", (C_SHAPE, C_CHAIN))
def h3_missing(c: Ctx) -> None:
    """One required member (``sequence``, ``previous_digest``, ``ledgers`` or ``run_id``) removed from a record, digest recomputed."""
    rs, i = _one(c)
    del rs[i][c.rng.choice(("sequence", "previous_digest", "ledgers", "run_id"))]
    redigest(rs[i])
    put(c, rs)


@hop("H3", "digest-member-missing", (C_SHAPE, C_CHAIN))
def h3_no_digest(c: Ctx) -> None:
    """The ``digest`` member removed from one record."""
    rs, i = _one(c)
    del rs[i]["digest"]
    put(c, rs)


@hop("H3", "signer-or-proof-member", (C_SHAPE, "undeclared_member"))
def h3_signer(c: Ctx) -> None:
    """A member that looks like a signer, proof or publication time added to a record, digest recomputed (the profile has none; it must
    not be read as one)."""
    rs, i = _one(c)
    name, value = c.rng.choice((("signer", "urn:cognous:principal:witness-holder"), ("proof", "ed25519:" + _rand_digest(c)[7:]),
                                ("published_at", "2026-10-05T19:00:00Z")))
    rs[i][name] = value
    redigest(rs[i])
    put(c, rs)


@hop("H3", "sequence-as-string", (C_SHAPE, C_CHAIN))
def h3_seq_str(c: Ctx) -> None:
    """``sequence`` written as a string (``"0"``), digest recomputed."""
    rs, i = _one(c)
    rs[i]["sequence"] = str(rs[i]["sequence"])
    redigest(rs[i])
    put(c, rs)


@hop("H3", "sequence-as-float", (C_SHAPE, C_CHAIN))
def h3_seq_float(c: Ctx) -> None:
    """``sequence`` written as a float of the same value (``1.0`` for ``1``), digest recomputed (equal in Python, not an integer)."""
    rs, i = _one(c)
    rs[i]["sequence"] = float(rs[i]["sequence"])
    redigest(rs[i])
    put(c, rs)


@hop("H3", "sequence-as-boolean", (C_SHAPE, C_CHAIN))
def h3_seq_bool(c: Ctx) -> None:
    """``sequence`` 0 or 1 written as ``false`` or ``true``, digest recomputed (a Python bool compares equal to the integer)."""
    rs = wit(c)
    idx = [i for i, r in enumerate(rs) if r["sequence"] in (0, 1)]
    i = c.rng.choice(idx)
    rs[i]["sequence"] = bool(rs[i]["sequence"])
    redigest(rs[i])
    put(c, rs)


def _entry(c: Ctx, rs: list[dict[str, Any]], i: int) -> dict[str, Any]:
    names = sorted(rs[i]["ledgers"])
    if not names:
        raise NotApplicable("record covers no ledger")
    return rs[i]["ledgers"][c.rng.choice(names)]


@hop("H3", "count-as-string", (C_SHAPE,))
def h3_count_str(c: Ctx) -> None:
    """A ledger entry's ``count`` written as a string, digest recomputed."""
    rs, i = _one(c)
    e = _entry(c, rs, i)
    e["count"] = str(e["count"])
    redigest(rs[i])
    put(c, rs)


@hop("H3", "count-as-float", (C_SHAPE,))
def h3_count_float(c: Ctx) -> None:
    """A ledger entry's ``count`` written as a float of the same value, digest recomputed."""
    rs, i = _one(c)
    e = _entry(c, rs, i)
    e["count"] = float(e["count"])
    redigest(rs[i])
    put(c, rs)


@hop("H3", "count-as-boolean", (C_SHAPE,))
def h3_count_bool(c: Ctx) -> None:
    """A ledger entry whose ``count`` is 1 written as ``true``, digest recomputed (``True == 1`` in Python)."""
    rs = wit(c)
    spots = [(i, n) for i, r in enumerate(rs) for n in sorted(r["ledgers"]) if r["ledgers"][n]["count"] == 1]
    if not spots:
        raise NotApplicable("no ledger entry with count 1")
    i, n = c.rng.choice(spots)
    rs[i]["ledgers"][n]["count"] = True
    redigest(rs[i])
    put(c, rs)


@hop("H3", "count-negative", (C_SHAPE, C_CHAIN))
def h3_count_neg(c: Ctx) -> None:
    """A ledger entry's ``count`` made negative, digest recomputed."""
    rs, i = _one(c)
    e = _entry(c, rs, i)
    e["count"] = -e["count"]
    redigest(rs[i])
    put(c, rs)


@hop("H3", "head-not-a-digest", (C_SHAPE, C_HEAD))
def h3_head_upper(c: Ctx) -> None:
    """A held head written in upper-case hex or without the ``sha256:`` prefix (not the digest form), digest recomputed."""
    rs, i = _one(c)
    e = _entry(c, rs, i)
    e["head"] = c.rng.choice((e["head"].upper(), e["head"][7:], "sha1:" + e["head"][7:47]))
    redigest(rs[i])
    put(c, rs)


@hop("H3", "ledgers-as-list", (C_SHAPE,))
def h3_ledgers_list(c: Ctx) -> None:
    """``ledgers`` written as a list of ``{name, count, head}`` objects instead of an object, digest recomputed."""
    rs, i = _one(c)
    rs[i]["ledgers"] = [{"name": n, **v} for n, v in sorted(rs[i]["ledgers"].items())]
    redigest(rs[i])
    put(c, rs)


@hop("H3", "ledger-entry-extra-member", (C_SHAPE,))
def h3_entry_extra(c: Ctx) -> None:
    """An extra member (``algorithm`` or ``rows``) in a ledger entry, digest recomputed."""
    rs, i = _one(c)
    e = _entry(c, rs, i)
    e[c.rng.choice(("algorithm", "rows"))] = "sha256-chain"
    redigest(rs[i])
    put(c, rs)


@hop("H3", "ledger-entry-member-missing", (C_SHAPE,))
def h3_entry_missing(c: Ctx) -> None:
    """``count`` or ``head`` removed from a ledger entry, digest recomputed."""
    rs, i = _one(c)
    e = _entry(c, rs, i)
    del e[c.rng.choice(("count", "head"))]
    redigest(rs[i])
    put(c, rs)


@hop("H3", "extension-key-without-x", (C_SHAPE, "invalid_extension_key"))
def h3_ext(c: Ctx) -> None:
    """An ``extensions`` object whose key has no ``x-`` prefix added to a record, digest recomputed."""
    rs, i = _one(c)
    rs[i]["extensions"] = {c.rng.choice(("note", "publisher", "location")): "hub"}
    redigest(rs[i])
    put(c, rs)


@hop("H3", "line-is-an-array", (C_SHAPE,))
def h3_array(c: Ctx) -> None:
    """One witness line written as a one-element JSON array holding the record."""
    rs, i = _one(c)
    rs[i] = [rs[i]]
    put(c, rs)


@hop("H3", "record-split-across-lines", (C_SHAPE, "wire_syntax", "wire_trailing_data"))
def h3_pretty(c: Ctx) -> None:
    """One record pretty-printed over several lines (the file is no longer one record per line)."""
    rs, i = _one(c)
    lines = [json.dumps(r, sort_keys=True, separators=(",", ":")) for r in rs]
    lines[i] = json.dumps(rs[i], sort_keys=True, indent=1)
    put_text(c, lines)


@hop("H3", "wire-duplicate-member", ("wire_duplicate_member",))
def h3_dup_member(c: Ctx) -> None:
    """A second ``run_id`` (or ``ledgers``) member written before the real one in a witness line, so a last-wins reader sees the clean record."""
    rs, i = _one(c)
    key = c.rng.choice(("run_id", "ledgers"))
    other: Any = "run-" + _rand_digest(c)[7:15] if key == "run_id" else {}
    pairs = []
    for k in sorted(rs[i]):
        if k == key:
            pairs.append((k, other))
        pairs.append((k, rs[i][k]))
    lines = [json.dumps(r, sort_keys=True, separators=(",", ":")) for r in rs]
    lines[i] = dumps(Pairs(pairs), indent=None)
    put_text(c, lines)


@hop("H3", "wire-nonfinite-count", ("wire_nonfinite_constant",))
def h3_nan(c: Ctx) -> None:
    """A ledger entry's ``count`` written as ``NaN`` or ``Infinity``."""
    rs, i = _one(c)
    names = sorted(rs[i]["ledgers"])
    if not names:
        raise NotApplicable("record covers no ledger")
    rs[i]["ledgers"][c.rng.choice(names)]["count"] = Raw(c.rng.choice(("NaN", "Infinity")))
    lines = [json.dumps(r, sort_keys=True, separators=(",", ":")) for r in rs]
    lines[i] = dumps(rs[i], indent=None)
    put_text(c, lines)


@hop("H3", "wire-byte-order-mark", ("wire_bom",))
def h3_bom(c: Ctx) -> None:
    """A UTF-8 byte-order mark in front of the witness file."""
    c.raw["witness"] = b"\xef\xbb\xbf" + c.trace.files["witness"]


@hop("H3", "wire-trailing-data-on-line", ("wire_trailing_data",))
def h3_trailing(c: Ctx) -> None:
    """A second JSON value after the record on one witness line."""
    rs, i = _one(c)
    lines = [json.dumps(r, sort_keys=True, separators=(",", ":")) for r in rs]
    lines[i] += c.rng.choice((" {}", " 0", " []"))
    put_text(c, lines)


@hop("H3", "wire-invalid-utf8", ("wire_not_utf8", "wire_syntax"))
def h3_utf8(c: Ctx) -> None:
    """An invalid UTF-8 byte inside the run id string of one witness line."""
    rs, i = _one(c)
    lines = [json.dumps(r, sort_keys=True, separators=(",", ":")).encode("utf-8") for r in rs]
    lines[i] = lines[i].replace(b'"run_id":"', b'"run_id":"\xff', 1)
    c.raw["witness"] = b"".join(x + b"\n" for x in lines)


@hop("H3", "wire-lone-surrogate", ("wire_lone_surrogate",))
def h3_surrogate(c: Ctx) -> None:
    """A lone UTF-16 surrogate escape appended to the run id string of one witness line."""
    rs, i = _one(c)
    lines = [json.dumps(r, sort_keys=True, separators=(",", ":")) for r in rs]
    lines[i] = lines[i].replace('"run_id":"', '"run_id":"\\ud800', 1)
    put_text(c, lines)


# ============================================================================ H4: ledger shrink against a witness (expected reject)

def _drop_row(c: Ctx, where: str) -> tuple[str, int]:
    rs = wit(c)
    doc = rec(c)
    name = _ledger_with(c, rs, 1)
    rows = doc[name]
    if len(rows) > rs[-1]["ledgers"][name]["count"]:
        raise NotApplicable("the ledger has unwitnessed rows; a drop would not fall below the witnessed count")
    i = {"tail": len(rows) - 1, "head": 0, "middle": c.rng.randrange(len(rows))}[where]
    del rows[i]
    return name, i


@hop("H4", "covered-row-dropped-tail", (C_SHRUNK,))
def h4_tail(c: Ctx) -> None:
    """The last row of a fully covered run-record ledger removed; the witness unchanged."""
    _drop_row(c, "tail")


@hop("H4", "covered-row-dropped-first", (C_SHRUNK,))
def h4_first(c: Ctx) -> None:
    """The first row of a fully covered run-record ledger removed; the witness unchanged."""
    _drop_row(c, "head")


@hop("H4", "covered-row-dropped-any", (C_SHRUNK,))
def h4_any(c: Ctx) -> None:
    """A random row of a fully covered run-record ledger removed; the witness unchanged."""
    _drop_row(c, "middle")


@hop("H4", "ledger-emptied", (C_SHRUNK,))
def h4_emptied(c: Ctx) -> None:
    """A covered ledger emptied (``[]``); the witness unchanged."""
    rs = wit(c)
    rec(c)[c.rng.choice(covered(c, rs))] = []


@hop("H4", "ledger-removed", (C_SHRUNK,))
def h4_removed(c: Ctx) -> None:
    """A covered ledger member removed from the record; the witness unchanged."""
    rs = wit(c)
    del rec(c)[c.rng.choice(covered(c, rs))]


@hop("H4", "witness-count-raised", (C_SHRUNK,))
def h4_count_up(c: Ctx) -> None:
    """The latest record's count for a ledger raised by one (head kept), digest recomputed: the record now holds fewer rows than witnessed."""
    rs = wit(c)
    name = c.rng.choice(covered(c, rs))
    rs[-1]["ledgers"][name]["count"] += 1
    redigest(rs[-1])
    put(c, rs)


@hop("H4", "record-rolled-back", (C_SHRUNK,), ("run_record", "destination_ledger", "witness"))
def h4_rollback(c: Ctx) -> None:
    """The record and the destination ledger replaced by their own earlier snapshot (taken at the first publication, a valid state of the
    same run), the full witness unchanged: a newer witness against an older record."""
    if "earlier_run_record" not in c.trace.extra:
        raise NotApplicable("no earlier snapshot (single publication)")
    c.raw["run_record"] = c.trace.extra["earlier_run_record"]
    c.raw["destination_ledger"] = c.trace.extra["earlier_destination_ledger"]


@hop("H4", "shrunk-then-republished", (C_SHRUNK, C_CHAIN))
def h4_launder(c: Ctx) -> None:
    """A covered row dropped and a new witness record made over the shrunk record appended, correctly linked (what ``publish_head`` refuses
    to do: laundering the drop into a fresh digest)."""
    name, _ = _drop_row(c, c.rng.choice(("tail", "head")))
    rs = wit(c)
    new = make_record(rec(c), rs[-1]["run_id"])
    put(c, rechain(rs + [new]))


@hop("H4", "shrunk-latest-record-rewritten", (C_SHRUNK, C_HEAD, C_CHAIN))
def h4_rewrite_tail(c: Ctx) -> None:
    """A row covered by an earlier record dropped and the witness's latest record re-made over the shrunk record (linked to the previous
    one): the earlier digest still covers the dropped row."""
    rs = wit(c)
    need_records(rs, 2)
    doc = rec(c)
    names = [n for n, e in sorted(rs[-2]["ledgers"].items()) if e["count"] >= 1 and n in doc]
    if not names:
        raise NotApplicable("the earlier record covers no ledger")
    name = c.rng.choice(names)
    del doc[name][0]
    rs[-1] = make_record(doc, rs[-1]["run_id"])
    put(c, rechain(rs))


@hop("H4", "destination-row-dropped-uncorroborated", (C_SHRUNK, "observation_without_ledger_row", "acknowledged_attempt_without_ledger_row"),
     ("run_record", "destination_ledger", "witness"))
def h4_destination(c: Ctx) -> None:
    """The destination ledger row of an effect nothing in the record corroborates (unknown attempt, no accepted applied or partial
    observation: the R6 shape) dropped in a witnessed trace. The design says: "with a witness the same drop is H4". The witness profile
    covers the run record's list-valued members only; the destination snapshot is a different file."""
    if not c.has("destination_ledger"):
        raise NotApplicable("no destination ledger")
    wit(c)
    _drop_row_of_uncertain(c, corroborated=False)  # the same precondition and drop as the unwitnessed R6 operator
    c.touched.discard("run_record")


# ============================================================================ H5: ledger rewrite or reorder against a witness (expected reject)

@hop("H5", "covered-rows-swapped", (C_HEAD,))
def h5_swap(c: Ctx) -> None:
    """Two distinct covered rows of one ledger swapped (count unchanged); the witness unchanged."""
    rs = wit(c)
    name = _ledger_with(c, rs, 2)
    rows = rec(c)[name]
    n = rs[-1]["ledgers"][name]["count"]
    i, j = _differing_pair(rows[:n], c)
    rows[i], rows[j] = rows[j], rows[i]


@hop("H5", "covered-row-string-rewritten", (C_HEAD,))
def h5_rewrite(c: Ctx) -> None:
    """One string value inside a covered row changed (a character appended); the witness unchanged."""
    rs = wit(c)
    name = _ledger_with(c, rs, 1)
    rows = rec(c)[name]
    i = c.rng.randrange(rs[-1]["ledgers"][name]["count"])
    paths = _string_paths(rows[i])
    if not paths:
        raise NotApplicable("row holds no string")
    path = c.rng.choice(paths)
    _set(rows[i], path, _get(rows[i], path) + c.rng.choice(("x", "0", " ")))


@hop("H5", "covered-row-extension-added", (C_HEAD,))
def h5_ext(c: Ctx) -> None:
    """An ``extensions`` member with one ``x-`` name added to a covered row (where the record's contracts admit extensions this is the
    one change only the witness can see); the witness unchanged."""
    rs = wit(c)
    name = _ledger_with(c, rs, 1)
    rows = rec(c)[name]
    row = rows[c.rng.randrange(rs[-1]["ledgers"][name]["count"])]
    if not isinstance(row, dict):
        raise NotApplicable("row is not an object")
    row.setdefault("extensions", {})["x-annotation"] = "edited after publication"


@hop("H5", "covered-row-replaced-by-copy", (C_HEAD,))
def h5_copy(c: Ctx) -> None:
    """A covered row replaced by a copy of another row of the same ledger (count unchanged); the witness unchanged."""
    rs = wit(c)
    name = _ledger_with(c, rs, 2)
    rows = rec(c)[name]
    i, j = _differing_pair(rows[: rs[-1]["ledgers"][name]["count"]], c)
    rows[i] = copy.deepcopy(rows[j])


@hop("H5", "covered-row-dropped-and-padded", (C_HEAD,))
def h5_pad(c: Ctx) -> None:
    """A covered row dropped and a copy of the last row appended so the count holds; the witness unchanged."""
    rs = wit(c)
    name = _ledger_with(c, rs, 2)
    rows = rec(c)[name]
    n = rs[-1]["ledgers"][name]["count"]
    i = c.rng.randrange(n - 1)
    del rows[i]
    rows.append(copy.deepcopy(rows[-1]))


@hop("H5", "covered-row-amount-integer-form", (C_HEAD,))
def h5_int(c: Ctx) -> None:
    """A whole-number float ``amount`` in a covered row written as an integer (a different canonical number); the witness unchanged."""
    rs = wit(c)
    doc = rec(c)
    spots = []
    for name in covered(c, rs):
        for i, row in enumerate(doc.get(name, [])[: rs[-1]["ledgers"][name]["count"]]):
            for path in _all_paths(row):
                if path and path[-1] == "amount" and isinstance(_get(row, path), float) and float(_get(row, path)).is_integer():
                    spots.append((name, i, path))
    if not spots:
        raise NotApplicable("no whole float amount in a covered row")
    name, i, path = c.rng.choice(spots)
    _set(doc[name][i], path, Raw(str(int(_get(doc[name][i], path)))))


def _all_paths(value: Any, path: tuple = ()) -> list[tuple]:
    out = [path]
    if isinstance(value, dict):
        for k in sorted(value):
            out += _all_paths(value[k], path + (k,))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            out += _all_paths(v, path + (i,))
    return out


@hop("H5", "witness-head-replaced", (C_HEAD,))
def h5_witness_head(c: Ctx) -> None:
    """A held head replaced by another digest and the record's digest recomputed (a consistent witness holding a wrong head)."""
    rs = wit(c)
    i = c.rng.randrange(len(rs))
    names = sorted(rs[i]["ledgers"])
    if not names:
        raise NotApplicable("record covers no ledger")
    rs[i]["ledgers"][c.rng.choice(names)]["head"] = _rand_digest(c)
    put(c, rechain(rs))


@hop("H5", "witness-count-lowered-head-kept", (C_HEAD,))
def h5_count_down(c: Ctx) -> None:
    """The latest record's count for a ledger lowered by one with the head kept, digest recomputed (the head no longer covers that prefix)."""
    rs = wit(c)
    prev = rs[-2]["ledgers"] if len(rs) > 1 else {}
    names = [n for n in covered(c, rs, 2) if prev.get(n, {}).get("count", 0) <= rs[-1]["ledgers"][n]["count"] - 1]
    if not names:
        raise NotApplicable("no ledger whose count can be lowered without a chain defect")
    rs[-1]["ledgers"][c.rng.choice(names)]["count"] -= 1
    redigest(rs[-1])
    put(c, rs)


# ============================================================================ H6: holder-inventory damage (expected reject)

INV_CODES = (C_INV, "undeclared_member", "unknown_enum_value", "timestamp_invalid", "unsupported_contract_version", "invalid_extension_key")


def inv(c: Ctx) -> dict[str, Any]:
    if not c.has("holder_inventory"):
        raise NotApplicable("no holder inventory in the trace")
    return c.doc("holder_inventory")


def _holder(c: Ctx) -> dict[str, Any]:
    hs = inv(c).get("holders") or []
    if not hs:
        raise NotApplicable("inventory enumerates no holder")
    return c.rng.choice(hs)


@hop("H6", "kind-lifecycle-value", ("unknown_enum_value", C_INV), ("holder_inventory",))
def h6_kind(c: Ctx) -> None:
    """A holder's ``kind`` set to a lifecycle word (``expired``, ``revoked`` or ``lapsed``) the closed set does not have."""
    _holder(c)["kind"] = c.rng.choice(("expired", "revoked", "lapsed"))


@hop("H6", "kind-case-changed", ("unknown_enum_value", C_INV), ("holder_inventory",))
def h6_kind_case(c: Ctx) -> None:
    """A holder's ``kind`` capitalised (``Routed``)."""
    h = _holder(c)
    h["kind"] = h["kind"].capitalize()


@hop("H6", "kind-missing", (C_INV,), ("holder_inventory",))
def h6_kind_missing(c: Ctx) -> None:
    """A holder's ``kind`` removed."""
    del _holder(c)["kind"]


@hop("H6", "holders-missing", (C_INV,), ("holder_inventory",))
def h6_holders_missing(c: Ctx) -> None:
    """The ``holders`` member removed from the inventory."""
    del inv(c)["holders"]


@hop("H6", "holders-as-object", (C_INV,), ("holder_inventory",))
def h6_holders_obj(c: Ctx) -> None:
    """``holders`` written as an object keyed by holder id instead of a list."""
    d = inv(c)
    d["holders"] = {h["holder_id"]: h for h in d.get("holders") or []} or {"h": {}}


@hop("H6", "version-other-profile", ("unsupported_contract_version", C_INV), ("holder_inventory",))
def h6_version(c: Ctx) -> None:
    """``version`` set to another profile (``witness-digest/0.1``) or a next minor (``holder-inventory/0.2``)."""
    inv(c)["version"] = c.rng.choice(("witness-digest/0.1", "holder-inventory/0.2"))


@hop("H6", "version-not-a-string", (C_INV,), ("holder_inventory",))
def h6_version_num(c: Ctx) -> None:
    """``version`` written as the number ``0.1``."""
    inv(c)["version"] = 0.1


@hop("H6", "inventory-member-undeclared", ("undeclared_member", C_INV), ("holder_inventory",))
def h6_inv_member(c: Ctx) -> None:
    """An undeclared member (``signature``, ``complete`` or ``covers_classes``) added to the inventory."""
    inv(c)[c.rng.choice(("signature", "complete", "covers_classes"))] = c.rng.choice((True, "sig", ["c"]))


@hop("H6", "holder-member-undeclared", ("undeclared_member", C_INV), ("holder_inventory",))
def h6_holder_member(c: Ctx) -> None:
    """An undeclared member (``revoked_at``, ``secret`` or ``state``) added to a holder."""
    _holder(c)[c.rng.choice(("revoked_at", "secret", "state"))] = "2026-10-05T19:00:00Z"


@hop("H6", "recorded-at-without-offset", ("timestamp_invalid", C_INV), ("holder_inventory",))
def h6_naive(c: Ctx) -> None:
    """``recorded_at`` without its UTC offset (a naive time) or as a bare date."""
    d = inv(c)
    t = d["recorded_at"]
    d["recorded_at"] = c.rng.choice((t[:19], t[:10]))


@hop("H6", "recorded-at-not-a-time", ("timestamp_invalid", C_INV), ("holder_inventory",))
def h6_not_time(c: Ctx) -> None:
    """``recorded_at`` a word, not a time."""
    inv(c)["recorded_at"] = c.rng.choice(("yesterday", "unknown"))


@hop("H6", "string-member-emptied", (C_INV,), ("holder_inventory",))
def h6_empty(c: Ctx) -> None:
    """``inventory_id``, ``recorded_by`` or a holder's ``enforcement_point`` / ``holder_id`` set to the empty string."""
    which = c.rng.choice(("inventory_id", "recorded_by", "enforcement_point", "holder_id"))
    (inv(c) if which in ("inventory_id", "recorded_by") else _holder(c))[which] = ""


@hop("H6", "holder-id-too-long", (C_INV,), ("holder_inventory",))
def h6_long(c: Ctx) -> None:
    """A holder id of 257 characters (the limit is 256)."""
    _holder(c)["holder_id"] = "h" * 257


@hop("H6", "credential-ref-not-a-string", (C_INV,), ("holder_inventory",))
def h6_cred(c: Ctx) -> None:
    """A holder's ``credential_ref`` written as a number or an object."""
    _holder(c)["credential_ref"] = c.rng.choice((123, {"ref": "vault://x"}))


@hop("H6", "extension-key-without-x", ("invalid_extension_key", C_INV), ("holder_inventory",))
def h6_ext(c: Ctx) -> None:
    """An ``extensions`` object whose key has no ``x-`` prefix, on the inventory or on a holder."""
    target = c.rng.choice((inv(c), _holder(c)))
    target["extensions"] = {"note": "added"}


@hop("H6", "document-is-a-list", (C_INV,), ("holder_inventory",))
def h6_list(c: Ctx) -> None:
    """The inventory written as a one-element list holding the inventory object."""
    c.raw["holder_inventory"] = dump_file_bytes([inv(c)])


@hop("H6", "wire-duplicate-kind", ("wire_duplicate_member",), ("holder_inventory",))
def h6_dup(c: Ctx) -> None:
    """A second ``kind`` member (``expired``) written before the real one in a holder, so a last-wins reader sees the clean inventory."""
    d = inv(c)
    hs = d.get("holders") or []
    if not hs:
        raise NotApplicable("inventory enumerates no holder")
    i = c.rng.randrange(len(hs))
    pairs = []
    for k in hs[i]:
        if k == "kind":
            pairs.append(("kind", "expired"))
        pairs.append((k, hs[i][k]))
    hs[i] = Pairs(pairs)
    c.raw["holder_inventory"] = (dumps(d, indent=1) + "\n").encode("utf-8")


def _record_names_inventory(c: Ctx) -> None:
    """The precondition the brief's holder operators need: the run record names the inventory (its id appears anywhere in the record)."""
    inv_id = inv(c).get("inventory_id")
    text = c.trace.files["run_record"].decode("utf-8")
    if not inv_id or json.dumps(inv_id) not in text:
        raise NotApplicable("the record names no inventory (it does not retain the runtime-authority profile; holder-inventory non-claim)")


@hop("H6", "holder-duplicated-against-record-reference", (C_INV,), ("run_record", "holder_inventory"))
def h6_dup_holder(c: Ctx) -> None:
    """Where the record names the inventory: a holder duplicated in the supplied inventory (so it is not the inventory the record names)."""
    _record_names_inventory(c)
    hs = inv(c)["holders"]
    hs.append(copy.deepcopy(c.rng.choice(hs)))


@hop("H6", "holder-dropped-against-record-reference", (C_INV,), ("run_record", "holder_inventory"))
def h6_drop_holder(c: Ctx) -> None:
    """Where the record names the inventory: a holder removed from the supplied inventory."""
    _record_names_inventory(c)
    hs = inv(c)["holders"]
    del hs[c.rng.randrange(len(hs))]


@hop("H6", "holder-added-against-record-reference", (C_INV,), ("run_record", "holder_inventory"))
def h6_add_holder(c: Ctx) -> None:
    """Where the record names the inventory: an extra holder added to the supplied inventory."""
    _record_names_inventory(c)
    inv(c)["holders"].append({"holder_id": "h-extra", "kind": "routed", "enforcement_point": "unlisted gateway", "credential_ref": None})


# ============================================================================ H7: rows appended after the latest digest (control, expected abstain)

@hop("H7", "witness-tail-truncated", ())
def h7_tail(c: Ctx) -> None:
    """The latest witness record(s) removed so an older valid witness is replayed against the newer record: the remaining latest record
    covers fewer rows than the record holds (the rows appended since are unwitnessed, not damaged)."""
    rs = wit(c)
    need_records(rs, 2)
    doc = rec(c)
    keep = c.rng.randrange(1, len(rs))
    rs = rs[:keep]
    if all(rs[-1]["ledgers"].get(n, {}).get("count", 0) >= len(rows) for n, rows in ledgers(doc).items()):
        raise NotApplicable("the older record already covers every row")
    c.touched.discard("run_record")
    put(c, rs)


@hop("H7", "witness-remade-over-prefix", ())
def h7_prefix(c: Ctx) -> None:
    """The witness replaced by one record made over a prefix of one ledger (as if published before the later rows were appended); the record
    unchanged."""
    doc = rec(c)
    c.touched.discard("run_record")
    rs = wit(c)
    names = [n for n, rows in ledgers(doc).items() if len(rows) >= 2]
    if not names:
        raise NotApplicable("no ledger with two or more rows")
    name = c.rng.choice(names)
    counts = {n: len(rows) for n, rows in ledgers(doc).items()}
    counts[name] = c.rng.randrange(1, len(doc[name]))
    put(c, rechain([make_record(doc, rs[-1]["run_id"], counts)]))


@hop("H7", "witness-omits-a-ledger", ())
def h7_omit(c: Ctx) -> None:
    """Every witness record re-made without one ledger and the chain re-computed (consistent; that ledger's rows are not covered at all)."""
    rs = wit(c)
    name = c.rng.choice(covered(c, rs))
    for r in rs:
        r["ledgers"].pop(name, None)
    put(c, rechain(rs))


@hop("H7", "witness-count-lowered-head-recomputed", ())
def h7_count(c: Ctx) -> None:
    """The latest record's count for one ledger lowered by one with the head recomputed over the shorter prefix, digest recomputed
    (consistent: the last row is now unwitnessed)."""
    doc = rec(c)
    c.touched.discard("run_record")
    rs = wit(c)
    prev = rs[-2]["ledgers"] if len(rs) > 1 else {}
    names = [n for n in covered(c, rs, 2) if prev.get(n, {}).get("count", 0) <= rs[-1]["ledgers"][n]["count"] - 1]
    if not names:
        raise NotApplicable("no ledger whose count can be lowered without a chain defect")
    name = c.rng.choice(names)
    n = rs[-1]["ledgers"][name]["count"] - 1
    rs[-1]["ledgers"][name] = {"count": n, "head": head(doc[name][:n])}
    redigest(rs[-1])
    put(c, rs)


# ============================================================================ H8: witness holding no digest (control, expected abstain); witness file absent (input-error control, decision 30-A)

@hop("H8", "witness-empty-file", (), ("witness",))
def h8_empty(c: Ctx) -> None:
    """The witness file supplied empty (zero bytes)."""
    wit(c)
    c.raw["witness"] = b""


@hop("H8", "witness-blank-lines", (), ("witness",))
def h8_blank(c: Ctx) -> None:
    """The witness file holding only line ends (no record; the producer's reader skips blank lines)."""
    wit(c)
    c.raw["witness"] = c.rng.choice((b"\n", b"\n\n", b"\r\n"))


@hop("H8", "witness-file-absent", (), ("witness",), expected_outcome="input_error")
def h8_absent(c: Ctx) -> None:
    """``--witness`` names a path where no file exists: an input-error control (ODES decision 30-A), expected exit 2 and no report."""
    wit(c)
    c.raw["witness"] = ABSENT_FILE


# ============================================================================ B: benign controls in the witnessed population (expected accept)

def _reorder(value: Any, c: Ctx) -> Any:
    if isinstance(value, dict):
        keys = list(value)
        c.rng.shuffle(keys)
        return {k: _reorder(value[k], c) for k in keys}
    if isinstance(value, list):
        return [_reorder(v, c) for v in value]
    return value


@hop("B", "witness-keys-reordered", ())
def b_w_reorder(c: Ctx) -> None:
    """Each witness line's members written in a different order (compact); same records."""
    rs = wit(c)
    put_text(c, [json.dumps(_reorder(r, c), separators=(",", ":")) for r in rs])


@hop("B", "witness-spaced-separators", ())
def b_w_spaces(c: Ctx) -> None:
    """Each witness line written with a space after every ``:`` and ``,`` (still one record per line)."""
    put_text(c, [json.dumps(r, sort_keys=True) for r in wit(c)])


@hop("B", "witness-crlf", ())
def b_w_crlf(c: Ctx) -> None:
    """CRLF line ends in the witness file."""
    c.raw["witness"] = b"".join(json.dumps(r, sort_keys=True, separators=(",", ":")).encode() + b"\r\n" for r in wit(c))


@hop("B", "witness-no-final-newline", ())
def b_w_nonl(c: Ctx) -> None:
    """The witness file without its final line end."""
    c.raw["witness"] = c.trace.files["witness"].rstrip(b"\n")


@hop("B", "witness-blank-line-between-records", ())
def b_w_blank(c: Ctx) -> None:
    """An empty line before or between witness records (the producer's reader skips blank lines)."""
    rs = wit(c)
    lines = [json.dumps(r, sort_keys=True, separators=(",", ":")) for r in rs]
    lines.insert(c.rng.randrange(len(lines) + 1) if len(lines) > 1 else 0, "")
    put_text(c, lines)


@hop("B", "witness-escaped-ascii", ())
def b_w_escape(c: Ctx) -> None:
    """Letters of the run id written as ``\\u00XX`` escapes (the same string)."""
    rs = wit(c)
    lines = []
    for r in rs:
        line = json.dumps(r, sort_keys=True, separators=(",", ":"))
        rid = json.dumps(r["run_id"])
        esc = '"' + "".join("\\u%04x" % ord(ch) if ch.isalpha() else ch for ch in r["run_id"]) + '"'
        lines.append(line.replace('"run_id":' + rid, '"run_id":' + esc, 1))
    put_text(c, lines)


@hop("B", "witness-republished-unchanged", ())
def b_w_republish(c: Ctx) -> None:
    """A further record over the unchanged record appended, correctly chained (a re-publication with nothing new: a valid witness)."""
    rs = wit(c)
    doc = rec(c)
    c.touched.discard("run_record")
    put(c, rechain(rs + [make_record(doc, rs[-1]["run_id"])]))


@hop("B", "record-keys-reordered", (), ("run_record",))
def b_r_reorder(c: Ctx) -> None:
    """Every object's members in the run record written in a different order (the heads are over canonical rows, so unchanged)."""
    doc = rec(c)
    c.raw["run_record"] = dump_file_bytes(_reorder(doc, c))


@hop("B", "record-compact-whitespace", (), ("run_record",))
def b_r_compact(c: Ctx) -> None:
    """All insignificant whitespace removed from the run record."""
    c.raw["run_record"] = dumps(rec(c), indent=None).encode("utf-8")


@hop("B", "covered-row-float-spelling", (), ("run_record",))
def b_r_float(c: Ctx) -> None:
    """A whole float ``amount`` in a covered row written as ``50.00``, ``5e1`` or ``50.0e0`` (one float, one canonical form: the head is unchanged)."""
    rs = wit(c)
    doc = rec(c)
    spots = []
    for name in covered(c, rs):
        for i, row in enumerate(doc.get(name, [])):
            for path in _all_paths(row):
                if path and path[-1] == "amount" and isinstance(_get(row, path), float) and float(_get(row, path)).is_integer() and int(_get(row, path)) % 10 == 0:
                    spots.append((name, i, path))
    if not spots:
        raise NotApplicable("no whole float amount (multiple of ten) in a covered row")
    name, i, path = c.rng.choice(spots)
    whole = int(_get(doc[name][i], path))
    _set(doc[name][i], path, Raw(c.rng.choice((f"{whole}.00", f"{whole // 10}e1", f"{whole}.0e0"))))


@hop("B", "inventory-keys-reordered", (), ("holder_inventory",))
def b_i_reorder(c: Ctx) -> None:
    """The holder inventory's members written in a different order."""
    c.raw["holder_inventory"] = dump_file_bytes(_reorder(inv(c), c))


@hop("B", "inventory-repeated-holder-id", (), ("holder_inventory",))
def b_i_repeat(c: Ctx) -> None:
    """A second holder with the id of an enumerated holder (kind ``other``). The profile defines no uniqueness rule; the ODES draft pins this
    as valid (``repeated-holder-id-is-not-refused``). Contract-valid, not value-equal: an accept is the contract's expectation."""
    hs = inv(c).get("holders") or []
    if not hs:
        raise NotApplicable("inventory enumerates no holder")
    h = c.rng.choice(hs)
    hs.append({"holder_id": h["holder_id"], "kind": "other", "enforcement_point": "second listing", "credential_ref": None})


# ============================================================================ F: forgery bound in the witnessed population (expected accept)

@hop("F", "reseal-amount-and-rewitness", (), ("run_record", "proposal_export", "destination_ledger", "witness"))
def f_rewitness(c: Ctx) -> None:
    """The catalogue's self-consistent reseal (proposal amount changed, every dependent commitment recomputed) and the witness re-made over
    the resealed record with the same publication structure (each record's counts kept, heads and digests recomputed): the record and the
    witness rewritten together so that they agree."""
    rs = wit(c)
    f_reseal(c)
    doc = json.loads(c.raw["run_record"].decode("utf-8"))
    for r in rs:
        r["ledgers"] = head_digest(doc, {n: e["count"] for n, e in r["ledgers"].items()})
    put(c, rechain(rs))


@hop("F", "witness-history-collapsed", ())
def f_collapse(c: Ctx) -> None:
    """A multi-record witness replaced by one fresh record over the current record (the witness's holder rewrote its history)."""
    rs = wit(c)
    need_records(rs, 2)
    doc = rec(c)
    c.touched.discard("run_record")
    put(c, rechain([make_record(doc, rs[-1]["run_id"])]))


@hop("F", "witness-history-extended", ())
def f_extend(c: Ctx) -> None:
    """A fabricated intermediate publication inserted before the latest record: its counts lie between the previous record's and the
    latest's, its heads are right for those prefixes, and the chain is re-computed (the witness's holder added history that never happened)."""
    rs = wit(c)
    doc = rec(c)
    c.touched.discard("run_record")
    prev = rs[-2]["ledgers"] if len(rs) > 1 else {}
    counts = {}
    for name, e in sorted(rs[-1]["ledgers"].items()):
        low = max(1, prev.get(name, {}).get("count", 1))
        counts[name] = c.rng.randint(min(low, e["count"]), e["count"])
    put(c, rechain(rs[:-1] + [make_record(doc, rs[-1]["run_id"], counts), rs[-1]]))


def witness_categories() -> list[str]:
    return sorted({o.category for o in WITNESS_OPERATORS})


assert all(r in ROLES for o in WITNESS_OPERATORS for r in o.roles)
