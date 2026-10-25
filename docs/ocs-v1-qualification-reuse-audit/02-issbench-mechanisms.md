# 02 Relevant ISSBench mechanisms

**Status: documentation-only analysis. Non-authorizing. Draft for Architect review. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.**

Nothing here authorizes a migration, approves a pin, selects or activates a record, or changes a qualification verdict. Implementation is not authorized. Labels as in [01](01-existing-ocs-capabilities.md).

`cognous-issbench-v2` was read at `5e05ecf71894731d2816ecabc764d8962652b5b9` as a read-only reference. No ISSBench script or test was run, and no ISSBench file is copied, linked or required by anything in this package. Capabilities are compared, not ISS-specific oracles. Rows are IDs I01 to I13 in [data/capability-matrix.csv](data/capability-matrix.csv).

## 1. Headline

ISSBench's reusable value is a **method plus small generic patterns, not importable code**. Almost everything under `fixtures/s02-*` and `fixtures/m1-*` is bound to ISS V6, Firestore and A1 contract identifiers. No product-independent library exists: each generic helper is 5 to 15 lines of standard library and is better re-expressed than imported. **SOURCE FACT**

The two repositories have no coupling in either direction. The qualification repository contains no occurrence of `issbench`, `iss-v1` or `iss-v6`; ISSBench contains no occurrence of `cognous-stack-qualification`, `cognous-control-plane`, `cognous-execution-runtime`, `cognous-replay-bundle` or `ocs-registry`. A SHA-256 comparison of every non-result, non-vendored file found **zero** byte-identical files across the two repositories and no near-identical same-name pair. **SOURCE FACT**

## 2. Two layers

1. **A small Python harness** (`issbench/*.py`, about 1,430 lines) built for context-management comparison and cost accounting: an append-only hash-chained `EvidenceLog`, request and response attempt accounting, spend reservation, paired bootstrap statistics, a dotted-path comparator, a raw-provenance checker, and freeze verification. Much of it is LLM-cost-specific. **SOURCE FACT**
2. **A document-and-JSON contract layer** (`specs/v6-planning`, `config/`) describing a TestSpec to EvidenceRecord pipeline. It is design requirements only; `qualification-record-contract.json` is marked `DESIGN_REQUIREMENTS_NOT_IMPLEMENTED_RUNTIME_SCHEMA`. It is the closest thing to selection, activation, revocation and freshness handling, and every part of it is ISS V6 content. **SOURCE FACT**

## 3. Mechanisms and what each means for OCS V1

| Mechanism | Where | Generic or ISS-specific | OCS V1 position |
|---|---|---|---|
| Freeze manifest, SHA-256 inventory of every file, fresh immutable output directory, per-attempt retention including failures | `fixtures/*/freeze.json`, `results/s02-v1/*/SHA256.json`, `scripts/qualify_s02.py` | Generic pattern | Equivalent exists here (immutable writer, `freeze-manifest.json`, `SHA256SUMS`). Use the local one (I02) |
| Prepared binding, then reviewed execution binding; corrections as additive successors, never edits | `fixtures/s02-*/binding.prepared.json`, `s02-replay-identity-v2/` | Generic pattern | Equivalent: versioned `expectations.proposed.vN.json`, `refreeze-log.json`, pre-registration amendments (I03) |
| Hash-chained evidence log | `issbench/core.py:86-132` | Generic structure, single-writer, LLM attempt accounting | Not needed (I01) |
| Raw-provenance oracle input: every normalized claim must resolve to a raw-record pointer; unassessed scope is BLOCKED | `issbench/s02_provenance.py:8-183` | Generic idea | Optional. The refusal template's independent read-only ledger read already covers the V1 need (I04) |
| Dotted-path comparator with a MISSING sentinel | `issbench/s02.py:20-54` | Comparator generic, dispositions ISS | Nothing to port (I05) |
| Durability battery M1DR-01 to 09: bound ALLOW atomic once; normal refusal then negative custody; HOLD then negative custody; staging failure atomic rollback; commit ACK loss then retry; fresh process after a later commit; historical readback with no duplicate effects; tampered or missing runtime evidence fails closed | `fixtures/m1-durability-recovery-v1/` | Property set generic; mechanics Firestore-bound | Checklist for the oracle author. Most is already covered here (NC2, `test_ruling4_lost_ack`, worker21, refusal evidence) (I06) |
| Changed-binding replay must not reuse the old receipt; no-write confirmed by before and after inventory diff; present / absent / inconclusive readback kept distinct | `fixtures/s02-replay-changed-binding-v1`, `s02-no-write-v1`, `s02-lost-ack-v1`, `s02-absent-v1`, `s02-inconclusive-v1` | Property generic, injection point Firestore-specific | The registry analogue (same selection id, different digest, refused under the lock) is a new case in QG-09 (I07) |
| Result vocabulary: PASS, FAIL, BLOCKED, NOT_EXECUTED, NOT_ASSESSED, NOT IMPLEMENTED, NOT APPLICABLE | `docs/qualification/README.md`, `specs/iss-v1-enterprise-qualification-v1.md:449-456` | ISS vocabulary | Not imported; it would invent statuses here (I08) |
| Lossless gzip pack and unpack of raw evidence | `scripts/pack_retention_evidence.py` | Generic | Not needed (I09) |
| Paid-pilot gating: approval string, single-use receipt, concurrency group | `.github/workflows/*-pilot.yml` | Generic gating pattern, LLM spend | Not applicable; V1 is synthetic-only (I10) |
| DGR test-idea families: RACE (activation or epoch change between resolve and commit gives STALE_CONTEXT, no delta, no retry), AUTH-BAD, SHADOW, REPLAY, ID, PRECEDENCE | `docs/qualification/registry-comparative-assurance.md`, `declarative-governance-registry-m1.md` | ISS V6 contracts, unrun | Ideas only for the independent author (I11) |
| Vendored upstream capsule with per-file blob and sha256 | `vendor/iss-v1/UPSTREAM.json` | Mechanism generic, ISS-v1 content | This repository has its migration manifest (I12) |
| Reimplemented canonical-JSON and sha256 helpers | `issbench/core.py:15`, `scripts/*` | Generic, trivial | Duplicate (I13); see [03](03-reuse-and-duplication-matrix.md) |

## 4. What ISSBench says about OCS, in its own words

These support keeping V1 qualification in this repository. **SOURCE FACT**, read in `docs/qualification/`:

- `registry-comparative-assurance.md`: "ISSBench retains independent oracle custody", and it forbids a generic interpreter and an OCS dispatch.
- `configuration-aware-plan.md`: OCS owners keep generic execution, replay, packaging and verifier services; "No OCS infrastructure duplication or tuple adoption follows."
- `AGENTS.md`: "the policy registry does not confer OCS effect authority" (prose only).
- `program-qualification-map.json`: "No candidate or OCS tuple selected."
- `m1-binding-expectations-20261021.md` itself reuses ISSBench's earlier manifest and validator "in form, without invoking the historical S02 collector", which is the re-express-not-import pattern recommended here.

## 5. What ISSBench does not have

No explicit revocation list or propagation, no rollback semantics beyond "recovery is monotonic authorized compensation, not old-pointer rollback" (an ISS storage rule), no registry freshness TTL beyond the ISS H1 HOLD clock (300 s, event-driven), no automated requalification trigger, and no generic result-diff tool. The A1C and A1D vectors are documentation proposals marked `PROPOSED_UNRUN_UNADOPTED`. **SOURCE FACT** So ISSBench cannot supply anything for revocation, expiry or rollback; those gaps stay OCS-side.

## 6. Unverified

Execution of any ISSBench test or script; whether freeze hashes still verify; the `fixtures/m1-binding-20261021/execution-*` adapters; the `s02-terminal-v1` semantics beyond protocol text (they concern terminal custody of an expired HOLD and are ISS-only); whether ISSBench repository has required status checks (not visible locally); the full text of a few long truncated lines in `configuration-aware-plan.md` and `s02-execution-v1.md`. The `m1-binding` freeze was recorded as never committed, so its immutability is unconfirmed.
