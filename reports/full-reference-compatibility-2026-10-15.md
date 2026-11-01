# Full-reference compatibility repair — 2026-10-15

**Local bounded compatibility: PASS. Candidate remains nonselected. Publication,
production and operational trust remain HOLD / NOT ESTABLISHED.**

This repairs the fixture/generation failures recorded by hub PR #131. It does not
repair the unsafe C0 check-to-commit interval, implement an external restore anchor,
or establish independent security/rights/operational acceptance. C1 stays optional,
same-host and cooperative; no C2/C3 or real settlement is qualified.

## Sources and method

- Owning hub source: `9d45ab4389f9ac7b7cd0e3b8823fa2fde56d8503`.
- Canonical qualification starting point: `c7f0ae68333886b187808768b1bfa4ed0191348d`.
- First published repaired suite head: `a53a736f31d4248bfdae45050ce363f1ce4aab04`,
  Git tree `2d9097321dec48cef83a0b62d9e65a629642ea02`, identical to the tested local
  suite tree. Local recorded suite commit IDs in raw batch summaries identify the
  development checkout; they are not asserted to be reachable GitHub commits.
- Profile: owning source `profiles/remediation-full-reference-20261015.json`;
  thirteen candidate/static component pins unchanged. The seven-component repaired
  chain and all older regression pins remain exact. All 30 actual reused component
  checkouts were checked at completion for tracked cleanliness and their Git heads.
- A fresh detached owning-source worktree received the canonical overlay through
  `tools/install_suite.py`, retaining both Git identities, original source hashes,
  adapted suite hashes and modification notices. No component implementation was
  patched. Dependency versions use the existing hashed release requirements.
- Concurrent main `60f2ef819f48192d1d5a9d34ee637b9b72c9f707` adds comparator assets
  and hosted-adoption records. Those changes were merged intact after the local
  run; they do not change the tested compatibility code. Comparator behavior is
  not claimed executed by this report. Hosted final-head results are recorded in
  the PR handoff rather than predicted here.

## Repairs

1. Keep every historical producer pairing at its original revisions. Historical
   merged-consumer generators no longer receive the new executor/Replay pair.
   New consumer implementations still run their backward-compatibility suites.
2. Separately require current executor, Replay, ODES, Evidence Pack and GAX refusal
   suites, with both repetitions required. Missing current suites cannot be
   satisfied by historical green results. Skipped or failed current/merged cases
   fail aggregation; no xfail is introduced.
3. Dated synthetic fixtures explicitly inject the CP service clock, without
   changing its freshness policy or restoring trust in request-supplied time.
   The expiry case advances its independent service fixture clock. Runtime
   source files, live clocks and authority settings are unchanged.
4. Constructor fixtures honor declared optional dataclass defaults, while actual
   constructors still reject missing required inputs.
5. Candidate recovery denial must append exactly one bound refusal and one read
   check, retain their typed reasons and exact exported evidence, preserve
   prior decisions/attempts/observations/closeouts and maintain monotonic input
   floors. Destination rows, original export and no-retry requirements remain.
   Historical no-append/no-evidence expectations remain for historical inputs.
   Negative controls reject substituted export data, changed decisions, extra
   attempts, missing refusals and regressed floors.
6. Current GAX artifact tests run from the canonical checkout against clean,
   exact component implementations. Their candidate provenance sets are exact
   singletons; historical revision assertions run separately unchanged. This
   does not broaden a production consumer allowlist or suppress a comparison.
7. Overlay installation accepts only original or explicitly recorded reconciled
   source bytes. The concurrent hub aggregator adaptation is recorded by exact
   source commit/hash; arbitrary newer source files still fail closed.

## Observed results

The baseline authority run reproduced 68 setup errors in each 155-element
repetition and eight failures in the separate 120-element OpenShell mock suite.
Intermediate failed runs were retained, not relabeled. The final local run used
Python 3.12.14; both repetitions had the same outcome counts:

| Batch | Testcase elements per repetition | Passed | Failures | Errors | Skips |
| --- | ---: | ---: | ---: | ---: | ---: |
| Authority | 162 | 162 | 0 | 0 | 0 |
| Exchange | 137 | 137 | 0 | 0 | 0 |
| Consumers | 757 | 756 | 0 | 0 | 1 |
| Registry | 82 | 82 | 0 | 0 | 0 |

Counts are raw JUnit testcase elements, not assertions about independent cases or
subtests. The one consumer skip is collection of the existing opt-in
`tests.test_w3_composed_candidate`, outside this bounded profile. It remains visible
and is not counted as coverage. All mandatory current refusal and merged producer
cases have zero skips. The separate OpenShell suite passed 120 elements in mocked
transport scope only. Registry Node tests passed 20 per repetition. Optional
protocol checks remain static JSON checks, not behavioral evaluation.

The unchanged 35-scenario acceptance matrix resolved successfully. It includes
explicit historical regression evidence plus current candidate behavior, not an
assertion that each historical consumer fixture was redefined as current.
Current authority/transport/recovery, retained artifact and typed-refusal tests
exercise the actual candidate pins; historical producer interoperability remains
separately identifiable. Both transported representatives passed material checks,
including exactly one effect, matching destination rows, identities, commitments
and retained artifacts. Their normalized expected outcomes repeat; UUID-bearing
raw bytes are not asserted byte-identical.

See [machine results](full-reference-compatibility-2026-10-15.json) for all batch
results, raw JUnit/summary hashes, aggregate hash and actual component/regression
pins. Local raw material remains scratch evidence; the new PR matrix retains raw
JUnit/log/representative artifacts and assembly identities in GitHub Actions.
Artifacts have GitHub retention limits and require durable accepted evidence
references before any future release claim.

## Reproduction

From an owning hub checkout, first assemble this canonical suite with
`tools/install_suite.py` and retain its identity report. Use a clean qualification
checkout whose migration manifest matches the adapted test hashes. Run:

```bash
python tools/reference_release.py run --qualification-root /path/to/cognous-stack-qualification --profile profiles/remediation-full-reference-20261015.json --batch authority --results-dir results/current-authority
python tools/reference_release.py run --reuse-checkouts --qualification-root /path/to/cognous-stack-qualification --profile profiles/remediation-full-reference-20261015.json --batch exchange --results-dir results/current-exchange
python tools/reference_release.py run --reuse-checkouts --qualification-root /path/to/cognous-stack-qualification --profile profiles/remediation-full-reference-20261015.json --batch consumers --results-dir results/current-consumers
python tools/reference_release.py run --reuse-checkouts --qualification-root /path/to/cognous-stack-qualification --profile profiles/remediation-full-reference-20261015.json --batch registry --results-dir results/current-registry
python -m tools.aggregate_full_candidate --profile profiles/remediation-full-reference-20261015.json --artifacts results --out aggregate-results
```

Use a fresh results tree containing only the four intended batch summaries.
The canonical PR workflow performs all four batches independently and aggregates
within the same run, with fixed owning source and exact suite revision. Adopting
this new canonical commit into hub delegates is a separate integration change;
the open hub migration PR must preserve these diagnostics and pin the accepted
suite commit. Private-inventory administrative metadata is omitted from the updated public
manifest; only the disabled-public-export flag remains. No private repository
content was read or exported. No selected lock, existing profile, acceptance matrix, release
permission, repository setting or production grant changes here.
