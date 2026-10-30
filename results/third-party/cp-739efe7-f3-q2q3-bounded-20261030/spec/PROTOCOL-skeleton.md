# OCS-F3-Q2Q3-BOUNDED-v1 - bounded Q2/Q3 qualification of Control Plane 739efe7 (work package OCS-F3-Q240-BOUNDED-QUALIFICATION)

SKELETON, COMMON PART ONLY (Worker A). Per-case sections 7.x are appended by the lead from the case workers' specs. Status: DRAFT until the lead freezes it; frozen means `protocol.sha256` written BEFORE any case execution, and this file does not contain its own hash. Bracketed `[LEAD]` items are filled at freeze.

## 0. Identity
- Protocol id: `OCS-F3-Q2Q3-BOUNDED` ; version `v1` ; short name `BOUNDED-v1`.
- Cases (exactly five, no others, none added after results are seen): FC-H1, FC-H2, FC-H3, FXE-JOINT, N-CLAIM-JOINT.
- Specification source: hub `docs/f3-q240-closeout/08-q2q3-class-a-reachability-dossier-2026-10-30.md` section 7 (case specs), section 5 (reachability matrix), section 8 (impossibility findings); hub `07-f3-architectural-technical-disposition-2026-10-30.md` section 0 (operative Q2/Q3 OPEN). Hub `main` at freeze: `07aa90553da41305bd38fd54447b3fbc29ed6cbc` (re-verify at freeze).
- Prior frozen-protocol convention: `results/third-party/cp-739efe7-f3-q2q3-isolation-20261030/PROTOCOL-D1-v1.md` (expectations stated before runs; deviations are adverse findings, never rescored).

## 1. Standing contract position (restated, not changed by this protocol)
- Registry record 12 (Class A) controls: Q2 (A25(a) scope.authority_domain) and Q3 (A25(e) host_profile_digest and effective_profile_digest) are **OPEN - required isolation not fully demonstrated**.
- Original F3-A: **FAIL** under the frozen oracle (23 failed assertions); preserved, never relabelled.
- Successor F3-A (Registry `06`/`11`, OCS-F3A-DEV-PE-1-INTERPRETATION/1.0, human adoption PENDING): conditional scoped technical PASS only, not an acceptance.
- This protocol adds bounded evidence only. No result of it re-scores D-1, D-2, #242 or the original run, discharges Q2/Q3, changes record 12, or adopts anything. Final Tier 1 DEFERRED, NOT WAIVED; publication/release/production HOLD.

## 2. Provenance statement (mandatory in README.md and limitations.md)
Protocol author, case workers, executing runner and any reviewer are one session lineage (producer session `session_01VFvQdn8XjieqzRUfpEtpgy`, lead qualification builder and its subordinate workers), same model family as the builder and oracle authors, with fixtures reused from the original qualifier harness (disclosed shared tooling). **No organizational independence is claimed.** A fresh process or agent does not establish independence. Placement under `results/third-party/` proves nothing about independence or acceptance. The result is a bounded technical record; formal acceptance is reserved to the Architect/competent authority. Predictions in this protocol are not blind (informed by D-1 and the dossier).

## 3. Frozen subject and source identities, verified BEFORE the first run
Record every command output verbatim into `source-identity.json` and `raw/preflight/`. Any mismatch = STOP (section 12); no run starts.

| Identity | Expected | Verification command |
|---|---|---|
| Control Plane commit | `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69` | `git -C <cp-git-repo> rev-parse 739efe7d^{commit}` |
| CP root tree | `1e7a7555eb3a956fcd2db21d3eb944169d0f7783` | `git -C <cp-git-repo> rev-parse 739efe7d^{tree}` |
| CP src tree | `d248bde478ae3f2ce050db4637f0c1203066e906` | `git -C <cp-git-repo> rev-parse 739efe7d:src` |
| Pristine copy == commit | no diff output, exit 0 | `git -C <cp-git-repo> archive 739efe7d | tar -x -C "$SCRATCH/arch" && diff -r "$SCRATCH/arch" "$CP_ROOT"` (pristine copy has no `.git`) |
| Pristine content hash (before AND after all runs, must be equal) | `d468827e822b5533b4238b9cd352b06ba6fc7fa36d7cbe1177d09972e0721e11` (value from D-1 ENV-MANIFEST; the command below was re-run read-only by Worker A on `/tmp/claude-0/work/src/cp-739efe7` and reproduces it) | `cd "$CP_ROOT" && find . -type f -print0 \| LC_ALL=C sort -z \| xargs -0 sha256sum \| sha256sum` |
| Registry pin HEAD | `a40fe755e2384a99c37016fa9ad59396f1835900` | `git -C "$REG_PIN_DIR" rev-parse HEAD` |
| Registry pin detached and clean | `HEAD` detached; porcelain empty | `git -C "$REG_PIN_DIR" symbolic-ref -q HEAD; echo $?` (expect exit 1) ; `git -C "$REG_PIN_DIR" status --porcelain` (expect empty) |
| Registry main (contract reading only, not executed) | `6b96a9a658923954433dc1a4c13626fa5145b9c7` | `git -C <registry-repo> rev-parse origin/main` |
| Constitution | convention `dcdbe3b76843d672ca3cfb1f000124ecd78ed03c`; baseline `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` | `git -C <constitution-repo> cat-file -t <sha>` (each prints `commit`) and `rev-parse` of each |
| Hub | `main` `07aa90553da41305bd38fd54447b3fbc29ed6cbc` at draft time `[LEAD: re-verify at freeze]` | `git -C <hub> rev-parse HEAD` |
| Runtime | Python 3.11.18 | `"$PY" -V` |

Not transferable: no result applies to `8616d5f`, CP `main` (`b19c47dd`), Registry main, or Python 3.12. The pristine tree is read-only; `PYTHONDONTWRITEBYTECODE=1` always.

## 4. Contract revisions read (hashes of the exact blobs recorded in `source-identity.json`)
Registry `6b96a9a658923954433dc1a4c13626fa5145b9c7`, directory `docs/family-migration/final-three/`: `02-architect-authorization-and-contract-freeze-2026-10-29.md`, `03-f3-qualification-expectations-F3A-F3B-2026-10-29.md`, `06-f3a-dev-pe-1-interpretation-v1.0-2026-10-29.md`, `11-architect-successor-confirmation-decision-record-2026-10-30.md`, `12-f3-closeout-coverage-and-adoption-status-2026-10-30.md`, `13-f3-acceptance-readiness-record-2026-10-30.md`, `14-f3-final-engineering-closeout-2026-10-30.md`. Record each as `git -C <registry-repo> rev-parse origin/main:docs/family-migration/final-three/<file>` (blob id) plus `git ... show origin/main:<path> | sha256sum`. Constitution at `dcdbe3b` / `1c2e920`. Hub records: dossier `08-...`, `07-f3-architectural-technical-disposition-...`, `07-final-technical-closeout-record-...`, `06-final-custody-and-disposition-...` (sha256 each).

## 5. Environment capture (before the first run, into `environment.json` and `raw/preflight/`)
```
"$PY" -V ; "$PY" -m pip freeze            # must contain pydantic==2.14.2 PyNaCl==1.6.2 pytest==9.2.0 cryptography==50.0.2
"$PY" -c "import pydantic,nacl,pytest,cryptography,sys;print(pydantic.VERSION,nacl.__version__,pytest.__version__,cryptography.__version__,sys.executable)"
uname -a ; date -u +%FT%TZ ; env | grep -E '^(OCS_|PYTHON|BQ_|D1_|F3_)' | sort
sha256sum "$PY"
```
Required values: Python 3.11.18, pydantic 2.14.2, PyNaCl 1.6.2, pytest 9.2.0, cryptography 50.0.2, `OCS_REQUIRE_REGISTRY_PIN=1`, `OCS_REGISTRY_PIN_DIR=$REG_PIN_DIR`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=$CP_ROOT/src`. A preflight observation also records `acp.__file__` (the imported Control Plane module must resolve under `$CP_ROOT/src`) as D-1 `PREFLIGHT` did.

## 6. Harness file inventory (hashes written at freeze; any change after freeze is an amendment, section 14)
| File | sha256 | Note |
|---|---|---|
| `harness/d1_lib.py` | `5ec947ba028fdd9aa5024215881103d8ac55c2ffb5f7049cfd70a4f76ac3bddc` | reused UNMODIFIED from D-1 (12459 bytes); Worker A confirmed `/tmp/claude-0/work/bq/harness/d1_lib.py` matches |
| `harness/orig_harness.py` | `a51474128d8094932c91b3dd95b95fd751920b12b61499ab06acfbdac8727b0b` | shared tooling, byte-identical to `test_f3a_independent.post-AMEND4.py` (90949 bytes); matches `/tmp/claude-0/work/bq/harness/` |
| `harness/<new lib>` `[LEAD name, e.g. bq_lib.py]` | `[LEAD at freeze]` | new fixtures (class-unreadable world, claim helper, evidence-row writer) |
| `harness/<new test files>` `[LEAD, one or more test_bq_*.py]` | `[LEAD at freeze]` | the five cases' frozen assertion inventories |
| `harness/run_bq.sh` | `[LEAD at freeze]` | section 8 |
| `harness/bq_env_check.sh` / preflight script `[LEAD]` | `[LEAD at freeze]` | commands of sections 3 and 5 |
New files may import `d1_lib` / `orig_harness` but must not edit them. `test_d1.py`, `probe_d1.py`, `run_d1.sh` and D-1 mutant diffs are NOT part of this protocol's instruments (no mutants are run, section 10).

## 7. Cases (per-case sections appended by the lead)
Each case section MUST contain: world construction; control(s) and their required outcomes; validity preconditions (a failing one yields BLOCKED); the complete frozen assertion inventory with ids `<CASE>.<nn>`, each stating kind, expected value, and observation method; predicted outcome; claim permitted if all pass; what the case cannot establish. Case order of execution: fixed `[LEAD]` and recorded.
- 7.1 FC-H1 host-digest, claim leg `[LEAD appends]`
- 7.2 FC-H2 class-unreadable masked-host, execute `[LEAD appends]`
- 7.3 FC-H3 unmasked-host contrast, bounded control only `[LEAD appends]`
- 7.4 FXE-JOINT effective-profile joint transition (freshness extension), execute `[LEAD appends]`
- 7.5 N-CLAIM-JOINT authority-domain natural joint claim refusal `[LEAD appends]`

Common instrument (reused from D-1): complementary binding diff = dotted-leaf diff between the PERSISTED decision binding and the binding the LIVE world genuinely mints for the same proposal (`d1_lib.live_binding`, `split_diff`), split into base diff (outside `runtime_authority.effective_configuration`) and ECB diff (inside). Attribution of `authorization_binding_changed` (or the claim `PermissionError`) to a member comes ONLY from the complementary diff, never from the refusal code (the comparison `current != persisted.binding` is generic). The candidate's `configuration_binding_status` is evidence only, never the oracle; the oracle for member content is the harness's own recomputation (`own_commit`, `H.my_digest`).

## 8. Run command (parameterized; no worker home paths)
`harness/run_bq.sh` (modelled on D-1 `run_d1.sh`; body to be frozen exactly as below, `[LEAD]` may only fill the test file names):
```bash
#!/usr/bin/env bash
# usage: run_bq.sh <label> <cp-root> <reg-pin-dir> <python> <outdir> [pytest -k expr]
# <outdir> is the evidence root for this run; run_bq.sh is run from any cwd; harness dir = dir of this script.
set -u
L=$1; CP=$2; REG=$3; PY=$4; OUT=$5; SEL=${6:-}
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$OUT/helper" "$OUT/basetemp-parent"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$CP/src" \
  OCS_REGISTRY_PIN_DIR="$REG" OCS_REQUIRE_REGISTRY_PIN=1 \
  BQ_PROTOCOL=OCS-F3-Q2Q3-BOUNDED-v1 BQ_CP_ROOT="$CP" BQ_LABEL="$L" BQ_EVIDENCE_DIR="$OUT" \
  D1_CP_ROOT="$CP" D1_LABEL="$L" D1_EVIDENCE_DIR="$OUT" F3_EVIDENCE_DIR="$OUT/helper"   # D1_*/F3_* are read by the reused d1_lib/orig_harness
ARGS=(); if [ -n "$SEL" ]; then ARGS=(-k "$SEL"); fi
cd "$OUT"
date -u +%FT%TZ > "$OUT/start.txt"
"$PY" -I -m pytest -p no:cacheprovider -q -rA --junitxml="$OUT/junit.xml" --basetemp="$OUT/basetemp-parent/bt" \
  "${ARGS[@]}" "$HERE"/test_bq*.py > "$OUT/stdout.txt" 2> "$OUT/stderr.txt"
echo "exit=$?" >> "$OUT/stdout.txt"
date -u +%FT%TZ > "$OUT/end.txt"
tail -15 "$OUT/stdout.txt"
```
`[LEAD]` check: whether `-I` is compatible with `PYTHONPATH`-based import of the subject (the `-I` flag IGNORES `PYTHONPATH`; if the harness imports the subject via `PYTHONPATH` the `-I` must be dropped, as D-1 did not use it). Worker A did not execute this. Use of `-p no:cacheprovider -q -rA` and `--junitxml` is mandatory. Run-ids: `run1`, `run2` (section 9). Environment capture (section 5) is executed immediately before run1 and again after run2.

## 9. Deterministic rerun rule
Exactly one rerun of the full frozen file set: run1, then run2, same instruments, same command, same environment, fresh `--basetemp`, no code or expectation edits in between, no selective rerun, no third run. Run2 is determinism evidence, not a retry: run1 results are never replaced. Comparison: per-assertion `(case_id, assertion_id, result)` vectors and per-case destination call counts, journal row counts and complementary-diff leaf sets must be identical; timestamps, tmp paths, random ids and signatures are ignored. Any divergence is recorded as an ADVERSE FINDING "nondeterministic" and the affected case is scored by the worse of the two runs (precedence FAIL > BLOCKED > PASS; NOT EXECUTED only if neither run executed it). If run1 aborts before executing a case (collection/import error, runner crash), that case is BLOCKED or NOT EXECUTED per section 10; the abort is not repaired in place (section 14). Run2 may still be executed once to the same set.

## 10. Scoring rule
Each case receives exactly one of: **PASS / FAIL / BLOCKED / NOT EXECUTED**.
- **PASS**: the case ran in the run(s) per section 9, every validity precondition and control held, AND every assertion in its frozen inventory executed and passed. A single non-passing or unexecuted assertion denies PASS. There is no partial PASS and no PASS for an unexecuted assertion.
- **FAIL**: preconditions and controls held (the case is interpretable) and at least one frozen assertion failed or the observed outcome contradicts the frozen prediction. Preserve the counterexample verbatim; it is an adverse finding, never revised or rescored; an implementation defect observed stops that case (no repair).
- **BLOCKED**: a validity precondition or control did not hold (examples: control claim/execute did not occur exactly once; live-world diff not as required; masking not in effect so the host edit changed the effective commitment; Registry/adapter refused the fixture value; a mandatory guard would have to be disabled to proceed; instrument error before the first assertion). The case is NOT interpreted: neither PASS nor FAIL is inferred for the product; record the failed precondition, its raw output and the stop reason.
- **NOT EXECUTED**: no assertion of the case ran (not collected, skipped, not reached after a section 12 stop, or deselected). Skips and xfails count as NOT EXECUTED, never PASS.
Assertion-level results use the same words except an individual assertion is PASS/FAIL/BLOCKED/NOT EXECUTED. No case result is aggregated into a Q2/Q3 or F3-A verdict by this protocol; the closing statement says only per-case results and per-dimension statements (section 11).

## 11. Six separately recorded dimensions
Each case record states, per dimension, one of: ESTABLISHED (case PASS and dimension is within the "can" column), NOT ESTABLISHED (case FAIL/BLOCKED/NOT EXECUTED, or dimension outside the case's reach), or NOT APPLICABLE. Dimensions are never merged into one verdict.
1. **Functional correctness**: the live world mints/accepts/executes/claims correctly under the unperturbed control; member values equal the harness's independent recomputation.
2. **Member sensitivity**: a change of the stated member changes the ECB digest and that member's leaf, shown by the complementary diff (and which other leaves moved).
3. **Guard-order evidence**: which mandatory guard fired first, and whether the ECB comparison was consulted at all (observed refusal reasons/exception text, not code alone).
4. **End-to-end refusal**: the leg actually fails closed with its contract-defined outcome and the destination is untouched (execute: durable `EffectTimeRefusal` `authorization_binding_changed`, no attempt row; claim, successor semantics: `PermissionError`, no claim, no `EffectTimeRefusal`).
5. **Independent isolation**: Record 12 Class A sense - the member alone differs (base diff empty, ECB diff exactly `{digest, member leaf}`) AND the refusal is end-to-end.
6. **Contract coverage**: which interface leg(s), family(ies) and contract reading the case touches.

| Case | 1 Functional | 2 Member sensitivity | 3 Guard order | 4 End-to-end refusal | 5 Independent isolation | 6 Contract coverage |
|---|---|---|---|---|---|---|
| FC-H1 (host, claim leg, F5 class-age masked-host) | CAN: control claim issues exactly once; host digest = independent commitment | CAN: host member, ECB diff exactly `{digest, members.host_profile_digest}`, base diff empty | CAN: approval/base guards pass, ECB comparison is the refuser | CAN: claim `PermissionError`, no claim, no `EffectTimeRefusal` (successor 06/11 reading only) | CAN, single pathway: masked-host, host member only, claim leg only, one family. CANNOT: unmasked host edits, other families, execute, pin-export; does not discharge Q3 | CAN: claim leg for host member on F5 class-age. CANNOT: execute (D-1 did), pin-export, frozen-literal claim reading (see section 15 item 3) |
| FC-H2 (host, class-unreadable masked-host, execute) | CAN: control executes once; digest recomputes | CAN: host member, same exact diff form | CAN | CAN: execute durable refusal, no attempt row, destination untouched | CAN, single pathway: second family, masked-host, execute only. CANNOT: claim leg, unmasked, pin-export; second fixture counts for "two" only under reading R2 (dossier section 3), UNVERIFIED | CAN: execute leg, class-unreadable family. CANNOT: other families |
| FC-H3 (unmasked-host contrast) | CAN: control executes; unmasked edit changes effective/catalogue/approval commitment as measured | CANNOT as isolation: moves more than the host member (effective digest, catalogue, approval commitment); records which leaves moved | CAN: shows guard-first (`runtime_authority_approval_mismatch`) without re-issue, or joint with re-issue; whichever is frozen per sub-run | CAN only to its boundary: fail-closed by an earlier guard, no host-member attribution | CANNOT, never isolating. Bounded control to distinguish the masked-host mechanism from the unmasked one | CAN: documents the masked-host limit alongside; no interface coverage claim |
| FXE-JOINT (effective profile, freshness-extension, execute) | CAN: eff digest = independent commitment = `catalogue_digest` | PARTIAL, JOINT: base diff exactly `{approval_commitment, catalogue_digest}`, ECB diff exactly `{digest, effective_profile_digest}`; CANNOT show effective member alone | CAN: control C1 (approval not re-issued) shows approval-mismatch guard first | CAN: execute durable refusal after re-issue (joint) | **CANNOT: JOINT evidence, NO independent isolation** (by construction I1-I4 effective moves with catalogue/approval) | CAN: execute, class-age freshness-extension only. CANNOT: claim, pin-export, live derivation sensitivity of the effective digest alone |
| N-CLAIM-JOINT (authority_domain, natural, claim) | CAN: domain-world control claim issues; member = manifest domain | PARTIAL, JOINT: base diff `{manifest_digest, proposal_commitment}` (expected), ECB side per case spec; CANNOT isolate the leaf | CAN: shows the ECB is reached on the claim leg when approvals are re-issued | CAN: claim `PermissionError`, no claim, no `EffectTimeRefusal` (successor reading) | **CANNOT: JOINT evidence, NO independent isolation** | CAN: claim leg, F4 fixture, natural joint. CANNOT: pin-export, graft, seam-patch, member-specific refusal |
General: guard-first refusal shows fail-closed only up to its boundary (the refusing guard); it says nothing about the later ECB member. A PASS of a case never upgrades component evidence to end-to-end, and no case here upgrades any member to "isolated" other than FC-H1/FC-H2 for host_profile_digest on their single masked-host pathways.

## 12. Failure conditions and stop conditions
Case-level FAIL conditions: any frozen assertion fails; the refusal code/reasons differ from the frozen expectation (e.g. extra or missing reason); a claim/execute that was expected to be refused is acknowledged/issued; a destination call count differs; an unexpected durable row appears (`EffectTimeRefusal` on a claim leg; an attempt row on a refused execute); complementary diff leaf set differs from the frozen set; a control that is part of the assertion inventory fails while its precondition role held.
Run-level STOP (no further case executes; remaining cases NOT EXECUTED; record why): (a) any source/identity/environment check of sections 3 or 5 fails; (b) pristine content hash changes during the run; (c) a mandatory guard would have to be disabled, patched or bypassed to proceed; (d) any attempt to reach network, a paid call or an external effect is observed; (e) the destination records a call where a refusal was frozen (kept as a FAIL counterexample, then that case stops); (f) disk/runner failure losing evidence rows. Case-level stop: implementation defect observed - preserve verbatim, stop that case, do not repair. A stopped case that already executed assertions is scored per section 10 on what ran (never PASS).

## 13. Exclusions (binding on every case)
No guard bypass, disabling or patching of any subject function, constant or seam (no seam-patch; N-EXEC-PATCH withdrawn); no source or mutant edits of the subject and no mutant runs; no direct store writes to a decision, journal or authorization store (no grafts, no resealing, no forged or re-signed persisted member); the only signed material is what production or the disclosed fixtures sign (no signature forgery, no key/signature tampering); approval re-issue only via the supported host duty (`bind_approval` as in D-1 Q3-E2); no external effects, no network access, no paid or production calls (destination is the in-process recording stub); no pin-export cases, no graft cases (N-PIN-GRAFT, N-CLAIM-GRAFT), no F4-dedicated host/effective persisted perturbation, no policy-composition/revocation/anchor workflows; only the five named cases; no case, assertion, control or expectation is added, removed or reworded after any result is seen; harness-created scratch stores under `--basetemp` are permitted only as the fixtures' normal construction; the pristine subject tree and Registry pin are never written to.

## 14. Amendments
No change to any expected outcome, assertion, precondition or case set after the first run starts. A harness defect or a needed correction requires a successor protocol `OCS-F3-Q2Q3-BOUNDED-v2` (new hash, new freeze time, new evidence directory or clearly labelled subdirectory); the v1 protocol, its hash, raw outputs and results are preserved unedited and are never overwritten or rescored. Pre-freeze exploratory runs, if any, live under `raw/probe/`, are not evidence of PASS and are listed in `limitations.md`. `amendments/` is not created; a v2 is the only correction route.

## 15. DISCREPANCIES and contract points the case writers must know
1. **Dossier section numbering.** The directive points to dossier sections 5-8 for the five cases. The case specs are in dossier **section 7** (FC-H1/H2/H3 and N-CLAIM-JOINT under "REACHABLE cases" and "Non-natural sensitivity cases"; FXE-JOINT under "GUARD-FIRST / JOINT-ONLY cases"); section 5 is the reachability matrix, section 6 the evidence crosswalk, section 8 the impossibility findings.
2. **N-CLAIM-JOINT is filed under a "non-natural" heading in dossier section 7 but is itself labelled "(natural)".** It is the natural, supported-route case (domain Y world, approvals re-issued); the grafts (N-PIN-GRAFT, N-CLAIM-GRAFT) and seam-patch are NOT among the five. The dossier states only the base diff `{manifest_digest, proposal_commitment}` and `PermissionError`, no claim; the ECB diff expectation (by analogy with D-1 Q2-A2(ii): `{digest, members.scope.authority_domain}`) and the exact exception text must be taken from the case worker's source reading and frozen before running. Dossier confidence for this claim leg is only medium and it has never run (UNVERIFIED).
3. **Successor vs frozen oracle.** Claim semantics: successor `06` section 5 / `11` section 3C: `PermissionError("authorization-critical inputs changed before claim issuance")` (`local_authority_effect.py:443-466`), no claim, **no `EffectTimeRefusal` and no refusal write**, destination untouched; the machine-readable `authorization_binding_changed` token is an obligation of the effecting (execute) path only. Pre-existing stage-`claim` `ResolutionCheck` rows and `check_events` ARE written and are expected (do not assert "no new journal rows" for the claim leg; assert specifically no `EffectTimeRefusal`, no attempt/claim row, no authorization-state write). Frozen `03` expectation 1 / `02` section 4 rule 2 literal wording ("execute and pin-export claim ... refuse `authorization_binding_changed` and a durable `EffectTimeRefusal`") would, read literally, demand a refusal row on the claim/pin-export path; that literal reading FAILed in the original (DEV-PE-1). The successor interpretation is **adopted by no human yet**. Therefore FC-H1 and N-CLAIM-JOINT are scored against the successor reading and each must carry a separately recorded, non-scored annotation "under frozen-literal reading: no durable refusal observed". Execute cases (FC-H2, FC-H3, FXE-JOINT) follow the frozen contract, which both readings agree on.
4. **FC-H1 control claim is UNVERIFIED.** Dossier: "UNVERIFIED: that the F5 world can issue a control claim." If the control claim cannot be issued once on the unperturbed F5 world, FC-H1 is BLOCKED, not FAIL, and not repaired. Likewise for N-CLAIM-JOINT's domain-world control claim.
5. **FC-H2 requires a reversible host class.** D-1's class-unreadable host class is irreversible and `host_class_defect` rejects it unless `refuse`; the case needs a reversible host class plus a Registry value that masks the host edit (record 12 item 2's `test_c06` is such a fixture, same family). If the Registry/adapter cannot be built so that the edited host leaf is masked (effective profile unchanged) without bypassing a guard, FC-H2 is BLOCKED. FC-H2 counts toward "two" only under reading R2 (unverified); do not claim it discharges item 2.
6. **FC-H3 is a bounded control, optional in the dossier and "never isolating".** Dossier gives two possible outcomes (GUARD-FIRST `runtime_authority_approval_mismatch` without re-issue, or JOINT with re-issue). The protocol must freeze BOTH sub-runs and their expected outcomes before running (not choose after); neither can carry an isolation claim. Its purpose is to document the masked-host limit text alongside (record 12 wording is broader than the CP text, which exists only at `8616d5f`; at `739efe7` it is absent).
7. **FXE-JOINT specifics (dossier CE4).** Class-age; host extension limit 100, T1 age 60; decide under Registry SA={T1:70}, rebuild under SB={T1:90}, re-issue approval, execute. Expected: `PermissionError`, exactly one new refusal `[authorization_binding_changed]`, no attempt row, destination untouched, base diff exactly `{approval_commitment, catalogue_digest}`, ECB diff exactly `{digest, effective_profile_digest}` (no `families.*` leaf, no host leaf). Dossier controls C0 (SA unchanged executes), C1 (no re-issue gives `[runtime_authority_approval_mismatch]` only), C2 (neutral re-signed SA' executes), C3 (effective-map change widens ECB diff to the families leaf). UNVERIFIED: that the pinned adapter accepts a Registry value above the host; if it refuses, STOP the case as BLOCKED. This corrects the D-1 reviewer's belief that an effective change always moves `families.0.effective_policy_digest`; the base-diff expectation is an unexecuted inference.
8. **Q2 record 12 item 1 asks for execute AND pin-export; this protocol contains no pin-export case and no authority_domain isolation.** N-CLAIM-JOINT is joint evidence and a different interface. No wording in the evidence package may suggest it addresses item 1.
9. **Record 12 item 2 "two independent fixtures" is ambiguous** (R1 one fixture per member; R2 two for the host member). The protocol takes no position; limitations.md must restate it as UNVERIFIED.
10. **Open interface not covered:** the public read-only `configuration_binding_status` / `effective_configuration_binding` classifier surface (dossier section 8). Cases may read it as evidence only; no classifier claim is made.
11. **Hub identity.** Dossier text names hub `main` `1c9b7197`; current hub HEAD is `07aa9055` (the dossier is present in it). Record both in `source-identity.json`; no conflict in the subject identities.
12. **D-1 instrument naming.** `d1_lib.rec` reads `D1_EVIDENCE_DIR` (mandatory) and `orig_harness` reads `F3_EVIDENCE_DIR`; the new lib's evidence rows (section 16) must be written by a wrapper because D-1 rows use `case/kind/t/check` (`CHECK_PASS`/`CHECK_FAIL`/`OBSERVATION`) without `expected`/`observed`/protocol fields.

## 16. Evidence package layout and evidence-row schema
Directory: `results/third-party/cp-739efe7-f3-q2q3-bounded-20261030/` containing: `README.md` (result in one line per case, NOT-claims, provenance section 2, reproduce command), `PROTOCOL.md` (this protocol, frozen, with per-case sections), `protocol.sha256` (sha256 of `PROTOCOL.md`; plus `FREEZE-TIME` line inside it or sibling `protocol.freeze.txt` `[LEAD]`), `manifest.json` (file list with sizes and sha256, instrument hashes, run labels, start/end times), `SHA256SUMS` (written LAST; `sha256sum -c SHA256SUMS` from the directory root must pass), `environment.json` (section 5 outputs), `source-identity.json` (section 3 and 4 outputs, before and after pristine hash), `case-results.json` (per case: result, per-assertion results, six-dimension statuses, run1/run2 agreement), `expected-vs-observed.md` (table per assertion: id, expected, observed, result), `raw/` (`preflight/`, `run1/`, `run2/` each with `stdout.txt`, `stderr.txt`, `junit.xml`, `start.txt`, `end.txt`, evidence jsonl, journal snapshots, exception traces, `post/` environment and pristine hash), `review/` (reviewer notes, labelled same-lineage), `limitations.md` (provenance, UNVERIFIED items, what is not claimed, nondeterminism if any).

Evidence row (one JSON object per line, `sort_keys`, UTF-8) in `raw/<run>/bq_evidence.jsonl`; required keys:
- `protocol` (`OCS-F3-Q2Q3-BOUNDED-v1`), `run` (`run1`/`run2`), `case_id`, `assertion_id` (`<CASE>.<nn>`; precondition/control rows use ids like `<CASE>.P<nn>` / `<CASE>.C<nn>`), `kind` in {`PRECONDITION`, `CONTROL`, `ASSERTION`, `OBSERVATION`, `SNAPSHOT`, `EXCEPTION`},
- `expected` (the frozen value, JSON), `observed` (JSON), `result` in {`PASS`,`FAIL`,`BLOCKED`,`NOT EXECUTED`} (OBSERVATION/SNAPSHOT rows: `n/a`),
- `t_start`, `t_end` (UTC ISO 8601 with Z) and `t` (epoch seconds, as D-1).
Additional mandatory content, as `SNAPSHOT`/`OBSERVATION` rows per case: (a) durable journal row snapshots BEFORE and AFTER each leg (decision rows, `EffectTimeRefusal` rows with reasons and vocabulary, attempt/claim rows, `ResolutionCheck` rows, authorization state), as canonical JSON with row counts; (b) destination call counts before/after each leg (execute and claim legs) with the stub's own count; (c) complementary binding diff: full leaf sets for base diff and ECB diff and the member digests with independent recomputation values; (d) every raised exception: type, `str`, full traceback in an `EXCEPTION` row (an expected `PermissionError` is recorded too, with its text); (e) for every PASS assertion on a refusal, the observed reasons list verbatim. A case record without all of (a)-(e) cannot be scored PASS.

## 17. Scope statements the README and limitations.md must carry
Bounded technical record of five cases at CP `739efe7`, Registry pin `a40fe755`, Python 3.11.18 only. Not a Tier 1 result, not an independent or competent certification, not an acceptance of Q2 or Q3, not a statement about `8616d5f`, `main` or Python 3.12, not a pin-export result, not an authority_domain isolation. Q2 and Q3 remain OPEN under record 12 Class A unless and until the Architect decides otherwise. Original F3-A FAIL (23 assertions) is unchanged; successor F3-A remains a conditional scoped PASS pending human adoption of record 11.
