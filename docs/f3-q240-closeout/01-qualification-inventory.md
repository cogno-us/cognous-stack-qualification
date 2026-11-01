# 01 Qualification inventory and Q1-Q8 dispositions (2026-10-30)

## 1. Verified current heads (fetched 2026-10-30)
| Repository | Head | Note |
|---|---|---|
| cogno-us/cognous-ocs-registry main | `6b96a9a658923954433dc1a4c13626fa5145b9c7` | Matches directive |
| cogno-us/cognous-control-plane main | `b19c47ddd020409d24e52e70b11359c46265edbb` | Later than the frozen subject |
| cogno-us/cognous-stack-qualification main | `b7d813111128cb31518620688f6e89e41042dadd` | Matches directive; PR #242 open on top |
| cogno-us/cognous-engineering-constitution main | `dcdbe3b76843d672ca3cfb1f000124ecd78ed03c` | Prospective convention revision |

**Frozen executable subject:** Control Plane `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69` (src tree `d248bde4...`). Live main `b19c47dd` is NOT the subject. `8616d5f` differs from 739efe7 only in a module docstring (AST equality derived in PR #242). Registry r08-v8 pin for execution: `a40fe755e2384a99c37016fa9ad59396f1835900` (detached checkout).

## 2. Evidence inventory
| Item | Location | State |
|---|---|---|
| Original F3 independent evidence (FAIL, DEV-PE-1, 23 failed assertions; F3-B scoped PASS) | hub `results/third-party/cp-739efe7-f3-independent-20261029/` | In merged custody; permanent |
| Successor readjudication evidence (48 files, `SHA256SUMS` 47 entries) | PR #242 head `2246a61c18a2c491a1230c21912b1240c109e90a`, `results/third-party/cp-739efe7-f3a-readjudication-20261030/` | Original bytes (tree id identical to `44ce26eb`) published by the producing session; **not merged, not yet independently checksum-verified** |
| Registry records 11-14 | Registry `docs/family-migration/final-three/` | Record 11 builder-prepared, unsigned; human adoption pending |
| Constitution revisions 1c2e920 / 230c0af / dcdbe3b | constitution repo | No ADOPTION.md-form instrument for any |

## 3. Disposition of Q1-Q8
Rule applied: CLOSED only when the item's own acceptance criterion is met. Nothing below is CLOSED.

| Q | Obligation | Disposition | Actual acceptance criterion | Dependency / blocker (authority) |
|---|---|---|---|---|
| Q1 | Successor evidence custody | **OPEN** (bytes available; not BLOCKED) | Merged repository contents independently checksum-verified from a fresh checkout | Independent review and merge of PR #242 by an authorized reviewer (Architect/repository controls); then fresh-clone `sha256sum -c` by someone other than the producer. Byte identity: the evidence directory at PR #242 head `2246a61c` has git tree id `9004b517b381e5bc57bf7079f11d73c20e4d64ed`, identical to the tree at the originally reported local commit `44ce26eb` (found in the coordinator's local clone, branch `f3a-readjudication-20261030`, 48 files). Nothing was regenerated. Caveat: the producer is the coordinator session, so independent checksum verification remains required. |
| Q2 | A25(a) authority-domain isolation | **OPEN** | Independent end-to-end demonstration, or an independently adjudicated evidence decomposition (component / end-to-end / guard-order) | Archetype D assignment `D-1` ready; needs designated independent owner (Q7). Static finding: natural isolation structurally impossible (member is a function of the manifest whose digest is itself a base-binding member); a GRAFT route is predicted to isolate; unexecuted. |
| Q3 | A25(e) host/effective digest isolation | **OPEN** | As Q2 | Same assignment. Predicted: `host_profile_digest` end-to-end isolable on an F5 masked-host edit (contrary to the original record); `effective_profile_digest` joint-only. All unexecuted. |
| Q4 | D06-M06 evidence | **OPEN** | Independent re-execution of the M06 kill on a pristine copy, with the harness identity re-hashed | Assignment `D-2` ready; needs Q7. Source evidence now exists in PR #242 (`raw/M06-mutant`: 1 failed, three named persisted-content checks) and the first-run record is intact. Limits: written by the same session after the survival was known; shows harness content sensitivity, not comparison sensitivity. |
| Q5 | `provision_local_execution_claim` coverage | **DEFERRED** (class B per record 12) | Independent coverage of the provision wrapper under D-06 drift, or the Architect's explicit acceptance of the limit | Assignment `D-2` ready. Not exercised by the original or readjudication harnesses; builder tests do not drive D-06 through provision. Whether class B deferral stands is an Architect decision. |
| Q6 | Python 3.12 coverage | **DEFERRED** (class B) | Independent 3.12 run, or the Architect's acceptance of CI-only evidence | Assignment `D-2` ready. CI at 739efe7 has a 3.11/3.12 matrix (builder-controlled; logs not inspectable by this session; ungated D-06 suites never shown to execute under no-skip). All independent runs were 3.11.18. |
| Q7 | Independent-owner designation and certification | **BLOCKED** | Written designation of an independent owner with a recorded independence basis; a competent certification decision | Architect/operator. No designation exists anywhere. Sources name three conflicting designating authorities. Sources give only a negative independence standard. |
| Q8 | Constitutional adoption instrument | **BLOCKED** | ADOPTION.md-form instrument (exact revision, scope, effective point, reserved powers, exceptions) | Architect approval. Draft supplied (05). Not required for the engineering closeout document to be accurate; required before any adoption claim or before treating the newer revisions' process texts as governing. |

Recorded scope limits (unchanged, not closed by this package): pin-export declares the F4 family only; cross-process real clock outside F3-A scope; DEF-OBS-TOL-OVERFLOW-1 open and separate.
