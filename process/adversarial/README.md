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

Final revisions, listed in [`components.json`](components.json) and checked against each checkout's HEAD at run time:
control plane `3755c71a`, runtime `7170da59`, verifier `0a43a7f0`, Replay `541180fd`, Evidence Pack `63e9ee99`, ODES `304f6cc3`,
hub `afca5bbd` (read-only, T18 and T20). The governed exchange (route C) and the orchestrator are not in the attacked set; legs
that need them are named as not covered in the module docstrings.

## Running

```
ADV_CONTROL_PLANE_DIR=... ADV_RUNTIME_DIR=... ADV_VERIFIER_DIR=... ADV_REPLAY_DIR=... ADV_EVIDENCE_PACK_DIR=... \
ADV_ODES_DIR=... ADV_HUB_DIR=... python -m pytest -p no:cacheprovider process/adversarial/tests
```

Dependencies as the component suites: `pytest==8.3.5 pydantic==2.13.5 cryptography==50.0.0`. A test whose checkout is not named,
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

Run of 2026-10-18 (local; Python 3.13): **126 passed, 7 xfailed, 0 failed, 0 skipped** (133 cases). Per test, the overall
classification; [`batch-1.json`](batch-1.json) carries the same table with a summary per test.

| Test | Title | Ideas | Status | Notes |
|---|---|---|---|---|
| T01 | Direct-call matrix over every destination class | D25 | prevented | non-enforcing classes listed as not applicable |
| T02 | Non-dispatching entry points leave destinations unchanged | D25, H65, G54 | prevented | stopped reaper: decide refuses (detected only) |
| T03 | Raw-ingress canonicalization differential at acp run | A06, A01, A07 | prevented | |
| T04 | Every-field post-approval mutation completeness | A01, A02, A04, A07 | prevented | unbound members listed with reasons |
| T05 | Target equivalence and prefix semantics | A02 | reproduced failure | composed route prevented; evaluator differential (xfail) |
| T06 | Adapter identity versus implementation | A03 | detected only | prevention needs adapter attestation (E6) |
| T07 | Authority ABA | B15 | reproduced failure | suspected defect, 3 cases (xfail); detail held for the private channel |
| T08 | Revocation against the delayed-commit destination | B09, B10, B16 | prevented | default route A window is the documented C0 limit |
| T09 | Expiry equality and offset across evaluators | B13 | reproduced failure | boundary differential at the equality instant (xfail) |
| T10 | Rollback of programme-2 state | B14 | detected only | undetected without a witness (known, SCN-D07) |
| T11 | C3 chain per configuration | C22, C17, C20 | prevented | default configuration duplicates (known, F-5/F-18) |
| T12 | Stale worker resumes after lease or deadline expiry | C23, B12 | prevented | no destination fencing token (residual) |
| T13 | Real process kill at every persistence boundary | C18, C19 | prevented | process exit only, no power loss |
| T14 | Observation field matrix | H55, H56, H58 | detected only | verifier V4; consistent rewrites pass (forgery bound) |
| T15 | Profile-flag forwarding completeness | D32, A05 | prevented | regression guard for R1 finding 1 |
| T16 | Canary-secret sweep over every artifact | D31 | reproduced failure | suspected defect, 1 path (xfail); detail held for the private channel |
| T17 | Last-unit budget race and grant multiplication | G47, G48 | prevented | multiplication characterised (known, SCN-C16) |
| T18 | Control-panel and results consistency checker | I74, I70 | detected only | read-only checker `consistency_check.py`; retained copies agree |
| T19 | Rule-revision downgrade | A05, F46 | prevented | |
| T20 | Coverage-claim audit of cited tests | I71 | detected only | 1 cited test asserts nothing about its idea (D26 row) |

`tests/test_adversarial_batch1.py` (run by CI with the rest of `tests/`) checks this table against `batch-1.json`, the plan's
batch-1 list and the test modules, without needing any component checkout.
