| ID | Source | Status | Mandatory | Provenance | Cases | Note |
|---|---|---|---|---|---|---|
| ER-01-1 | docx §01 BitRep | PASS | yes | NEW EXECUTION | 28 |  |
| ER-01-2 | docx §01 BitRep | PASS | yes | NEW EXECUTION | 6 |  |
| ER-01-3 | docx §01 BitRep | INCONCLUSIVE | yes |  | 9 | matched cases passed but are declared inadequate for the full requirement: tests exercise temporal behaviour; documentation of the semantics was not reviewed by |
| ER-01-4 | docx §01 BitRep | INCONCLUSIVE | yes |  | 7 | matched cases passed but are declared inadequate for the full requirement: zkproof tests execute; no test asserts the assurance-path refusal by name |
| ER-01-5 | docx §01 BitRep | PASS | yes | NEW EXECUTION | 15 |  |
| ER-02-1 | docx §02 The Index | PASS | yes | NEW EXECUTION | 25 |  |
| ER-02-2 | docx §02 The Index | FAIL | yes |  | 1 | product defect |
| ER-02-3 | docx §02 The Index | INCONCLUSIVE | yes |  | 1 | matched cases passed but are declared inadequate for the full requirement: only generic lifecycle/invariant tests matched; no supersession API exercised |
| ER-02-4a | docx §02 The Index | PASS | yes | NEW EXECUTION | 1 |  |
| ER-02-4b | docx §02 The Index | FAIL | yes |  | 1 | product defect |
| CTL-02 | docx §02 The Index | PASS | yes | NEW EXECUTION | 2 |  |
| ER-03-1 | docx §03 Alvorada constitutional governance | INCONCLUSIVE | yes |  | 18 | matched cases were skipped |
| ER-03-2 | docx §03 Alvorada constitutional governance | PASS | yes | NEW EXECUTION | 1 |  |
| ER-04-1 | docx §04 Agent Action Manifest | PASS | yes | NEW EXECUTION | 25 |  |
| ER-04-2 | docx §04 Agent Action Manifest | PASS | yes | NEW EXECUTION | 9 |  |
| ER-04-3 | docx §04 Agent Action Manifest | PASS | yes | NEW EXECUTION | 32 |  |
| ER-04-4 | docx §04 Agent Action Manifest | NOT RUN | yes |  |  | no executed check of migration notes; tools/validate_migrations.py scope not mapped to this component |
| ER-05-1 | docx §05 Agent Control Plane | PASS | yes | NEW EXECUTION | 30 |  |
| ER-05-2 | docx §05 Agent Control Plane | PASS | yes | NEW EXECUTION | 13 |  |
| ER-05-3 | docx §05 Agent Control Plane | PASS | yes | NEW EXECUTION | 3 |  |
| ER-05-4 | docx §05 Agent Control Plane | PASS | yes | NEW EXECUTION | 21 |  |
| ER-05-5 | docx §05 Agent Control Plane | PASS | yes | NEW EXECUTION | 30 |  |
| ER-05-6 | docx §05 Agent Control Plane | PASS | yes | NEW EXECUTION | 35 |  |
| ER-05-7 | docx §05 Agent Control Plane | NOT APPLICABLE | no |  |  | docx 05 Dependencies: fleet orchestration is a separate module to be scoped after the bounded workflow works; hub makes no C2/C3 fleet claim |
| ER-06-1 | docx §06 Moltbot Safe (supported runtime: cognous-execution-runtime) | PASS | yes | NEW EXECUTION | 174 |  |
| ER-06-2 | docx §06 Moltbot Safe (supported runtime: cognous-execution-runtime) | PASS | yes | NEW EXECUTION | 57 |  |
| ER-06-3 | docx §06 Moltbot Safe (supported runtime: cognous-execution-runtime) | INCONCLUSIVE | yes |  | 7 | matched cases passed but are declared inadequate for the full requirement: matched tests are few; filesystem/process/network isolation beyond a directory is not |
| ER-06-4 | docx §06 Moltbot Safe (supported runtime: cognous-execution-runtime) | PASS | yes | NEW EXECUTION | 18 |  |
| ER-07-1 | docx §07 Agent Replay Bundle | PASS | yes | NEW EXECUTION | 69 |  |
| ER-07-2 | docx §07 Agent Replay Bundle | PASS | yes | NEW EXECUTION | 50 |  |
| ER-07-3 | docx §07 Agent Replay Bundle | PASS | yes | NEW EXECUTION | 44 |  |
| ER-07-4 | docx §07 Agent Replay Bundle | INCONCLUSIVE | yes |  | 21 | matched cases passed but are declared inadequate for the full requirement: matched names are generic; no test named for delivery-to-verified promotion |
| ER-08-1 | docx §08 Agent Governance Evidence Pack | PASS | yes | NEW EXECUTION | 34 |  |
| ER-08-2 | docx §08 Agent Governance Evidence Pack | PASS | yes | NEW EXECUTION | 21 |  |
| ER-08-3 | docx §08 Agent Governance Evidence Pack | INCONCLUSIVE | yes |  | 21 | matched cases passed but are declared inadequate for the full requirement: assertion-label and relabel tests exist; no test asserts approval cannot follow from  |
| ER-09-1 | docx §09 Open Decision Evidence Standard | PASS | yes | NEW EXECUTION | 22 |  |
| ER-09-2 | docx §09 Open Decision Evidence Standard | INCONCLUSIVE | yes |  | 23 | matched cases passed but are declared inadequate for the full requirement: rejection vectors exist; separation of the three failure classes not asserted by name |
| ER-09-3 | docx §09 Open Decision Evidence Standard | NOT RUN | yes |  |  | document-review item; no executed check |
| ER-11 | docx §10-15 optional/other projects | NOT RUN | no |  |  | no test_*.py exists in this component at the pinned commit |
| ER-12 | docx §10-15 optional/other projects | PASS | no | NEW EXECUTION | 13 |  |
| ER-13 | docx §10-15 optional/other projects | NOT RUN | no |  |  | no test_*.py exists in this component at the pinned commit |
| ER-10 | docx §10-15 optional/other projects | NOT APPLICABLE | no |  |  | governed exchange transport covered under ER-IMX; archive repository private and excluded by the freeze manifest |
| ER-14 | docx §10-15 optional/other projects | NOT APPLICABLE | no |  |  | private repository; excluded by the freeze manifest (no private material read or published) |
| ER-15 | docx §10-15 optional/other projects | NOT APPLICABLE | no |  |  | private repository; excluded by the freeze manifest (no private material read or published) |
| ER-IMX | docx §10-15 optional/other projects | PASS | yes | NEW EXECUTION | 102 |  |
| SR-1 | docx Shared implementation requirements | INCONCLUSIVE | yes |  | 52 | matched cases passed but are declared inadequate for the full requirement: behavioural tests pass; no executed check of clock-uncertainty semantics as such |
| SR-2 | docx Shared implementation requirements | INCONCLUSIVE | yes |  |  | matched refund battery measures duplicate effect and recovery on one fixture; no conventional-control arm, latency or review-burden measurement executed (catalo |
| SR-3 | docx Shared implementation requirements | NOT RUN | yes |  |  | no executed provenance scan of the pinned public sources for proprietary logic |
| SC-MATCHED | Hub/Qualification PR #29 | PASS | no | NEW EXECUTION |  |  |
| SC-NATIVE-F5B | Hub F5b profile | PASS | yes | NEW EXECUTION |  |  |
| SC-TOOLING | PR #29 claim | PASS | no | NEW EXECUTION (verifies PR #29 claim) |  |  |
| SC-HUB-TESTS | Hub | PASS | yes | NEW EXECUTION |  |  |
| SCN-D01 | scenario catalog 3 Minimum deterministic acceptance suite | INCONCLUSIVE | yes |  |  | named synthetic assertion executed (matched refund battery, see SC-MATCHED); catalog mapping PARTIAL; not whole-catalog acceptance |
| SCN-D02 | scenario catalog 3 Minimum deterministic acceptance suite | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-D03 | scenario catalog 3 Minimum deterministic acceptance suite | INCONCLUSIVE | yes |  |  | named synthetic assertion executed (matched refund battery, see SC-MATCHED); catalog mapping PARTIAL; not whole-catalog acceptance |
| SCN-D04 | scenario catalog 3 Minimum deterministic acceptance suite | INCONCLUSIVE | yes |  |  | named synthetic assertion executed (matched refund battery, see SC-MATCHED); catalog mapping PARTIAL; not whole-catalog acceptance |
| SCN-D05 | scenario catalog 3 Minimum deterministic acceptance suite | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-D06 | scenario catalog 3 Minimum deterministic acceptance suite | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-D07 | scenario catalog 3 Minimum deterministic acceptance suite | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-D08 | scenario catalog 3 Minimum deterministic acceptance suite | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-D09 | scenario catalog 3 Minimum deterministic acceptance suite | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-A01 | scenario catalog 4 Agent and human qualification suite | NOT RUN | no |  |  | no accepted execution; coverage mapping UNIMPLEMENTED; needs paid agent runs or human participation, excluded by freeze manifest |
| SCN-A02 | scenario catalog 4 Agent and human qualification suite | NOT RUN | no |  |  | no accepted execution; coverage mapping PARTIAL; needs paid agent runs or human participation, excluded by freeze manifest |
| SCN-A03 | scenario catalog 4 Agent and human qualification suite | NOT RUN | no |  |  | no accepted execution; coverage mapping PARTIAL; needs paid agent runs or human participation, excluded by freeze manifest |
| SCN-A04 | scenario catalog 4 Agent and human qualification suite | NOT RUN | no |  |  | no accepted execution; coverage mapping PARTIAL; needs paid agent runs or human participation, excluded by freeze manifest |
| SCN-A05 | scenario catalog 4 Agent and human qualification suite | NOT RUN | no |  |  | no accepted execution; coverage mapping PARTIAL; needs paid agent runs or human participation, excluded by freeze manifest |
| SCN-A06 | scenario catalog 4 Agent and human qualification suite | NOT RUN | no |  |  | no accepted execution; coverage mapping PARTIAL; needs paid agent runs or human participation, excluded by freeze manifest |
| SCN-H01 | scenario catalog 4 Agent and human qualification suite | NOT RUN | no |  |  | no accepted execution; coverage mapping DEFERRED; needs paid agent runs or human participation, excluded by freeze manifest |
| SCN-H02 | scenario catalog 4 Agent and human qualification suite | NOT RUN | no |  |  | no accepted execution; coverage mapping DEFERRED; needs paid agent runs or human participation, excluded by freeze manifest |
| SCN-C01 | scenario catalog 18 Cognous Open Control Stack consolidation | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-C02 | scenario catalog 04 Agent Action Manifest | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-C03 | scenario catalog 01 BitRep | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-C04 | scenario catalog 02 The Index | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-C05 | scenario catalog 18 Cognous Open Control Stack consolidation | NOT RUN | yes |  |  | no accepted execution; coverage mapping UNIMPLEMENTED |
| SCN-C06 | scenario catalog 18 Cognous Open Control Stack consolidation | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-C07 | scenario catalog 18 Cognous Open Control Stack consolidation | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-C08 | scenario catalog 18 Cognous Open Control Stack consolidation | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-C09 | scenario catalog 18 Cognous Open Control Stack consolidation | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-C10 | scenario catalog 06 Moltbot Safe | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-C11 | scenario catalog Shared implementation requirements; 06 Moltbot Safe | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-C12 | scenario catalog 07 Agent Replay Bundle; 08 Agent Governance Evidence Pack | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-C13 | scenario catalog 07 Agent Replay Bundle | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-C14 | scenario catalog 09 Open Decision Evidence Standard; 18 Cognous Open Control Stack consolidation | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-C15 | scenario catalog 18 Cognous Open Control Stack consolidation | NOT RUN | yes |  |  | no accepted execution; coverage mapping UNIMPLEMENTED |
| SCN-C16 | scenario catalog 18 Cognous Open Control Stack consolidation | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-C17 | scenario catalog 18 Cognous Open Control Stack consolidation | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-C18 | scenario catalog 18 Cognous Open Control Stack consolidation | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-C19 | scenario catalog 18 Cognous Open Control Stack consolidation | NOT RUN | yes |  |  | no accepted execution; coverage mapping UNIMPLEMENTED |
| SCN-C20 | scenario catalog 03 Alvorada constitutional governance; 18 Cognous Open Control Stack consolidation | NOT RUN | yes |  |  | no accepted execution; coverage mapping UNIMPLEMENTED |
| SCN-C21 | scenario catalog 03 Alvorada constitutional governance | NOT RUN | yes |  |  | no accepted execution; coverage mapping UNIMPLEMENTED |
| SCN-C22 | scenario catalog 18 Cognous Open Control Stack consolidation | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
| SCN-C23 | scenario catalog 5 Evaluators metrics and acceptance rules | NOT RUN | yes |  |  | no accepted execution; coverage mapping PARTIAL |
