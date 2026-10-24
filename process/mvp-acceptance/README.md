# mvp-acceptance (proposed)

An independently owned Qualification job that runs the complete selected MVP route at the exact candidate tuple and applies a gate.
Everything here is **proposed**: Qualification owns the oracle and every verdict, the builder only proposes. Nothing is an acceptance, a
release decision or a production claim; release stays HOLD, and the gate verdict document says `authorizes: false`.

| File | Role |
|---|---|
| [`candidate-identity.inputs.json`](candidate-identity.inputs.json) | The only source of the tuple: eight components, each a full 40-hex sha. Exchange is listed only under `excluded_components`. |
| [`mandatory-battery.proposed.v1.json`](mandatory-battery.proposed.v1.json) | The frozen-candidate list of mandatory tests (50) and the skip rule. |
| [`gate-expectations.proposed.v1.json`](gate-expectations.proposed.v1.json) | Exact Verifier dispositions and environment floor. |
| [`candidate-commitment.proposed.v1.json`](candidate-commitment.proposed.v1.json) | Versioned qualification candidate: sha256 of the battery, mapping, gate expectations, tuple, environment profile, gate, workflow and every mandatory test source. |
| [`environment-profile.proposed.v1.json`](environment-profile.proposed.v1.json) | The supported environment record: CPython 3.13, Yama `ptrace_scope >= 1`, required hub record checks. |
| [`mvp-applicability.proposed.v1.json`](mvp-applicability.proposed.v1.json) | Route C (Exchange) EXCLUDED and NOT INVOKED, with the checks that verify it. |
| [`../../.github/workflows/mvp-acceptance.yml`](../../.github/workflows/mvp-acceptance.yml) | Dispatch-only workflow (Python 3.13, pydantic 2.13.5 from the hash lock). |
| [`../../tools/mvp_acceptance_gate.py`](../../tools/mvp_acceptance_gate.py) | `resolve`, `verify-checkouts`, `gate` (standard library only); tests in `tests/test_mvp_acceptance_gate.py`. |

## What the job runs

Real claim provisioning (journal mode, operation identity), actual route B synthetic execution, grant and approval revocation negatives
(NC1), lost-acknowledgement and duplicate-operation negatives (NC2, NC3, and the ruling 4 assertions), Replay and Evidence Pack
reconstruction, the pinned Verifier, custody and tamper checks (NC5, NC6), the trusted-host ingress boundary (NC4: ingress as a dedicated non-root uid, client as another) and the
route C exclusion checks. The chain, negatives and Verifier come from `suites/mvp-chain` (its expectations v3 are the oracle and are not
changed); `suites/mvp-d2-route-b` and `suites/mvp-d09` are not in this job because they hard-code the Runtime sha and one of them fails by
design; the same behaviours are exercised here by mvp-chain.

## Tuple

`tools/mvp_acceptance_gate.py resolve` reads the identity file, applies per-component `workflow_dispatch` inputs (each validated as 40-hex lower
case; branches, tags and short shas are refused), and writes the resolved pin file the suites read plus `tuple-resolved.json`. `verify-checkouts`
requires each checkout to be at exactly its sha and pristine before any test runs, and the gate compares the heads the suite saw. The
identity file names the final PROVISIONAL, UNQUALIFIED tuple (Control Plane `7a4bcd40`, Runtime `c5e97e87` (post-F3), Replay `40012b8c`, Evidence Pack `7b9511f2`, ODES `1a5e1d30`, Verifier `c0b8ba1f`, Action Manifest `fa170815`, hub `5b76c58a`); it mirrors `process/mvp-chain/tuple-pin.proposed.json`. A different component sha is a `*_revision` input for one run, or a changed identity value and therefore a new candidate (new commitment).

## Gate verdicts

`INCOMPLETE` over `REJECT` over `ACCEPT`.

* **Zero unexplained skips inside the mandatory battery.** A listed test that is skipped (including xfail), not discovered (absent from
  `pytest --collect-only`), not executed (absent from the junit report), errored, or whose oracle row is `BLOCKED` or `NOT RUN` makes the
  verdict `INCOMPLETE`. `NOT APPLICABLE` counts only when the row id is listed under `declared_not_applicable` with a justification (empty
  today); any other `NOT APPLICABLE` is `INCOMPLETE`. A declared `NOT APPLICABLE` is a different thing from a skip. Tests outside the list
  (historical suites, KL-01) are not required to be skip-free.
* **Exact Verifier dispositions** (G-07), re-read from the retained report bytes (sha256 must match the run's record): run B exits 3
  (abstain), 28 checks, 27 confirmed, 1 could-not-check (`v4.ledger.rows-agree-with-attempts`), 0 refuted; V4 has 4 confirmed, 1 abstained
  and 2 not applicable (`v4.ledger.acknowledged-attempts-have-rows`, `v4.ledger.observations-agree`). Run A (no ledger) exits 3 with 29 checks,
  22 confirmed, 7 could-not-check (all `input_absent`). Nothing is asserted as "all other V4 checks pass".
* A changed expectation v1, v2 or v3 is a `REJECT` (G-02); the gate never edits one.
* A `FAIL` row is a `REJECT`; the job fails unless the gate says `ACCEPT`.

The oracle's own FAIL rows are never softened by the gate. Whether any row fails at the final tuple (for example NC1-04, approval revocation terminality, which failed at the pre-F3 Runtime `ec728da6`) is a result of a run, not asserted here; no dispatched run exists yet.

## Candidate commitment, environment record, Python 3.13 (Architect rulings #2 item 6)

All of these stay **PROPOSED** pending independent Qualification acceptance and freeze (target 2026-10-27).

* **Commitment (G-12, G-13).** `candidate-commitment.proposed.v1.json` lists the sha256 of: ALL files (not only `.py`) under `suites/mvp-chain` and
  `suites/mvp-applicability`; the transitive closure of the local modules they import, computed by static import analysis (this reaches
  `suites/operation-identity/_oi_flow.py` and `tools/pristine_checkout.py`); `pytest.ini`; the lock files the workflow references; EVERY file directly in each `sys.path` directory (`suites/`, `suites/operation-identity/`, `tools/`; at the repository root every importable file, which `python -m pytest` puts first on `sys.path`) and the `__init__` of each package directory there, so a planted `tools/yaml.py`, `suites/jsonschema.py`, `sitecustomize.py` or package is an uncommitted file (FAIL), not a shadowed import; every file of
  `process/mvp-chain` and `process/mvp-acceptance` (candidate tuple, battery, mapping, gate expectations, environment profile); the gate tool and
  the workflow. It also records files that must stay absent (a root or `suites/` `conftest.py`, `tox.ini`, `setup.cfg`, `pyproject.toml`).
  Symbolic links anywhere in or above the committed set are refused, both when the commitment is built and by the gate. The sha256 of the
  commitment file must be supplied from outside this checkout (`candidate_commitment_sha256`); without it the verdict is INCOMPLETE. A changed,
  added or removed file, or a planted file that must be absent, is a FAIL, and a collected test that is not in the committed battery (mandatory,
  or the committed non-mandatory KL-01) is INCOMPLETE. A later change is a new file (`...v2.json`) and a new candidate; `python
  tools/mvp_acceptance_gate.py commit` writes it. **Inherent limit:** the gate and the workflow that evaluate the commitment come from the same
  checkout, so a changed gate could report PASS; an independent reviewer must pin the commitment hash and the gate code outside the checkout.
  Not covered: component checkouts (pinned by sha), the runner image, site-packages (locked installs) and the hub environment record (captured in the run, below).
* **Environment record (G-11).** The suite runs the ingress per the approved profile and the hub environment record is **captured in the run**
  against that very process; there is no pre-committed record and no `environment_record*` workflow input any more. In the workflow the Provision
  step creates the dedicated users `mvp-ingress` and `mvp-client` (own primary groups) and the group `mvp-ipc` (exactly those two members), makes the
  checkouts readable and sets `kernel.yama.ptrace_scope=1` with `sudo sysctl` (absent Yama is BLOCKED/INCOMPLETE, never a weaker run). `_ingress.py`
  then starts the ingress as `mvp-ingress` (non-root, no supplementary groups) with a 0660 socket in a SEPARATE setgid IPC directory (group `mvp-ipc`,
  2751: others may traverse but not list or write, so the outsider probe is denied by the socket's own mode and group) the client traverses, and its 0700 state directory elsewhere; the client runs as `mvp-client` with the `mvp-ipc` group; owner-side
  observations are made as the ingress uid. The hub script `tools/mvp_env_record/capture_env_record.py` (hub PR #219, hub 3fff3dfb; script bytes identical to 050dcd67/0e2b52a0) is run as root against the live
  process with a run-bound `--label` (`hosted-runner acceptance run <run_id>, profile=approved`; required, the gate checks it names this run), the actual uids, gids, pid, database, ledger, tuple pins, source pins and the tuple's action-manifest file, and writes
  `mvp-chain/artifacts/environment-record.json` unchanged. A gate-side **envelope** (`environment-record.envelope.json`) binds `run_id` and
  `qualification_sha` (supplied by the workflow as `MVP_RUN_ID` and `MVP_QUALIFICATION_SHA`; the hub script has no flags for them and its deterministic
  record cannot hold a later run id), the record's own `record_sha256`, the sha256 of the record file, of the capture script and of the environment profile.
  **Pin:** the sha256 of the capture script (`environment-profile.proposed.v1.json`, `capture_script`) is committed because #219 is still moving: the
  script in the hub checkout at the tuple sha and the one the envelope names must both have exactly those bytes, otherwise FAIL (a moved script is a new
  candidate); a tuple hub sha that predates the script is INCOMPLETE, so a run needs `hub_revision` set to a sha that contains it. Required: valid
  `record_sha256`; `overall` consistent with its checks; PASS for all 31 check ids the hub script emits (reconciled against the script, including
  `ipc.socket_mode_owner_group`, `isolation.ingress_capabilities`, `ipc.directory_separate_and_protected` and `qualification.outsider_denied_socket`);
  CPython 3.13 equal to the suite's interpreter; `kernel.yama.ptrace_scope >= 1`; socket group policy `dedicated`, mode 0660, in a directory that is not
  the state directory; non-root ingress; no relaxed requirement; `ingress_source_sha256` equal to the hub files at the tuple sha; the manifest digest
  equal to the tuple's manifest file; every component pin equal to the tuple sha; and the identities (ingress uid and gid, client uid and gid, IPC gid,
  non-root) the suite observed equal to those in the record. **Developer opt-out:** `MVP_INGRESS_PROFILE=developer-optout` (never set by the
  workflow) keeps the old local behaviour (root ingress, socket mode 666, client uid 65534, no record); the suite records `profile=developer-optout`
  and the gate verdict is INCOMPLETE. A FAIL is a REJECT; BLOCKED, a missing record, envelope or field, or Yama absent is INCOMPLETE.
* **Interpreters.** The probe client that attacks the ingress runs under the system `/usr/bin/python3 -I` (an isolated, unprivileged interpreter), while the
  ingress and the capture script run under the workflow's CPython 3.13. The interpreter-match checks (`python.interpreter_matches_ingress`, the record's
  `python.version` equal to the suite's interpreter, `--require-python 3.13`) apply to the ingress and the suite only, never to the probe client.
  `hub_revision` must name a hub sha whose `tools/mvp_env_record/capture_env_record.py` has the pinned sha256; the workflow checks this right after the hub
  checkout (`preflight-hub`) and exits 1 otherwise. `qualification_revision` must be blank or equal the workflow commit.
* **Python (G-04, G-04b).** The workflow uses 3.13, asserts it, and the gate (`--require-python 3.13`) refuses to run its verdict as qualifying on
  any other interpreter. A Python 3.12 result is supplementary and cannot qualify the 3.13 profile. `mvp-chain.yml` on main is not changed.
* **Pending rows (G-14).** The new origin-rule negative mutation expectations for NC4-03 are NOT battery rows. `pending_rows` holds a clearly
  marked placeholder with no rows; they are added only after Qualification freezes the corrected NC4-03 predicate, and the gate refuses a
  placeholder that carries rows.

## Binding, anchoring and limits

* **Run binding.** `resolve` records the Qualification commit actually run (`git rev-parse HEAD` after checkout) and a fresh `run_id`
  (exported as `MVP_RUN_ID`). `results.json`, `observations.json`, each exclusion observation, the ingress module dump and each junit
  `testsuite` name must carry that run id, and the gate fails closed (INCOMPLETE) otherwise. The Verifier exit code and overall are
  re-derived from the retained report bytes; a malformed report is INCOMPLETE, never a crash. The artifact is named with the Qualification
  commit. `qualification_revision` is validated as 40-hex before it is used as a checkout ref, and the pristine check includes ignored files.
* **Frozen-file anchor.** The workflow reads the git blob ids of expectations v1-v3 and `test_scn_d09.py` on `main` through the REST API
  and the gate (G-02c) requires this checkout's blobs to be identical, in addition to the recorded sha256 values. Limit: that proves
  identity with the content `main` holds now, not an owner approval; protecting `main` (CODEOWNERS or branch rules) is what freezes it.
* **Exchange exclusion scope (AP-06).** Covered: the pytest processes that run the battery and the pinned ingress server process (its loaded
  modules are written at exit by `suites/mvp-applicability/plugin/ingress_probe/sitecustomize.py`, which `suites/mvp-chain/_ingress.py` puts on
  the server's PYTHONPATH; observation only). Not covered: other processes the battery starts, such as the Verifier CLI.
* **Out of scope observation.** `mvp-chain.yml` on main sets up Python 3.12; this job uses 3.13 as ruling 8 requires.

## Not run here

The workflow has not been dispatched from this change; the gate logic is covered by `tests/test_mvp_acceptance_gate.py` on synthetic
artifacts, and the ruling 4 and applicability tests were checked for syntax and (for the applicability tests) against the pinned hub
ingress sources.
