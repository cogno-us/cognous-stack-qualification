# Lane B notes: V1 and security-runtime batteries

Revisions read: qualification repo HEAD 998d39c5 (main, 2026-10-24); Control Plane 7a4bcd40; Execution Runtime c5e97e87 (head moved from the earlier ec728da6); registry docs main 783ff59f. All read-only. Labels: SOURCE FACT, REASONED INFERENCE, CUSTOMER HYPOTHESIS, UNVERIFIED.

## Files and counts
- `B-catalog-rows.jsonl`: 40 rows (D01-D09, A01-A06, H01-H02, C01-C23; ids match catalog.json; every test path exists; test symbols verified by AST for suites/ paths).
- `B-suitelocal-rows.jsonl`: 53 rows (`SL:<suite>:<slug>`): security-runtime 7, runtime-authority 1, operation-identity 13, v1-probes 22 (incl. 6 strict-xfail KNOWN_GAP rows), fix2-probes 10 (incl. 3 known-limit rows).

## Method
1. Catalog and coverage-map read for all 40 ids; the 49 distinct mapped tests all exist. Per scenario, test ids = coverage-map tests plus every `test_*` function in `suites/v1-scenarios/test_scn_<id>.py` (D02, D05-D09, C01-C04, C06-C14, C16-C18, C22, C23) plus matched-refund variants (`tools/run_matched_refund.py` VARIANTS) for D01/D03/D04.
2. Enforcement components read in Runtime and Control Plane source (path:line in `enforcement_function`). Components whose repos are not cloned (Index, Replay, Pack, Exchange, ODES, Verifier, BitRep) are marked "repo not cloned"; no line is inferred from READMEs.
3. Evidence from `results/v1-validation/v1-2026-10-16-a/g8-r10-39690459403/` (requirements matrix, summary), `docs/v1-known-limits.md`, `docs/test-inventory.md` X-01..X-06, `results/security-runtime-merged-20261016/`.
4. Every catalog scenario verdict is NOT RUN. SCN rows in the g8-r10 matrix are INCONCLUSIVE (partial coverage, named cases passed, 0 failed) for D02, D05-D09, C01-C04, C06-C14, C16-C18, C22, C23, and D01/D03/D04 come from the matched-refund battery (20/20 PASS). SCN rows are NOT RUN for A01-A06, H01, H02, C05, C15, C19, C20, C21. `PASS_RECORDED` in my rows means named executed cases passed, never whole-scenario acceptance.
5. `exclusion_impact` begins with OBSERVATION=FIXED_CODE_INVARIANT or OBSERVATION=CONFIGURABLE_VALUE, answering whether the required observation depends on a configurable policy value or a fixed invariant.

## Findings
**No catalog scenario is REGISTRY_REQUIRED (REASONED INFERENCE).** Of 40 rows: UNNECESSARY 25, UNKNOWN 12, BENEFICIAL 3 (C01, C09, C11). Every V1 enforcement path is in code, configured by Python constructor, manifest, resolver data or opt-in profile. In 26 of 40 rows the observation is a fixed invariant (binding, ordering, idempotency key, formats M7/M8).

**Where a registry would supply a value (not a copy):**
| Scenario | Family | What it would supply | Why only BENEFICIAL |
|---|---|---|---|
| C11 | F1a/F1b/F1c | local allow-lists and ceilings, composed by intersection (registry only narrows) | `LocalExecutionPolicy` (`safe_executor.py:359`) already enforces them; it has no loader (grep of engine/ for environ/getenv empty), so a registry needs a new consumer (G3). F1c open under D6 |
| C01 | F4/F5 | `on_unreadable`, `max_status_age_seconds` per ActionClass (`runtime_authority.py:82-88`) | missing-grant refusal is invariant (`bounded.py:2340`); only the unreadable tolerance is a value |
| C09 | F7 | dedupe-ttl window | profile is OFF by default; effect-id dedupe never expires and needs no registry |

**Redundant allow-list copies:** D02 and C02. The test (policy_mode narrow vs widened) shows binding to proposal/decision/grant (`control_plane_adapter.py:270-316`) and manifest membership (`bounded.py:2608-2689`) refuse, not an allow-list. A registry F1a/F1b copy would carry a copy of a comparison code already makes.

**Unsupported / not applicable by own text:** A01, C05, C15, C19, C20, C21 UNIMPLEMENTED (D9: stay NOT RUN, not N/A); H01/H02 DEFERRED human work; A02-A06 need paid agent arms and are excluded by the freeze manifest; D06 asks for measured CPU/memory/concurrency against a predeclared profile, no such test or profile exists (the mapped test checks report shape). C22, C23 are measurement-method scenarios, existing_protection NOT_APPLICABLE.

**Known-limit assertions counted as KNOWN_LIMIT_ASSERTED, not protection:** D07 (restore of authority plus revocation tables reopens a revoked grant; a registry is not an external anchor), C07 (route A residual check-to-commit race C0, resolver read once), C10, C11 (live-service surfaces), and all `*_today` operation-identity tests (profile-OFF legacy defaults assert two effects can land).

**Registry-adjacent existing mechanism:** `RuleRevisionProfile` (`rule_revision.py:65`) digest-pinned policy adoption with `signers` that are asserted and unauthenticated; operation-identity `test_adapter_forwarding` refuses an unadopted digest at effect time. This overlaps registry adoption/selection (C20/C21 are nearest, but unimplemented). Record, selection and activation are separate (D2: pin-only insufficient for selection; D7: mandatory participation only a design capability).

**F6 has no execution consumer.** `PermissionSystem` is used only by legacy `AgentEngine`, which never executes (status unsupported). `agent_id` is caller-asserted. Absent-agent semantics are D5 (open); not resolved here.

## Name collision
In `v1-known-limits.md`, the catalog and C04/Index probes, "registry" means the Index (cognous-evidence-registry) or the Control Plane reason registry (164 codes). Neither is the OCS Registry program. The reason registry vocabulary is mandatory M7. Readers must not equate "registry declares no reopen predicates" (xfail) with OCS Registry scope.

## G1-G4 candidates
| Id | Class | Source ref | Owner suggestion |
|---|---|---|---|
| G1-B1 | G1 copied evidence counted as independent (F-19, not closed beyond three copy cases) | docs/v1-known-limits.md F-19; SCN-C04; v1-probes test_index_probes.py | Index owner |
| G1-B2 | G1 six ADD-AUTH-RA spec-gap probes (component version, observation age, criterion reference, reopen predicates, trend unmapped codes, freshness-before-criterion) | suites/v1-probes/KNOWN_LIMITS.md; test_authority_ra_probes.py | Control Plane owner |
| G1-B3 | G1 Verifier checks effective_max_effects only against proposal export and ledger | suites/fix2-probes/KNOWN_LIMITS.md row 6 | Verifier owner |
| G1-B4 | G1 clock-domain stamp ordering (verifier and ODES reconciliation; ODES closeout) | fix2 KNOWN_LIMITS rows 1-3 | Verifier / ODES owners |
| G1-B5 | G1/spec: runtime reports observed_state applied after post-commit failure; probe expects unknown | fix2 KNOWN_LIMITS rows 4-5; `safe_executor.py:993,1035,1073` | Runtime owner |
| G2-B1 | G2 `LocalExecutionPolicy` values constructor-only; ints in workflow ctor and ActionClass; profile fields; FreshnessProfile; DedupeProfile; manifest limits; producer_keys | `safe_executor.py:359`; `bounded.py:1264-1291`; `runtime_authority.py:82-150` | Registry architect with Runtime and Control Plane owners |
| G2-B2 | G2 opt-in profiles default OFF; legacy defaults asserted by `*_today` tests | suites/operation-identity | Control Plane owner (D7 decision) |
| G3-B1 | G3 F6 allow-list governs only the legacy shell | `permissions.py`, `engine.py` | Runtime owner |
| G3-B2 | G3 no runtime loader or consumer for F1a-F1d values | grep of engine/ | Runtime owner |
| G3-B3 | G3 RuleRevisionProfile.signers unauthenticated vs registry adoption; trust anchors (producer_keys) unmapped to any family | `rule_revision.py:65`; `runtime_authority.py:150` | Registry architect |
| G3-B4 | G3 C0 race: route A reads the resolver once, so a registry-selected value cannot be bound atomically at commit on that route | `bounded.py` execute; docs/v1-known-limits.md | Control Plane owner |
| G4-B1 | G4 36 rows moved out of the claim (D15); V1 claim narrowed to 39 passing rows | docs/v1-known-limits.md D15 | Qualification owner |
| G4-B2 | G4 runtime-authority and operation-identity not run by the controller; runtime-authority evidence is a doc statement only | test-inventory X-04, X-06 | Qualification owner |
| G4-B3 | G4 F-15 and F-24-F-28 FIXED-UNVERIFIED pending a controller run at current pins | v1-known-limits | Qualification owner |
| G4-B4 | G4 Runtime head moved (c5e97e87) from the pins of the last controller run | suites/_pins.py | Qualification owner |
| G4-B5 | G4 security-runtime inventory X-03 NOT_RUN_HERE conflicts with controller native-f5b-suite 36/0/0/0 and a merged result (twice 36/36) | test-inventory; g8-r10 summary | Qualification owner |

## Limitations
- Index, Replay, Pack, Exchange, ODES, Verifier, BitRep source is not cloned; their rows carry no enforcement line (UNVERIFIED) and are inferred only from the relocated tests' names and docstrings.
- No suite or controller was run; counts come from AST and result files. Selector-matched counts are from g8-r10 and may not hold at current pins.
- evidence_status for operation-identity is COLLECTED_ONLY because the only PASS statement is the inventory page's state (X-06, 50 pass).
- R07 decisions D1, D5, D6, D12 and the 32 UNRESOLVED S02 rows are referenced as open and not resolved.
- Registry dependency ratings are REASONED INFERENCE about code seams; no customer demand is claimed, and nothing here is established as healthcare or financial customer validated.
- `registry_family` is UNMAPPED where R07 has no family for the mechanism (trust anchors, funded authorities, fleet, conflicting proposals).
- Control Plane returns in many rows cite one source line range; small line drift across revisions is possible.
