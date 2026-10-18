"""T16. Canary-secret sweep over every artifact (idea D31, tier 6).

SPDX-License-Identifier: Apache-2.0

Attacker: a reader of any produced file, log, exception text or downstream export.
Seeding: a canary secret (a) in the process environment as a credential, (b) in the text of a resolver failure (a credential-
bearing error from the authority source), (c) in the text of a destination failure (a provider error that echoes a token).
Paths: success, effect-time refusal, destination crash. Artifacts swept: every file under the run's work directory (control
plane record store, destination SQLite database and WAL as raw bytes), the executor result returned to the host (error and
evidence), the Replay bundle, the Evidence Pack, the ODES package and the verifier report built from the run.
Forms searched: plain, base64, hex and JSON-escaped (the canary carries a non-ASCII character so the escaped form differs).
Invariant: a credential canary appears in no artifact in any form. A payload canary (business data) is written where payload is
stored by design; it must not appear in diagnostic channels (failure detail, refusal reasons, stderr).

Does not prove: the live OpenShell subprocess environment (untested surface); encodings other than the four searched (for
example a canary split across a base64 boundary or compressed); artifacts produced by components outside the attacked set.
"""
from __future__ import annotations

import base64
import json
import os

import pytest

from _adv import bundle, downstream, flow, verify
from conftest import observe, require

T = "T16"
DNP = "OpenShell environment untested; only plain/base64/hex/JSON-escaped forms searched"
CANARY = "CANARY-7f3a9c-s3cr3t-é"


def forms(secret: str) -> dict[str, bytes]:
    raw = secret.encode("utf-8")
    return {"plain": raw, "base64": base64.b64encode(raw), "base64url": base64.urlsafe_b64encode(raw).rstrip(b"="),
            "hex": raw.hex().encode(), "json_escaped": json.dumps(secret).strip('"').encode()}


def sweep(blobs: dict[str, bytes], secret: str = CANARY) -> dict[str, list[str]]:
    hits = {}
    for name, data in blobs.items():
        found = [f for f, needle in forms(secret).items() if needle in data]
        if found:
            hits[name] = found
    return hits


def _files(root) -> dict[str, bytes]:
    out = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            out[str(path.relative_to(root))] = path.read_bytes()
    return out


def _run_path(tmp_path, mp, path):
    paths = require("verifier", "replay", "evidence_pack", "odes")
    fl = flow(tmp_path / "work", mp)
    mp.setenv("ADV_CANARY_CREDENTIAL", CANARY)
    if path == "refusal":
        def broken(ref):
            raise TimeoutError("authority source unavailable; token=" + CANARY)
        fl.r.grant_status = broken
    if path == "crash":
        def crash(snapshot, **kw):
            raise RuntimeError("provider rejected request with token=" + CANARY)
        fl.dest.commit = crash
    try:
        result = fl.run(fl.d1)
        returned = json.dumps({"status": result.status, "error": result.error, "evidence": result.control_plane_evidence,
                               "observation": result.observation}, default=str).encode()
    except Exception as exc:  # noqa: BLE001 - an exception text reaching the host is itself an artifact
        returned = repr(exc).encode()
    blobs = {"work/" + k: v for k, v in _files(tmp_path / "work").items()}
    blobs["executor-result"] = returned
    b = bundle(fl, tmp_path / "bundle")
    _, report = verify(paths["verifier"], b)
    blobs["verifier-report"] = json.dumps(report).encode()
    try:
        for name, f in downstream(fl, tmp_path / "downstream", paths).items():
            blobs[name] = f.read_bytes()
    except Exception as exc:  # noqa: BLE001 - a refused import is recorded, its message swept
        blobs["downstream-refusal"] = repr(exc).encode()
    return blobs


def test_positive_control_scanner_finds_planted_canary():
    planted = {"a": b"x" + forms(CANARY)["base64"] + b"y", "b": json.dumps({"k": CANARY}).encode(), "c": b"clean"}
    hits = sweep(planted)
    assert set(hits) == {"a", "b"} and "base64" in hits["a"] and "json_escaped" in hits["b"]


# Batch 1 recorded one failing path (crash) at the first attacked revisions; the runtime fix since then (destination exceptions are
# recorded by class name only) makes it pass, so it is now an ordinary assertion like the other two paths.
PATHS = ["success", "refusal", "crash"]


@pytest.mark.parametrize("path", PATHS)
def test_credential_canary_appears_in_no_artifact(cprt, tmp_path, monkeypatch, path):
    blobs = _run_path(tmp_path, monkeypatch, path)
    hits = sweep(blobs)
    observe(T, f"credential canary, {path} path", "prevented" if not hits else "reproduced failure", does_not_prove=DNP,
            detail={"artifacts_swept": len(blobs), "hits": hits})
    assert hits == {}, hits


def test_payload_canary_stays_out_of_diagnostic_channels(cprt, tmp_path, monkeypatch):
    """A canary inside the business payload is stored where payload is stored; it must not reach failure or refusal text."""
    fl = flow(tmp_path / "work", monkeypatch)
    p = fl.p.model_copy(deep=True)
    p.payload = {**p.payload, "refund_reason": "duplicate " + CANARY}  # a declared payload field
    p.payload_commitment = fl.cp.commitment(p.payload)
    ref = fl.r.contexts[fl.PROFILE]["grant"]["approval_refs"][0]
    fl.r.approvals[ref].proposal_commitment = fl.cp.commitment(p.model_dump(mode="json", exclude_none=False))
    fl.tra.bind_approval(fl.r, fl.f.runtime_authority_profile or fl.cfg)
    d = fl.f.decide(p, now=fl.NOW)
    assert d.result == "authorized", d.reasons
    fl.r.statuses[d.binding.grant_id].status = "revoked"  # refusal path: the payload is in the request, the refusal must not echo it
    r = fl.run(d, p)
    assert r.status == "denied"
    record = fl.f.records.load()
    diagnostic = {
        "executor-error": (r.error or "").encode(),
        "refusal-reasons": json.dumps([x.reasons for x in record.refusals]).encode(),
        "refusal-changed-inputs": json.dumps([[c.model_dump() for c in x.changed_inputs] for x in record.refusals]).encode(),
        "failure-detail": json.dumps([f["detail"] for f in fl.dest.failure_history()]).encode(),
    }
    hits = sweep(diagnostic)
    observe(T, "payload canary, refusal path, diagnostic channels", "prevented" if not hits else "reproduced failure",
            does_not_prove=DNP + "; payload is business data stored by design in proposal-bearing rows", detail={"hits": hits})
    assert hits == {}, hits
    assert os.environ.get("ADV_CANARY_CREDENTIAL") is None
