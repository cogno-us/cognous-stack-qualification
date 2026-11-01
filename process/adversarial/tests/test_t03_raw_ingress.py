"""T03. Raw-ingress canonicalization differential at `acp run` (ideas A06, A01, A07, tier 2).

SPDX-License-Identifier: Apache-2.0

Attacker: the author of the proposal JSON file given to `acp run` (control plane CLI, real BoundedAuthorizationWorkflow and
LocalRefundDestination; inputs are the control plane's own declared example under examples/acp_run).
Invariant: what was approved is what the destination receives. Duplicate members, NaN/Infinity, a BOM, trailing data and
non-UTF-8 bytes are refused (exit 2); number spellings (50, 50.0, 5e1) and Unicode forms either refuse or normalise
identically on both sides: the decision binding's commitments equal the commitments of the effect the destination stored.
Observed state: store/destination.json and out/bounded-run-record.json read back from disk after the run.

Does not prove: other ingress formats; the library API (T04 covers post-approval mutation there); files other than the
proposal (manifest, authority context and resolver state go through the same strict reader but are not perturbed here).
"""
from __future__ import annotations

import io
import json
import shutil
import unicodedata
from contextlib import redirect_stderr, redirect_stdout

import pytest

from conftest import observe

T = "T03"
DNP = "proposal file only; other ingress formats and the library API are separate"
NOW = "2026-10-05T19:00:00Z"


def _run(cp, tmp_path, proposal_bytes: bytes, *, approve_text: str | None = None):
    from agent_control_plane.bounded import RuntimeProposal, commitment
    from agent_control_plane.cli import main
    ex = cp / "examples" / "acp_run"
    inputs = tmp_path / "inputs"
    inputs.mkdir(parents=True)
    shutil.copy(ex / "manifest.json", inputs / "manifest.json")
    for name in ("authority-context", "resolver-state"):
        shutil.copy(ex / "authorized" / f"{name}.json", inputs / f"{name}.json")
    if approve_text is not None:  # the approver approved exactly this proposal text (the attacker controls both files here)
        state = json.loads((inputs / "resolver-state.json").read_text(encoding="utf-8"))
        approved = RuntimeProposal.model_validate(json.loads(approve_text))
        for approval in state["approvals"].values():
            approval["proposal_commitment"] = commitment(approved.model_dump(mode="json", exclude_none=False))
        (inputs / "resolver-state.json").write_text(json.dumps(state), encoding="utf-8")
    (inputs / "proposal.json").write_bytes(proposal_bytes)
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(["run", "--manifest", str(inputs / "manifest.json"), "--proposal", str(inputs / "proposal.json"),
                     "--authority-context", str(inputs / "authority-context.json"),
                     "--resolver-state", str(inputs / "resolver-state.json"), "--store-dir", str(tmp_path / "store"),
                     "--out-dir", str(tmp_path / "out"), "--now", NOW])
    effects = {}
    dest = tmp_path / "store" / "destination.json"
    if dest.exists():
        effects = json.loads(dest.read_text(encoding="utf-8"))["effects"]
    binding = None
    rec = tmp_path / "out" / "bounded-run-record.json"
    if rec.exists():
        decisions = json.loads(rec.read_text(encoding="utf-8"))["decisions"]
        binding = decisions[0]["binding"] if decisions else None
    return code, effects, binding, err.getvalue()


def _base(cp) -> str:
    return (cp / "examples" / "acp_run" / "authorized" / "proposal.json").read_text(encoding="utf-8")


def _assert_effect_matches_binding(effects, binding):
    from agent_control_plane.bounded import commitment
    [effect] = effects.values()
    assert commitment(effect["payload"]) == binding["payload_commitment"]
    assert (effect["target"], float(effect["amount"]), effect["unit"]) == (binding["target"], float(binding["amount"]), binding["unit"])


def test_positive_control_unperturbed_file_executes_once(tmp_path):
    from conftest import require
    cp = require("control_plane")["control_plane"]
    code, effects, binding, _ = _run(cp, tmp_path, _base(cp).encode())
    assert code == 0 and len(effects) == 1
    _assert_effect_matches_binding(effects, binding)


REFUSED = {
    "duplicate_member": lambda t: t.replace('"refund_reason": "duplicate"', '"refund_reason": "duplicate", "refund_reason": "x"').encode(),
    "duplicate_top_level_target": lambda t: t.replace('"unit": "USD",', '"unit": "USD", "target": "urn:cognous:synthetic-account:attacker",').encode(),
    "nan_amount": lambda t: t.replace('"amount": 50.0', '"amount": NaN').encode(),
    "infinity_amount": lambda t: t.replace('"amount": 50.0', '"amount": Infinity').encode(),
    "bom": lambda t: b"\xef\xbb\xbf" + t.encode(),
    "trailing_data": lambda t: (t + "\n{}").encode(),
    "not_utf8": lambda t: t.replace("duplicate", "dupl\udcffcate").encode("utf-8", "surrogateescape"),
    "unknown_member": lambda t: t.replace('"unit": "USD",', '"unit": "USD", "x_target_override": "attacker",').encode(),
}


@pytest.mark.parametrize("case", sorted(REFUSED))
def test_malformed_ingress_is_refused_without_effect(tmp_path, case):
    from conftest import require
    cp = require("control_plane")["control_plane"]
    code, effects, _, err = _run(cp, tmp_path, REFUSED[case](_base(cp)))
    assert code == 2, (case, code, err)
    assert effects == {}
    assert "attacker" not in err  # untrusted member values are not echoed
    observe(T, f"refused ingress: {case}", "prevented", does_not_prove=DNP)


SPELLINGS = {
    "amount_int": lambda t: t.replace('"amount": 50.0', '"amount": 50'),
    "amount_exponent": lambda t: t.replace('"amount": 50.0', '"amount": 5e1'),
    "amount_trailing_zero": lambda t: t.replace('"amount": 50.0', '"amount": 50.000'),
}


@pytest.mark.parametrize("case", sorted(SPELLINGS))
def test_number_spellings_normalise_identically(tmp_path, case):
    """The approval was made over the original file; an equivalent number spelling must not change what lands."""
    from conftest import require
    cp = require("control_plane")["control_plane"]
    code, effects, binding, err = _run(cp, tmp_path, SPELLINGS[case](_base(cp)).encode())
    assert code == 0, (case, err)
    _assert_effect_matches_binding(effects, binding)
    observe(T, f"number spelling: {case}", "prevented", does_not_prove=DNP, detail="same commitment both sides")


@pytest.mark.parametrize("form", ["NFC", "NFD"])
def test_unicode_form_reaches_destination_unchanged(tmp_path, form):
    """A payload in either Unicode form, approved as written, lands exactly as approved (no silent normalisation on one side)."""
    from conftest import require
    from agent_control_plane.bounded import commitment
    cp = require("control_plane")["control_plane"]
    doc = json.loads(_base(cp))
    doc["payload"]["refund_reason"] = unicodedata.normalize(form, "dupliçate")
    doc["payload_commitment"] = commitment(doc["payload"])
    text = json.dumps(doc, ensure_ascii=False)
    code, effects, binding, err = _run(cp, tmp_path, text.encode(), approve_text=text)
    assert code == 0, err
    _assert_effect_matches_binding(effects, binding)
    [effect] = effects.values()
    assert effect["payload"]["refund_reason"] == doc["payload"]["refund_reason"]
    other = unicodedata.normalize("NFD" if form == "NFC" else "NFC", doc["payload"]["refund_reason"])
    assert effect["payload"]["refund_reason"] != other
    observe(T, f"unicode payload form {form}", "prevented", does_not_prove=DNP, detail="stored exactly as approved")


def test_unicode_form_swap_after_approval_is_held(tmp_path):
    """Approved in NFC, submitted in NFD: the commitments differ and nothing lands."""
    from conftest import require
    from agent_control_plane.bounded import commitment
    cp = require("control_plane")["control_plane"]
    doc = json.loads(_base(cp))
    doc["payload"]["refund_reason"] = unicodedata.normalize("NFC", "dupliçate")
    doc["payload_commitment"] = commitment(doc["payload"])
    approved = json.dumps(doc, ensure_ascii=False)
    doc["payload"]["refund_reason"] = unicodedata.normalize("NFD", doc["payload"]["refund_reason"])
    doc["payload_commitment"] = commitment(doc["payload"])
    code, effects, _, _ = _run(cp, tmp_path, json.dumps(doc, ensure_ascii=False).encode(), approve_text=approved)
    assert code == 1 and effects == {}
    observe(T, "unicode form swapped after approval", "prevented", does_not_prove=DNP)
