#!/usr/bin/env python3
"""Stub verifiers that prove the mutation harness. They are NOT verifiers and verify nothing real.

    stub_verifier.py --mode accept|reject|abstain|crash|garbage|invalid|slow|partial --run-record F [--proposal F] [--ledger F]

``accept`` confirms every trace, ``reject`` refutes every trace, ``abstain`` could-not-checks every trace, ``crash`` exits without a
report, ``garbage`` prints text that is not JSON, ``invalid`` prints a report the ODES validator refuses, ``slow`` hangs. ``partial``
makes a handful of real but narrow checks (strict parse, result versus reasons, ledger rows versus authorized decisions) so a harness
test can see mixed detection. Each prints one ODES ``verification-report`` on standard output.
SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time

PROFILE = "json-sort-keys-compact-utf8-no-nan-python-semantics-v0.1"
CLAIMS = ("relative_to_pinned_controller", "semantic_quality_not_certified", "receipt_source_bounded", "self_consistent_forgery_not_detected",
          "not_an_attestation", "parse_strictness_is_refusal_not_repair", "no_v1_scope_claim", "differential_agreement_is_not_equivalence")


def commitment(value) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


class Strict(ValueError):
    pass


def _pairs(pairs):
    seen = set()
    for k, _ in pairs:
        if k in seen:
            raise Strict("wire_duplicate_member")
        seen.add(k)
    return dict(pairs)


def _const(name):
    raise Strict("wire_nonfinite_constant")


def strict_load(data: bytes):
    if data.startswith(b"\xef\xbb\xbf"):
        raise Strict("wire_bom")
    try:
        text = data.decode("utf-8")
        decoder = json.JSONDecoder(object_pairs_hook=_pairs, parse_constant=_const)
        value, end = decoder.raw_decode(text.lstrip())
    except Strict:
        raise
    except RecursionError:
        raise Strict("wire_depth")
    except ValueError:
        raise Strict("wire_syntax")
    if text.lstrip()[end:].strip():
        raise Strict("wire_trailing_data")
    stack = [(value, 1)]
    while stack:  # a stated depth limit, as a real verifier states one
        v, depth = stack.pop()
        if depth > 256:
            raise Strict("wire_depth")
        if isinstance(v, dict):
            stack.extend((x, depth + 1) for x in v.values())
        elif isinstance(v, list):
            stack.extend((x, depth + 1) for x in v)
    return value


def check(check_id, tier, verdict, findings=(), reason=None):
    n = 1
    tally = {"confirmed": int(verdict == "confirmed"), "could_not_check": int(verdict == "could_not_check"), "refuted": int(verdict == "refuted"), "n": n}
    return {"check_id": check_id, "tier": tier, "verdict": verdict, "tally": tally, "could_not_check_reason": reason,
            "findings": [{"code": c, "locator": "$", "detail": c.replace("_", " ")} for c in findings]}


def partial_checks(paths):
    out = []
    docs = {}
    for role, path in paths.items():
        try:
            docs[role] = strict_load(open(path, "rb").read())
        except Strict as exc:
            out.append(check(f"wire.{role.replace('_', '-')}", "V1", "refuted", [str(exc)]))
    if "run_record" in docs:
        rr = docs["run_record"]
        bad = [d for d in rr.get("decisions", []) if isinstance(d, dict) and ((d.get("result") == "authorized") != (not d.get("reasons")) or (d.get("result") == "authorized") != (d.get("binding") is not None))]
        out.append(check("v2.decisions", "V2", "refuted", ["decision_result_inconsistent"]) if bad else check("v2.decisions", "V2", "confirmed"))
        if "destination_ledger" in docs:
            authorized = {d.get("effect_id") for d in rr.get("decisions", []) if isinstance(d, dict) and d.get("result") == "authorized"}
            rows = docs["destination_ledger"].get("effects", {})
            stray = [r for r in rows.values() if r.get("effect_id") not in authorized]
            out.append(check("v4.ledger", "V4", "refuted", ["ledger_effect_without_decision"]) if stray else check("v4.ledger", "V4", "confirmed"))
    if not out:
        out.append(check("v1.nothing", "V1", "could_not_check", reason="input_absent"))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True)
    ap.add_argument("--run-record", required=True)
    ap.add_argument("--proposal")
    ap.add_argument("--ledger")
    a = ap.parse_args(argv)
    if a.mode == "crash":
        print("stub verifier crashed", file=sys.stderr)
        return 3
    if a.mode == "garbage":
        print("this is not a report")
        return 0
    if a.mode == "slow":
        time.sleep(30)
    paths = {"run_record": a.run_record}
    if a.proposal:
        paths["proposal_export"] = a.proposal
    if a.ledger:
        paths["destination_ledger"] = a.ledger
    if a.mode == "accept":
        checks = [check("stub.accept", "V1", "confirmed")]
    elif a.mode == "reject":
        checks = [check("stub.reject", "V1", "refuted", ["stub_always_reject"])]
    elif a.mode == "abstain":
        checks = [check("stub.abstain", "V1", "could_not_check", reason="tier_unavailable")]
    elif a.mode in ("partial", "invalid"):
        checks = partial_checks(paths)
    else:
        raise SystemExit(f"unknown mode {a.mode}")
    inputs = []
    for role, path in paths.items():
        data = open(path, "rb").read()
        inputs.append({"role": role, "name": path.rsplit("/", 1)[-1], "digest": "sha256:" + hashlib.sha256(data).hexdigest(), "size_bytes": len(data)})
    inputs.sort(key=lambda i: (i["role"], i["name"], i["digest"]))
    counts = {k: sum(1 for c in checks if c["verdict"] == k) for k in ("confirmed", "could_not_check", "refuted")}
    doc = {
        "contract": "verification-report", "contract_version": "0.1.0-draft", "profile": "verification-report/0.1", "report_kind": "verification_report",
        "report_id": "stub-" + commitment(inputs)[7:19], "generated_at": "2026-10-18T00:00:00+00:00",
        "verifier": {"name": "stub-verifier", "version": "0", "command": "cognous-verify", "source_revision": "stub", "canonicalization_profile": PROFILE},
        "subject": {"canonicalization_profile": PROFILE, "inputs": inputs, "inputs_digest": commitment(inputs),
                    "pinned": {"controller_revision": "stub", "contract_versions": {"control-plane-journal": "0.1.0-draft"}, "reason_registry_digest": "sha256:" + "0" * 64}},
        "scope": {"semantic_quality": "not_assessed", "tiers_run": sorted({c["tier"] for c in checks})},
        "checks": checks, "summary": {"checks": len(checks), **counts},
        "does_not_prove": [{"id": c, "statement": c.replace("_", " ")} for c in CLAIMS], "mutation_report": None,
    }
    if a.mode == "invalid":
        del doc["does_not_prove"]
    print(json.dumps(doc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
