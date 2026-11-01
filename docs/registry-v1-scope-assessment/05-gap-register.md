# 05 Gap register (G1 to G4)

Non-authorizing. Machine-readable twin with full source references and remediation text: [data/gap-register.csv](data/gap-register.csv) / [json](data/gap-register.json). 33 gaps.

| Class | Meaning | Owner rule |
|---|---|---|
| **G1** | **Existing enforcement defect or accepted known limit.** A protection fails regardless of registry configuration. | Stays with the owning component. Not a registry feature. |
| **G2** | **Registry configuration gap.** The protection exists, but customers cannot govern the relevant policy centrally. | Registry architect with the component owner; per-family authorization. |
| **G3** | **Integration gap.** The registry may express the policy but cannot reliably bind it to the operational enforcement boundary. | Component owners (R10); the registry cannot close it alone. |
| **G4** | **Evidence / qualification gap.** The protection may exist but has insufficient proof. | Qualification owner. |

**Class and owner confirmation (P1 reconciliation).** Each gap was re-checked against the four classes and its owning component; no gap changed class. In particular: operation identity / dedupe defaulting OFF stays **G1** (GAP-G1-01, a component default the registry cannot change; D12 and the mandatory profile are separate rulings); the missing consumption path (GAP-G3-01), unauthenticated selection (GAP-G3-07) and missing effect-time binding (GAP-G3-02, GAP-G3-03) stay **G3**; missing independent evidence stays **G4** (GAP-G4-01/02 no scenario-level PASS and nothing at the current heads, GAP-G4-09 no MVP oracle row for a `LocalExecutionPolicy` denial, GAP-G4-13 no independent qualification owner). "Registry migration necessary?" answers whether closing the gap needs registry work; it never says the gap is a registry defect.

Severity (REASONED INFERENCE): High = could permit an uncontrolled effect, a boundary bypass or an unsupported public claim; Medium = limits what can be claimed or governed; Low = housekeeping or out of V1 scope.

| ID | Class | Scenarios | Component | Severity | Registry migration necessary? | Owner | Phase |
|---|---|---|---|---|---|---|---|
| GAP-G1-01 | G1 | D04;C09;SL:operation-identity:*_today | Control Plane / Runtime | High | NO (registry cannot change a component default; D7 mandatory profile is a design capability, not authorized) | Control Plane and Runtime owners; operator (D7) | Component backlog; R10 input |
| GAP-G1-02 | G1 | D07;C07 | Control Plane | High | NO | Control Plane owner | Component backlog |
| GAP-G1-03 | G1 | SL:mvp-d2-route-b:REACHABLE (5) | Control Plane / Runtime / hub ingress | High | NO | Hub ingress owner; Control Plane owner | Component backlog; R17 disclosure |
| GAP-G1-04 | G1 | TC-L06-018;TC-L06-045;TC-L17-002;TC-L17-021 | Exchange / Replay / Evidence Pack (repos not cloned) | Medium | NO | Exchange, Replay, Pack owners | Component backlog |
| GAP-G1-05 | G1 | SL:fix2-probes;SL:v1-probes (16 KNOWN_GAP rows) | Verifier / ODES / Control Plane / Index / Runtime | Medium | NO | Verifier, ODES, Control Plane, Index, Runtime owners | Component backlog |
| GAP-G1-06 | G1 | TC-L06-028 | Control Plane | Medium | CONDITIONAL (F11 deferred) | Control Plane owner | Component backlog |
| GAP-G2-01 | G2 | C11;TC-L06-009;TC-L06-011;TC-L06-013;TC-L06-014;TC-L06-016;TC-L06-024 | Runtime | Medium | YES for F1a/F1b (conditional on G3-01/02); CONDITIONAL for F1c (D6) | Registry architect with Runtime owner | R10 then R11 (per-family authorization) |
| GAP-G2-02 | G2 | C01;TC-L06-015;TC-D09-009;TC-D09-016;D03;C07 | Control Plane + Runtime | Medium | CONDITIONAL (F4; D4, D1) | Registry architect; Control Plane and Runtime owners | R11 (F4 lane) after rulings |
| GAP-G2-03 | G2 | C01;TC-L05-012;TC-L05-013 | Control Plane | Medium | NO for relaxing toggles; CONDITIONAL for tightening-only fields (F5; W8-014 UNRESOLVED) | Control Plane owner; Registry architect | R11 (F5 lane) only after rulings |
| GAP-G2-04 | G2 | C09;D04;C08 | Runtime + Control Plane | High | NO for V1 (F7 deferred); revisit after D12 | Control Plane and Runtime owners; Architect (D12) | After D12 ruling |
| GAP-G2-05 | G2 | C10;C16;SL (F3 rows) | Runtime / Control Plane | Low | NO for V1 | Runtime owner | Deferred |
| GAP-G2-06 | G2 | A04 | Runtime + Control Plane | Low | NO | Runtime and Control Plane owners | Deferred |
| GAP-G3-01 | G3 | all registry-dependent rows (C11, C01, C09, TC-L06-009/011/013/015, ...) | Registry + Runtime + Control Plane | High | YES (this is the registry integration itself) | Runtime and Control Plane owners; operator | R10 |
| GAP-G3-02 | G3 | C11;D02 | Runtime | High | YES (binding is a precondition for relying on registry policy at the effect boundary) | Runtime and Control Plane owners | R10 |
| GAP-G3-03 | G3 | C07;D07 | Control Plane | Medium | NO (route limit); disclose | Control Plane owner | R10 disclosure |
| GAP-G3-04 | G3 | TC-L06-014;TC-L06-016;TC-L06-024;C16;C18 | Control Plane + Runtime | Medium | CONDITIONAL (D6) | Architect (D6); Runtime and Control Plane owners | R11 (F1c lane) after D6 |
| GAP-G3-05 | G3 | TC-L06-013 | Runtime | Medium | NO for V1 (defer); revisit after an effect-bearing consumer and D5 exist | Runtime owner; Architect (D5) | Deferred |
| GAP-G3-06 | G3 | TC-L06-014;TC-L07-012 | Runtime | Medium | NO for V1 (defer) | Architect (D9) | Deferred |
| GAP-G3-07 | G3 | SL:operation-identity:adapter_forwarding;C20;C21 | Control Plane / registry | High | YES (R09) | OCS authority owner; operator | R09 |
| GAP-G3-08 | G3 | SL:hub ingress rows | Hub | Low | CONDITIONAL | Operator | R10 scoping |
| GAP-G4-01 | G4 | all 40 catalog scenarios | Qualification | High | NO | Independent qualification owner (not designated, D13) | R17 |
| GAP-G4-02 | G4 | all | Qualification | High | NO | Qualification owner | R17 |
| GAP-G4-03 | G4 | 656 Wiki cases | Qualification | Medium | NO | Qualification owner | R17 |
| GAP-G4-04 | G4 | A01;H02;C05;C15;C19;C20;C21 | Qualification | Medium | NO | Qualification owner | R17 |
| GAP-G4-05 | G4 | TC-L05-013 | Qualification | Medium | NO | Qualification owner | Before R17 |
| GAP-G4-06 | G4 | TC-L06-009 | Qualification | Low | NO | Qualification owner | Before R17 |
| GAP-G4-07 | G4 | SL:runtime known-limit tests | Qualification | Medium | NO | Qualification owner; Runtime owner | Before R17 |
| GAP-G4-08 | G4 | docs | Qualification | Low | NO | Qualification owner | Before R17 |
| GAP-G4-09 | G4 | C11;C02 | Qualification | High | NO | Qualification owner | Before R17 |
| GAP-G4-10 | G4 | D07;SL:mvp-chain NC1-04 | Runtime | High | NO | Qualification owner | R17 |
| GAP-G4-11 | G4 | D06 | Qualification | Low | NO | Qualification owner | Deferred |
| GAP-G4-12 | G4 | D04;C09 | Control Plane | Medium | NO until D12 | Architect (D12) | After D12 |
| GAP-G4-13 | G4 | all | Qualification | High | NO | Operator | Before R11/R17 |

## Reading the register

- **Do not classify all gaps as new registry features.** Only GAP-G2-01, GAP-G2-02 (conditional), GAP-G3-01, GAP-G3-02 and GAP-G3-07 need registry work. The existing enforcement defects and known limits (G1) and the evidence gaps (G4) are owned elsewhere and would remain open if the registry shipped tomorrow.
- **The G3 rows decide V1.** GAP-G3-01 (no consumption path), GAP-G3-02 (the `LocalExecutionPolicy` check is outside the atomic transaction; R10 Options A, B and C are all unimplemented) and GAP-G3-07 (selection is unauthenticated: `RuleRevisionProfile` signers are asserted, not verified) mean that **any family**, however well-ranked, delivers no protected governance until R09 and R10 exist.
- **Known-limit tests are not protection.** Tests that pass by asserting a limit (D07, C07, C10, C11 live-service surfaces, the six operation-identity `*_today` tests, the strict-xfail probes, the five `test_REACHABLE_*` tests, and the named Wiki `*_known_limit` tests) are evidence of a KNOWN_GAP. They are listed separately in the [acceptance matrix](06-v1-acceptance-matrix.md) and never counted toward a gate.
- **D12 is not a gap that has been confirmed.** GAP-G4-12 records the `dedupe.py` / `merge.py` difference and that no supported path to the divergent input was found. It is held for the Architect.
- **Evidence-quality items found while building the crosswalk** (not verdict changes): GAP-G4-05 (a known-limit test that cannot detect the opt-in `bounded_tolerance` toggle), GAP-G4-06 (a "known limit" test that asserts a refusal at the r13 pin), GAP-G4-07 (11 Runtime `*_known_limit` tests undeclared), GAP-G4-08 (stale inventory prose). Per release-gate rule 4 any reclassification is recorded by the owner before the next run that could show the result.

## Source-access limitation on the register

Rows whose component source is the Exchange, Replay, Evidence Pack, ODES, Verifier, BitRep or Index (GAP-G1-04, GAP-G1-05, parts of GAP-G4) rest on relocated test names and docstrings and are UNVERIFIED as to enforcement source.
