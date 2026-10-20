# Decisions of the comparison runner

Decisions already taken (not reopened here): destination-only comparison with a separate cross-reference column and no mixed scoring;
declared time T=0, clock from 100, usable range 100 to 999, statuses accepted and denied only, seeds 1701 and 1702, five repetitions;
scoring unchanged for every configuration; the block of RP-6 is always present; comparative statements only for a set on which the
configurations ran (RP-7); scope text and caveats unchanged on every report; run identity recorded (RP-9); outcomes shown as "asked k of n";
unscored observations of runnable not-claimed scenarios are retained; TC-D13-003 is not claimed (amendment 39).

## Rules of the column

The adapter applies a step exactly when the declared interface of the destination can express it. The interface is the eight request fields
(grant, effect, generation, policy, target, payload, verifier_status, issuer_claims) and the closed operation list (fence, grants, provision,
revoke, execute, ingress recovery). Every other scenario gets a not-expressible or not-claimed record with citations (interface item,
amendments 39, 74, 75, 76, the draft citation rule, case text). No record was derived from a result; the generator reads the plan file only,
and a test shows that changing expected outcomes does not change the declarations. Plumbing used renamed twins with verdicts discarded.

## Borderline decisions for the coordinator (conservative default applied, each one listed)

1. **Calls to a target other than the fixture sink (55 scenarios, code NE-TOOL-SET).** The destination pins one target per grant and has no
   allow-list of tools. Per-agent, per-tool grants could express some of these; the default is not expressible with citation. Alternative:
   provision one grant per agent and tool and compare the outcomes; this changes the column from destination-only to a mapped design.
2. **Positive-control scenarios asked (4 asked: TC-L06-008-S0, TC-L06-023-S1, TC-L06-034-S0, TC-L09-014-S3).** Asked because every step is
   expressible. The cell then reads "pass, asked 1 of n", which says nothing about the other scenarios of the case.
3. **Stop mapped to revoke.** Kept not expressible: a revoke removes a grant, a stop is a state of an agent. Alternative: map stop to
   revoke_grant for the agent grant.
4. **Not claimed by case sentence (TC-L09-018-S4, TC-L09-019-S1, TC-L09-019-S3).** Claims or payload content is the subject and the published
   applicability sentence says what OCS does not claim. Without a published sentence the question would be void and the scenario asked
   (code ASK-VOID-NC); none occurs today.
5. **Mixed cells.** A case with both not-claimed and not-expressible scenarios and none asked is labelled not expressible.
6. **Cell label "not asked"** added to the vocabulary for cases whose scenarios have no executable steps.
7. **RP-6 split** into (a) comparator pass with OCS fail or could not check and (b) comparator pass with OCS not expressible or not claimed;
   TC-D13-003 is annotated with amendment 39. (b) is not a fail and not a comparative statement.
8. **Principal 'agent' for every provisioned grant.** The ingress budget is 128 attempts per 60 clock units and administrative commands count
   against it; one principal per agent would saturate the longest scenario. The world's maximum effects and expiry are kept per grant.
9. **Plan-level not-executed scenarios (35: 19 not expressible, 16 not asked)** are carried for every configuration unchanged.
10. **Cognous unit control-removal probes (13)** are a different harness and are not run here. The registered plan's probes on the OPA
    application are run with the registered runner.
11. **Amendment numbering.** The repository's amendment 79 is a different text (major defects). The citation rule for not-expressible and
    not-claimed records is cited as "79-draft" until its number is settled.
12. **Cross-reference** column is read from comparators/wiki/crossref and labelled "different harness, not scored by this oracle".
13. **Unlisted-files check.** The package digest tool of `comparators/` does not know the `runner` group, so its unlisted-file check reports
    these files until its owner adds the group. This directory keeps its own `digests.json`; `run_comparison.py` verifies it.
14. **Declarations are generated from the plan file** and checked against its digest. If the plan gains or loses scenarios the entry points
    stop with exit status 2 until `declare_ocs_column.py --write` has been run and the output reviewed.
15. **Candidate manifest digest** follows amendment 91 (the three listed manifest files); a missing file is recorded as not available.
16. **Contract self-check is part of the real run** and stops it on any problem.
