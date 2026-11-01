# Adversarial tests, batch 1 (T01 to T20)

Executable tests for the batch-1 list of the adversarial test plan ([`docs/adversarial-test-plan.md`](../../docs/adversarial-test-plan.md),
section 7; machine-readable twin [`ideas.json`](ideas.json)). Programme 2, tracker cogno-us/cognous-control-plane#43.

- These are **not** scenario-catalogue entries and they **never** feed the `v1_validation` verdict. Their result vocabulary is the
  plan's: prevented, detected only, reproduced failure, inconclusive, not applicable, not tested.
- Synthetic fixtures only (the components' own test fixtures, through the existing harness `suites/operation-identity/_oi_flow.py`).
  No network effects, no release, no pin change.
- The plan and `ideas.json` still say `not tested`; they are left unchanged here and are updated at the docs cleanup.
- Each test module's docstring states the attacker, the invariant, how destination state is read (always through an independent
  read, never from the executor's acknowledgement) and what the test does **not** prove.

## Components attacked

Current revisions, listed in [`components.json`](components.json) and checked against each checkout's HEAD at run time:
control plane `2bac7875`, runtime `6b16962d`, verifier `dc09a98f`, Replay `6a6a4774`, Evidence Pack `fd030615`, ODES `2893d935`,
hub `afca5bbd` (read-only, T18 and T20; the hub revision is unchanged from the 2026-10-18 run and is not part of the current component tuple). The tuple also
contains the action manifest `ff549082` and the governed exchange `fdc2a410`; the batch does not take them.
The batch was first run on 2026-10-18 against earlier revisions: first control plane `3755c71a`, runtime `7170da59`, verifier
`0a43a7f0`, Replay `541180fd`, Evidence Pack `63e9ee99` and ODES `304f6cc3`, then control plane `3cd17ead`, runtime `11de097c`, verifier
`f99a6543`, Replay `46e8bd7c`, Evidence Pack `4fbbd344` and ODES `e2cbc0dc` (hub `afca5bbd`). It was re-run on 2026-10-19 at the previous tuple (runtime `c4a05883`, Replay `2a7963b1`, Evidence Pack `80e24650`,
ODES `4bf12128`); the revisions above are the r10 tuple of the profile `process/security-runtime-f5b-20261016-r10.json`. The governed exchange (route C) and the orchestrator are not in the attacked set; legs
that need them are named as not covered in the module docstrings.

## Running

```
ADV_CONTROL_PLANE_DIR=... ADV_RUNTIME_DIR=... ADV_VERIFIER_DIR=... ADV_REPLAY_DIR=... ADV_EVIDENCE_PACK_DIR=... \
ADV_ODES_DIR=... ADV_HUB_DIR=... python -m pytest -p no:cacheprovider process/adversarial/tests
```

Dependencies as the component suites: `pytest==8.3.5 pydantic==2.13.5 cryptography==50.0.0`, plus `jsonschema` (the ODES package imports it; T09 and T16 need it). A test whose checkout is not named,
or is at another HEAD, **fails**; nothing skips (`ADV_ALLOW_REVISION_DRIFT=1` runs against other heads and records them).
`ADV_REPORT_DIR` receives `observations.json`: one row per scenario with its result, detail and what it does not prove.
There is no workflow for this directory yet (workflow files are outside this change); the run below is a local run.

## Conventions

- A **new** reproduced failure is a strict `xfail(raises=AssertionError)` with a neutral reason. The detail is held for the
  private channel in each repository's SECURITY.md and is not described in this repository. A strict xfail turns red when the
  behaviour changes, so a fix is noticed; a broken precondition fails outright.
- A reproduced failure that matches a **documented limit** (C0 window on the default route, F-5/F-18, SCN-D07, SCN-C16) is
  characterised by a passing test and labelled known.
- Behaviour that is outside the attacked boundary by design (for example a destination class that holds no authority state) is
  recorded as `not applicable` and listed, never hidden.
- Two tests use the harness convention D3 (run twice from fresh stores, compare normalised observations): T11 and T12.

## Status

Run of 2026-10-19 (local; Python 3.13) at the previous tuple named above (not yet repeated at the r10 tuple), without `ADV_ALLOW_REVISION_DRIFT`: **132 passed, 4 xfailed, 0 failed, 0 skipped** (136 cases), the same counts and the same four strict xfails as the run of 2026-10-18, which was made at the earlier revisions named above (ODES `e2cbc0dc` in that run). History of the runs: the first run,
against the earliest revisions, was 126 passed, 7 xfailed (133 cases); changes since: T09 and T16 now pass, T07 route B asserts the refusal,
T07 route A gained a profile-on variant (2 cases), T04 route B lists one unbound member instead of three, and T01 covers the revoked-revision rule, and T05 gained an exact-mode agreement case (the runtime policy with `target_match` exact agrees with the control plane on every spelling). Per test, the overall
classification; [`batch-1.json`](batch-1.json) carries the same table with a summary per test.

| Test | Title | Ideas | Status | Notes |
|---|---|---|---|---|
| T01 | Direct-call matrix over every destination class | D25 | prevented | non-enforcing classes listed as not applicable; a revoked revision cannot be set back |
| T02 | Non-dispatching entry points leave destinations unchanged | D25, H65, G54 | prevented | stopped reaper: decide refuses (detected only) |
| T03 | Raw-ingress canonicalization differential at acp run | A06, A01, A07 | prevented | |
| T04 | Every-field post-approval mutation completeness | A01, A02, A04, A07 | prevented | one unbound member listed with its reason (attempt label) |
| T05 | Target equivalence and prefix semantics | A02 | reproduced failure | composed route prevented; evaluator differential (xfail) |
| T06 | Adapter identity versus implementation | A03 | detected only | prevention needs adapter attestation (E6) |
| T07 | Authority ABA | B15 | reproduced failure | route A default configuration: documented default, 2 cases (xfail); the opt-in terminal-revocation profile and route B refuse it |
| T08 | Revocation against the delayed-commit destination | B09, B10, B16 | prevented | default route A window is the documented C0 limit |
| T09 | Expiry equality and offset across evaluators | B13 | prevented | all three evaluators agree at the equality instant |
| T10 | Rollback of programme-2 state | B14 | detected only | undetected without a witness (known, SCN-D07) |
| T11 | C3 chain per configuration | C22, C17, C20 | prevented | default configuration duplicates (known, F-5/F-18) |
| T12 | Stale worker resumes after lease or deadline expiry | C23, B12 | prevented | no destination fencing token (residual) |
| T13 | Real process kill at five write points of the route-A sequence | C18, C19 | prevented | process exit only, no power loss |
| T14 | Observation field matrix | H55, H56, H58 | detected only | verifier V4; consistent rewrites pass (forgery bound) |
| T15 | Profile-flag forwarding completeness | D32, A05 | prevented | regression guard for R1 finding 1 |
| T16 | Canary-secret sweep over the work directory, executor result, Replay bundle, Evidence Pack, ODES package and verifier report | D31 | prevented | all three paths clean |
| T17 | Last-unit budget race and grant multiplication | G47, G48 | prevented | multiplication characterised (known, SCN-C16) |
| T18 | Control-panel and results consistency checker | I74, I70 | detected only | read-only checker `consistency_check.py`; retained copies agree |
| T19 | Rule-revision downgrade | A05, F46 | prevented | |
| T20 | Coverage-claim audit of cited tests | I71 | detected only | 1 cited test asserts nothing about its idea (D26 row) |

`tests/test_adversarial_batch1.py` (run by CI with the rest of `tests/`) checks this table against `batch-1.json`, the plan's
batch-1 list and the test modules, without needing any component checkout.
