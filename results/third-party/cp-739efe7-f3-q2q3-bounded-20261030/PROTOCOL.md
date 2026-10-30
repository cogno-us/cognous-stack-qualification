# OCS-F3-Q2Q3-BOUNDED-v1 - bounded Q2/Q3 qualification of Control Plane 739efe7 (work package OCS-F3-Q240-BOUNDED-QUALIFICATION)

FROZEN PROTOCOL OCS-F3-Q2Q3-BOUNDED-v1 (common part by Worker A; per-case specifications by Workers B, C, D reproduced in appendices; assembled and frozen by the lead). Frozen means `protocol.sha256` is written BEFORE any case execution; this file does not contain its own hash (see `protocol.sha256` and `FREEZE-TIME.txt`). Instrument hashes: see the Freeze record near the end.

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
| Hub | `main` `07aa90553da41305bd38fd54447b3fbc29ed6cbc` (dossier merge; the dossier text names the pre-merge main `1c9b7197`; both recorded) | `git -C <hub> rev-parse HEAD` |
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
| `harness/<new lib>` | none: the new test files use d1_lib.py and local helpers | no separate new library |
| `harness/test_bq_host.py`, `test_bq_eff.py`, `test_bq_domain.py` | see Freeze record | the five cases' frozen assertion inventories |
| `harness/run_bq.sh` | see Freeze record | section 8 |
| preflight | commands of sections 3 and 5 run by the lead before the first case; output in `source-identity.json` / `environment.json` | no separate preflight script |
New files may import `d1_lib` / `orig_harness` but must not edit them. `test_d1.py`, `probe_d1.py`, `run_d1.sh` and D-1 mutant diffs are NOT part of this protocol's instruments (no mutants are run, section 10).

## 7. Cases (per-case sections appended by the lead)
Each case section MUST contain: world construction; control(s) and their required outcomes; validity preconditions (a failing one yields BLOCKED); the complete frozen assertion inventory with ids `<CASE>.<nn>`, each stating kind, expected value, and observation method; predicted outcome; claim permitted if all pass; what the case cannot establish. Case order of execution: fixed (lead) and recorded.
Sections 7.1-7.5 are the case workers' frozen specifications, reproduced verbatim in the appendices at the end of this document: A (FC-H1, FC-H2, FC-H3a/b, `cases-host.md`), B (FXE-JOINT, `cases-eff.md`), C (N-CLAIM-JOINT, `cases-domain.md`).

Common instrument (reused from D-1): complementary binding diff = dotted-leaf diff between the PERSISTED decision binding and the binding the LIVE world genuinely mints for the same proposal (`d1_lib.live_binding`, `split_diff`), split into base diff (outside `runtime_authority.effective_configuration`) and ECB diff (inside). Attribution of `authorization_binding_changed` (or the claim `PermissionError`) to a member comes ONLY from the complementary diff, never from the refusal code (the comparison `current != persisted.binding` is generic). The candidate's `configuration_binding_status` is evidence only, never the oracle; the oracle for member content is the harness's own recomputation (`own_commit`, `H.my_digest`).

## 8. Run command (parameterized; no worker home paths)
`harness/run_bq.sh` (modelled on D-1 `run_d1.sh`; body to be frozen exactly as below, `python -I` is dropped (see lead decision below)):
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
"$PY" -m pytest -p no:cacheprovider -q -rA --junitxml="$OUT/junit.xml" --basetemp="$OUT/basetemp-parent/bt" \
  "${ARGS[@]}" "$HERE"/test_bq*.py > "$OUT/stdout.txt" 2> "$OUT/stderr.txt"
echo "exit=$?" >> "$OUT/stdout.txt"
date -u +%FT%TZ > "$OUT/end.txt"
tail -15 "$OUT/stdout.txt"
```
Lead decision at freeze: `python -I` is dropped because it ignores `PYTHONPATH`, which this harness uses to import the subject (as D-1 did); `PYTHONDONTWRITEBYTECODE=1` is set instead.

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
Directory: `results/third-party/cp-739efe7-f3-q2q3-bounded-20261030/` containing: `README.md` (result in one line per case, NOT-claims, provenance section 2, reproduce command), `PROTOCOL.md` (this protocol, frozen, with per-case sections), `protocol.sha256` (sha256 of `PROTOCOL.md`; plus `FREEZE-TIME` line inside it or sibling `protocol.freeze.txt` (lead)), `manifest.json` (file list with sizes and sha256, instrument hashes, run labels, start/end times), `SHA256SUMS` (written LAST; `sha256sum -c SHA256SUMS` from the directory root must pass), `environment.json` (section 5 outputs), `source-identity.json` (section 3 and 4 outputs, before and after pristine hash), `case-results.json` (per case: result, per-assertion results, six-dimension statuses, run1/run2 agreement), `expected-vs-observed.md` (table per assertion: id, expected, observed, result), `raw/` (`preflight/`, `run1/`, `run2/` each with `stdout.txt`, `stderr.txt`, `junit.xml`, `start.txt`, `end.txt`, evidence jsonl, journal snapshots, exception traces, `post/` environment and pristine hash), `review/` (reviewer notes, labelled same-lineage), `limitations.md` (provenance, UNVERIFIED items, what is not claimed, nondeterminism if any).

Evidence row (one JSON object per line, `sort_keys`, UTF-8) in `raw/<run>/bq_evidence.jsonl`; required keys:
- `protocol` (`OCS-F3-Q2Q3-BOUNDED-v1`), `run` (`run1`/`run2`), `case_id`, `assertion_id` (`<CASE>.<nn>`; precondition/control rows use ids like `<CASE>.P<nn>` / `<CASE>.C<nn>`), `kind` in {`PRECONDITION`, `CONTROL`, `ASSERTION`, `OBSERVATION`, `SNAPSHOT`, `EXCEPTION`},
- `expected` (the frozen value, JSON), `observed` (JSON), `result` in {`PASS`,`FAIL`,`BLOCKED`,`NOT EXECUTED`} (OBSERVATION/SNAPSHOT rows: `n/a`),
- `t_start`, `t_end` (UTC ISO 8601 with Z) and `t` (epoch seconds, as D-1).
Additional mandatory content, as `SNAPSHOT`/`OBSERVATION` rows per case: (a) durable journal row snapshots BEFORE and AFTER each leg (decision rows, `EffectTimeRefusal` rows with reasons and vocabulary, attempt/claim rows, `ResolutionCheck` rows, authorization state), as canonical JSON with row counts; (b) destination call counts before/after each leg (execute and claim legs) with the stub's own count; (c) complementary binding diff: full leaf sets for base diff and ECB diff and the member digests with independent recomputation values; (d) every raised exception: type, `str`, full traceback in an `EXCEPTION` row (an expected `PermissionError` is recorded too, with its text); (e) for every PASS assertion on a refusal, the observed reasons list verbatim. A case record without all of (a)-(e) cannot be scored PASS.

## 17. Scope statements the README and limitations.md must carry
Bounded technical record of five cases at CP `739efe7`, Registry pin `a40fe755`, Python 3.11.18 only. Not a Tier 1 result, not an independent or competent certification, not an acceptance of Q2 or Q3, not a statement about `8616d5f`, `main` or Python 3.12, not a pin-export result, not an authority_domain isolation. Q2 and Q3 remain OPEN under record 12 Class A unless and until the Architect decides otherwise. Original F3-A FAIL (23 assertions) is unchanged; successor F3-A remains a conditional scoped PASS pending human adoption of record 11.

## Freeze record: instrument hashes (lead, at freeze)
| File | sha256 |
|---|---|
| `harness/test_bq_host.py` | `ba2a307f727094383024df9bcbc24eadb040ac638cdaafbed8ce5fcb399ba508` |
| `harness/test_bq_eff.py` | `a3b66ce07fdaa3122253abdfe13a64e093906bebfbf320ae48ab63a88d103cc0` |
| `harness/test_bq_domain.py` | `2897ccde29d3108fc8f6a18e38634c5442bf5db41277d6ceaf25969728711f10` |
| `harness/run_bq.sh` | `092aa92785fd12464ea7e5187b8f2dc2907cda3ad58b0067f0a5a427c0a89da3` |
| `harness/d1_lib.py` | `5ec947ba028fdd9aa5024215881103d8ac55c2ffb5f7049cfd70a4f76ac3bddc` |
| `harness/orig_harness.py` | `a51474128d8094932c91b3dd95b95fd751920b12b61499ab06acfbdac8727b0b` |
| `spec/cases-host.md` / `cases-eff.md` / `cases-domain.md` | reproduced verbatim in this protocol; sha256 of each source file: db6b06a670aaea6e44d7e60786bb0cea4e57965c2744278849d8619ec1ac93b7 / 930ad7f97b311ae1b0e402de5b9eaf630352802b061e99eb071b14dd86d05e46 / d8a656cf432ab535af973ae039216731d36ba0571ca8f375e84a838cd7b661bb |

Lead pre-freeze notes (no execution has occurred): (1) N-CLAIM-JOINT gates its main case on a never-run provision route (control C01 and P08 use `provision_local_execution_claim`; record 12 item 7, Class B); if that route is refused the case scores BLOCKED, not FAIL. (2) FC-H1 control claim on the F5 world, FC-H2 Registry r08-v5 material builder and FXE-JOINT acceptance of a Registry value above the host at pin a40fe755 are source-read, not tested; any failure scores BLOCKED. (3) The test_bq_domain supplementary control `_CY` is retained as an evidence-only control, not a gate. (4) Hub main at freeze: 07aa90553da41305bd38fd54447b3fbc29ed6cbc (dossier named 1c9b7197; both recorded).


---
# Appendix A: cases-host.md (FC-H1, FC-H2, FC-H3a, FC-H3b)

# cases-host.md - frozen case specification FC-H1, FC-H2, FC-H3a, FC-H3b (OCS-F3-Q240-BOUNDED-QUALIFICATION, host_profile_digest)

Author: Worker B, DRAFT PHASE (nothing executed; sources read, `py_compile` and `pytest --collect-only` only). Same session lineage as the lead: NOT independent; technical qualification evidence only.
Code under spec: `/tmp/claude-0/work/bq/harness/test_bq_host.py` (imports read-only `d1_lib.py` sha256 5ec947ba..., and `orig_harness.py`). Test names: `test_FC_H1`, `test_FC_H2`, `test_FC_H3a`, `test_FC_H3b`.
Subject: Control Plane 739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69 (pristine tree `/tmp/claude-0/work/src/cp-739efe7`, `PYTHONPATH=<cp>/src`); Registry pin a40fe755 (`OCS_REGISTRY_PIN_DIR`, `OCS_REQUIRE_REGISTRY_PIN=1`); Python 3.11.18; env as D-1 `run_d1.sh` (`D1_CP_ROOT`, `D1_EVIDENCE_DIR`, `F3_EVIDENCE_DIR`, `D1_LABEL`).
Source citations below are CP 739efe7 `src/agent_control_plane/...` read from the pristine tree.

## 0. Conventions (apply to all four cases)

- Instrument: complementary binding diff = leaf diff of the PERSISTED decision binding (read from the store the subject wrote) vs the binding a scratch LIVE world genuinely mints (`d1_lib.live_binding`, a real `decide` in a fresh scratch store, same fixtures and clock), split by `d1_lib.split_diff` into base diff (outside `runtime_authority.effective_configuration`) and ECB diff (inside). D-1 decision rule: "isolated end-to-end" iff base diff == [] and ECB diff == {ecb.digest, ecb.members.host_profile_digest}; otherwise "joint". The candidate's `configuration_binding_status` is evidence only (rows `E*`), never an oracle.
- Evidence rows (`$D1_EVIDENCE_DIR/d1_evidence.jsonl`, one row per assertion, every row has `case`, `assertion_id`, `check`, `expected`, `observed`, `result`):
  `PRECONDITION_PASS/FAIL` (id `*-P*`); `CHECK_PASS/FAIL` (gating, ids `*-C*` controls and `*-A*` assertions, `gating=true`); `OBSERVATION` (`gating=false`, ids `*-E*`, evidence-only, `result` MATCH/DIVERGE, never part of a verdict); `BLOCKED`; `CLASSIFICATION` (H3a, H3b; H1/H2 carry the classification inside observation rows `FC-H1-E04`, `FC-H2-E03`); one `PREFLIGHT` row per session.
- BLOCKED rule (frozen): any failing `P*` row, an unissuable control claim (FC-H1-P04), or any unhandled exception in a case body writes a `BLOCKED` row (raw exception type, text and traceback retained) and fails the test hard. A BLOCKED case is NOT interpreted and is corrected only by a versioned successor.
- A failing `C*`/`A*` row against the pristine subject is an ADVERSE FINDING retained as observed; it is never revised after the fact.
- Expected values are hard-coded literals in the code and listed below. The only computed oracles are the harness's own independent sha256 commitments (`own_commit`, same as D-1) used in preconditions, never to produce an expected value of an assertion from an observed one.
- Not done by any case: no guard disabled/patched/bypassed, no store write or graft, no private attribute read (only `configuration_binding_status`, `decide`, `execute`, `materialize_local_execution_claim`, constructors), no network, only the D-1 clock patch (`H.patch_clock`). Synthetic data only.
- Shared fixture facts: F5 world = `d1_lib.f5_world(t1, reg)` (Registry r08-v2 class-age selection for class `synthetic-irreversible`, host class irreversible, `max_status_age_seconds` = t1, no freshness, no policy_binding); action id `urn:cognous:action:refund-issue-routine-v1`; approval bound to the EFFECTIVE profile at mint (`f5_mint`), NOT re-issued unless a case says so.

## 1. Exact reason / message strings frozen (derived from source)

| Where | String | Source |
|---|---|---|
| Execute, durable `EffectTimeRefusal.reasons` for any base-silent binding difference | `["authorization_binding_changed"]` | `bounded.py:1690-1693` (set only when no other reason exists) |
| Execute, refusal vocabulary | `runtime-authority-reasons/0.1` | `bounded.py:1707`, `vocabulary_for` |
| Execute, exception text | `authorization-critical inputs changed before effect` | `bounded.py:1711` |
| Execute, H3a guard-first reason | `["runtime_authority_approval_mismatch"]` (D-1 Q3-E1 literal) | `runtime_authority.py:332-335` |
| Claim issuance, exception text (FC-H1) | `authorization-critical inputs changed before claim issuance` (type exactly `PermissionError`) | `local_authority_effect.py:455-458` |
| Claim issuance, durable refusal | NONE. The claim path does NOT name `authorization_binding_changed` anywhere: no `EffectTimeRefusal`, no reason code in the exception text. The lifecycle `_resolve` (`registry_governed_lifecycle.py:271-285`) returns no reasons on a member mismatch (the code is only added when the stamped extension equals the persisted one, `:278`), so the only artefact of the refusal is one `ResolutionCheck` (stage `claim`, reasons `[]`) plus check events, written by `_record_check` (`local_authority_effect.py:451`, `bounded.py:1327`, `record_resolution_check` `:624-660`) before the raise | as listed |

Frozen reading: the claim leg refuses through the generic base comparison `current != decision.binding`; the attribution to `host_profile_digest` rests on the complementary diff (rows `FC-H1-A01/A02`), not on any reason string.

## 2. FC-H1 - host_profile_digest, CLAIM ISSUANCE leg, F5 class-age masked-host world

**Purpose.** Show on the D-1 H1 world (host class age 60 -> 61, masked by Registry 10, approval not re-issued) that a rebuilt workflow whose ONLY live difference is the host profile refuses to issue a local execution claim for the previously authorized decision, with the base binding unchanged and the ECB diff exactly {digest, host_profile_digest}, and that an unperturbed world issues exactly one claim.

**Validity preconditions (any failure => BLOCKED, not interpreted).**
P01 control world minted `authorized`; P02 `p.action_id == urn:cognous:action:refund-issue-routine-v1`; P03 control live world mints `authorized`; **P04 the control claim is issued on this world (frozen rule: if the control claim cannot be issued the case is BLOCKED, raw exception type/text recorded; the control is never weakened)**; P05 perturbed world minted `authorized`; P06 host class ages `[60, 61]`; P07 host dumps differ in exactly `actions.urn:cognous:action:refund-issue-routine-v1.max_status_age_seconds`; P08 effective profile dumps equal; P09 independent commitments of the effective dumps equal; P10 independent commitments of the host dumps differ; P11 effective class age `[10, 10]`; P12 live world with the edited host mints `authorized`; P13 `catalogue_digest` equal across (persisted vs live), `effective_profile_digest` equal across, persisted `catalogue_digest` == `own_commit(effective dump)` (all `[true, true, true]`).

**Steps.**
1. Control world `h1c`: `f5_world(60,10)`, `f5_mint`; restart identical host (`f5_flow`); live-world diff (scratch); ONE call `materialize_local_execution_claim(flow, p, persisted_decision, now=NOW, claim_id="bq-fc-h1-control")` (supported public interface, no `policy_binding`, no `expected_*`); store snapshot before/after.
2. Perturbed world `h1p`: `f5_world(60,10)`, `f5_mint`; build host2 (age 61); rebuild the workflow over the same store with host2, approval NOT re-bound; independent preconditions; live-world diff (scratch) BEFORE touching the store.
3. ONE call `materialize_local_execution_claim(flow2, p, persisted_decision, now=NOW, claim_id="bq-fc-h1-perturbed")` with store snapshots (`run.json` read, never written by the harness) and destination snapshot before/after.
4. Evidence-only restoration control: rebuild with the original host over the same store and issue `bq-fc-h1-restore`.

**Assertion inventory (expected values hard-coded).**

| id | statement | expected |
|---|---|---|
| FC-H1-C01 | control live binding diff, base | `[]` |
| FC-H1-C02 | control live binding diff, ECB | `[]` |
| FC-H1-C03 | `verify_local_execution_claim(control claim)` | `True` |
| FC-H1-C04 | `[claim.decision_id, claim.claim_id]` | `[<minted decision id>, "bq-fc-h1-control"]` |
| FC-H1-C05 | `claim.authorizing_by_possession` | `False` |
| FC-H1-C06 | `[claims issued, destination calls, destination snapshot unchanged]` | `[1, 0, True]` |
| FC-H1-C07 | control claim new rows `refusals/attempts/decisions` | `{"refusals":0,"attempts":0,"decisions":0}` |
| FC-H1-A01 | perturbed base binding diff | `[]` |
| FC-H1-A02 | perturbed ECB diff (sorted) | `["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.host_profile_digest"]` |
| FC-H1-A03 | exception type raised by claim issuance | `"PermissionError"` (row also records `type(exc) is PermissionError`) |
| FC-H1-A04 | claim object returned is None (no claim emitted) | `True` |
| FC-H1-A05 | exception text | `"authorization-critical inputs changed before claim issuance"` |
| FC-H1-A06 | text contains `authorization_binding_changed` | `False` |
| FC-H1-A07 | new durable refusal rows (`refusals` delta) | `0` |
| FC-H1-A08 | new attempt rows | `0` |
| FC-H1-A09 | `decisions/observations/reconciliations/closeouts` deltas | all `0` |
| FC-H1-A10 | `[destination calls, destination snapshot unchanged]` | `[0, True]` |
| FC-H1-A11 | top-level `run.json` keys that changed, minus `{check_events, input_time_floors, resolution_checks}` | `[]` |
| FC-H1-A12 | `resolution_checks` delta | `1` |
| FC-H1-A13 | `[stage, reasons]` of the new resolution check | `[["claim", []]]` |
| FC-H1-A14 | persisted decision after the refusal equals the decision before | `True` |

Evidence-only (never gating): E01 control classifier `bound`; E02 raw control claim type and bookkeeping; E03 perturbed classifier `mismatch`; E04 raw bookkeeping, base/ECB diffs and classification string; E05 restoration control issues a claim on the same store with the original host (`issued`).

**Failure conditions.** Any `C*/A*` row FAIL; any `P*` FAIL or unhandled exception => BLOCKED (not a FAIL of the subject). A02 failing with a non-empty base diff means the world is not isolating (label joint, stop). A12/A13 are source-derived (medium-high confidence: `_record_check` runs before the raise) and are bookkeeping facts, not the member claim; a failure of A12/A13 alone does not by itself contradict A01-A11 but is retained as observed.

**What it does / does not establish (six dimensions).**
- functional correctness: control world issues exactly one valid claim (C01-C07) on the F5 world. Does not establish claim content correctness beyond `verify_local_execution_claim` and decision binding.
- member sensitivity: with A01/A02/A03-A10 passing, the claim comparison refuses on a diff confined to `host_profile_digest` (and the derived ECB `digest`) on the LIVE side. Not shown: sensitivity of the comparison to other members on this leg (not in scope).
- guard-order evidence: claim path runs `_resolve(stage="claim")` (base guards incl. approval guard, then ECB) before the generic comparison; base reasons empty and base diff empty places the refusal at the ECB step. The claim path does not run `_gl_revalidate`/selection re-verification (`local_authority_effect.py:442-458`); that is source reading, not shown by a row.
- end-to-end refusal: yes for the claim leg (no claim object, no durable refusal by design); NOT an execute-leg or pin-export statement.
- independent isolation: NO. Same session lineage as the lead, same fixture family and helper library as D-1, n=1 world, one workflow family; an independent owner is not established.
- contract coverage: touches only the claim leg for host_profile_digest on class-age. Does not cover `provision_local_execution_claim`, `policy_binding` claim variants, other workflow families, pin-export, other members.

**Evidence rows written.** `PREFLIGHT`; `FC-H1` rows `FC-H1-P01..P13`, `C01..C07`, `A01..A14`, `E01..E05` (E05 expected `issued`); `BLOCKED` only on failure. Note: classification string (`isolated end-to-end` / `joint`) is in row `FC-H1-E04`.

## 3. FC-H2 - second masked-host workflow, EXECUTE (GovernedClassUnreadableWorkflow)

**Purpose.** Repeat the D-1 H1 pattern on a different workflow family, hook and Registry family: class-unreadable (Registry r08-v5 `f5-action-class-unreadable-policy`, hook `registry_f5_class_unreadable_governance.py:336`, masking `compose_unreadable` `:146-151`), where a host `on_unreadable` edit is masked by a Registry narrowing, and show the refusal and the diff attribution.

**Fixture.** Host profile (shape of the developer fixture): scoped action class `synthetic-reversible` (`irreversible=False`, `max_status_age_seconds=60`, `on_unreadable` = world value), a second action `urn:cognous:action:refund-issue-high-v1` class `synthetic-irreversible` (`irreversible=True`, `on_unreadable="refuse"`; the irreversible class is already `refuse`, so `host_class_defect` does not reject it; the D-1 class is NOT reused). Registry r08-v5 selection names class `synthetic-reversible` -> `refuse` (operation `refund-issue-unreadable`, scope tenant/institution/domain of the manifest). Mint under host `bounded_tolerance` (effective `refuse`), approval bound to the effective profile; rebuild with host `refuse` (effective `refuse`, identical), approval NOT re-issued.

**Validity preconditions (any failure => BLOCKED; if the edit is not masked the case is BLOCKED, not interpreted).**
P01 control world minted `authorized`; P02 action id literal; P03 control live world mints `authorized`; P04 perturbed world minted `authorized`; P05 scoped class irreversible `[false, false]` in host1/host2; P06 host scoped `on_unreadable` `["bounded_tolerance", "refuse"]`; P07 host dumps differ in exactly `actions.urn:cognous:action:refund-issue-routine-v1.on_unreadable`; **P08 effective profile dumps equal across worlds; P09 their independent commitments equal; P10 host independent commitments differ; P11 effective scoped `on_unreadable` `["refuse","refuse"]`; P12 live world with edited host mints `authorized`; P13 `catalogue_digest`, `members.effective_profile_digest`, `members.families.0.effective_policy_digest` all equal between persisted and live, and persisted `catalogue_digest == own_commit(effective dump)` (`[true,true,true,true]`)**; P14 family rows in both are exactly `["class_unreadable"]`. P08/P09/P11/P13 are the "effective profile and catalogue digests equal across worlds" validity precondition: if the edit is not masked the case is BLOCKED.

**Steps.** (1) Control world `h2c`: mint, identical restart, live diff, execute the original decision. (2) Perturbed world `h2p`: mint (host `bounded_tolerance`); rebuild over the same store with host `refuse`, approval NOT re-bound; live diff before execution; execute the original decision once via `H.drive_execute`.

**Assertion inventory.**

| id | statement | expected |
|---|---|---|
| FC-H2-C01 | control live diff base | `[]` |
| FC-H2-C02 | control live diff ECB | `[]` |
| FC-H2-C03 | control `[attempt status, exception]` | `["acknowledged", null]` |
| FC-H2-C04 | control new refusal rows | `[]` |
| FC-H2-C05 | control destination calls | `1` (unperturbed executes exactly once) |
| FC-H2-A01 | perturbed base binding diff | `[]` |
| FC-H2-A02 | perturbed ECB diff (sorted) | `["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.host_profile_digest"]` |
| FC-H2-A03 | exception type | `"PermissionError"` |
| FC-H2-A04 | exception text | `"authorization-critical inputs changed before effect"` |
| FC-H2-A05 | new durable refusals' reasons (exactly one new row) | `[["authorization_binding_changed"]]` |
| FC-H2-A06 | new refusal vocabulary | `["runtime-authority-reasons/0.1"]` |
| FC-H2-A07 | new attempt rows | `0` |
| FC-H2-A08 | `[destination calls, destination snapshot unchanged]` | `[0, true]` |

Evidence-only: E01 control classifier `bound`; E02 perturbed classifier `mismatch`; E03 raw classification string and diffs (the prediction is `isolated end-to-end`, not asserted as a row).

**Failure conditions.** Any `C*/A*` FAIL; the host edit EXECUTING (acknowledged, 1 destination call) is the kill-signal for a host-digest-from-effective defect in this hook; P-failure or exception => BLOCKED.

**What it does / does not establish.**
- functional correctness: a second workflow family mints, executes once (C03-C05) and exposes the same member contract.
- member sensitivity: with A01-A08 passing the live execute comparison refuses on a diff confined to `host_profile_digest` in the class-unreadable hook. No scratch mutant is run here, so sensitivity to a defect in the hook (`:336`) is inferred from the live refusal only, not demonstrated by a kill.
- guard-order evidence: base diff empty and base reasons absent show no earlier guard fired; the approval guard did not trip because the effective profile is identical. Not shown for any other member.
- end-to-end refusal: yes on execute for this family.
- independent isolation: NO (same lineage; same fixture library; n=1 world for this family).
- contract coverage: class-unreadable dedicated, execute leg, host_profile_digest only. Does not cover the joint class-unreadable+class-age workflow, composed policy workflow, claim leg, pin-export, freshness-extension, other members.

**Evidence rows written.** `FC-H2-P01..P14`, `C01..C05`, `A01..A08`, `E01..E03`; `BLOCKED` only on failure.

## 4. FC-H3 - unmasked-host contrast control (BOUNDED; NEVER ISOLATING)

Statement for both sub-cases: **FC-H3 does NOT isolate `host_profile_digest`.** The edit is unmasked by construction (host 60 -> 5 under Registry 10, effective min(5,10) = 5), so the effective profile, `catalogue_digest`, `approval_commitment` and the class-age family digest change together with the host digest. Its only purpose is to distinguish mechanism behavior: unmasked host drift is refused through other members first (H3a) or jointly (H3b). It must not be cited as evidence for the host member's isolation and must not be combined with FC-H1/FC-H2 into an isolation claim.

Shared preconditions (helper; ids `FC-H3a-P01..P07` and `FC-H3b-P01..P07`; any failure => BLOCKED): P01 minted `authorized`; P02 action id literal; P03 host class ages `[60, 5]`; P04 host dumps differ in exactly `actions.urn:cognous:action:refund-issue-routine-v1.max_status_age_seconds`; **P05 effective class age `[10, 5]` (the edit is NOT masked; if the effective value does not change the case is BLOCKED)**; P06 effective independent commitments differ; P07 host independent commitments differ. H3b adds P08 live world after approval re-issue mints `authorized`.

### FC-H3a - approval NOT re-issued (guard-first)
Steps: mint (host 60, Registry 10, approval bound to effective {10}); rebuild with host age 5 over the same store, approval NOT re-bound; execute the original decision.

| id | statement | expected |
|---|---|---|
| FC-H3a-A01 | exception type | `"PermissionError"` |
| FC-H3a-A02 | exception text | `"authorization-critical inputs changed before effect"` |
| FC-H3a-A03 | new durable refusal reasons | `[["runtime_authority_approval_mismatch"]]` |
| FC-H3a-A04 | vocabulary | `["runtime-authority-reasons/0.1"]` |
| FC-H3a-A05 | new attempts | `0` |
| FC-H3a-A06 | `[destination calls, unchanged]` | `[0, true]` |
| FC-H3a-A07 | `authorization_binding_changed` present in any new refusal | `False` |

Evidence-only: E01 classifier `mismatch` (it says nothing about guard order). `CLASSIFICATION` row: "guard-first (approval); host_profile_digest NOT isolated; the ECB was not the refusing comparison". "ECB not consulted" is an inference from guard order (approval guard `runtime_authority.py:332-335` runs inside the base `_resolve`, before the lifecycle ECB step, `registry_governed_lifecycle.py:266-268`); the row asserts only that the ECB code is absent.

### FC-H3b - approval re-issued against the new effective profile (joint)
Steps: mint (host 60); rebuild with host age 5 and `bind_approval` against the new effective profile; live-world diff (scratch) after the re-issue; execute the original decision.

| id | statement | expected |
|---|---|---|
| FC-H3b-A01 | base binding diff (sorted) | `["runtime_authority.approval_commitment", "runtime_authority.catalogue_digest"]` |
| FC-H3b-A02 | ECB diff (sorted) | `["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.effective_profile_digest", "runtime_authority.effective_configuration.members.families.0.effective_policy_digest", "runtime_authority.effective_configuration.members.host_profile_digest"]` |
| FC-H3b-A03 | classification by the D-1 rule | `"joint"` |
| FC-H3b-A04 | exception type | `"PermissionError"` |
| FC-H3b-A05 | exception text | `"authorization-critical inputs changed before effect"` |
| FC-H3b-A06 | new durable refusal reasons | `[["authorization_binding_changed"]]` |
| FC-H3b-A07 | vocabulary | `["runtime-authority-reasons/0.1"]` |
| FC-H3b-A08 | new attempts | `0` |
| FC-H3b-A09 | `[destination calls, unchanged]` | `[0, true]` |

Evidence-only: E01 classifier `mismatch`. `CLASSIFICATION` row: claim string, base diff, ECB diff. Derivation of A01/A02 (from source, same machinery as D-1 Q3-E2): the effective map {T1:10} -> {T1:5} changes the effective profile (hence `catalogue_digest` and `approval_commitment`, `runtime_authority.py:332`, `:473-475`), `effective_profile_digest` and the Registry family digest (`registry_f5_class_age_governance.py:180`, `:260`), and the host profile changes `host_profile_digest`; nothing else is expected to move (D-1 E2 base diff had exactly these two base leaves). If A01/A02 differ by a leaf the exact diff is retained as observed.

**Failure conditions (H3a/H3b).** Any `A*` FAIL; P-failure/exception => BLOCKED. Results of H3a/H3b are descriptive of mechanism ordering only.

**What FC-H3a/H3b do / do not establish.**
- functional correctness: the F5 class-age world refuses unmasked host drift; says nothing about control correctness beyond what FC-H1/FC-H2 controls show.
- member sensitivity: NOT for `host_profile_digest` (H3a: refusal occurs before the ECB; H3b: several members and base leaves move at once).
- guard-order evidence: H3a shows the approval guard precedes the ECB for host-driven effective changes (same pattern as D-1 Q3-E1); H3b shows the joint refusal after re-issue (D-1 Q3-E2 pattern).
- end-to-end refusal: yes (two refusals), joint/guard-first only.
- independent isolation: none; NEVER isolating.
- contract coverage: contrast for the masked-host fixtures only; documents that the masking is the isolation device and that an unmasked edit is refused via other members.

**Evidence rows written.** `FC-H3a-P01..P07`, `A01..A07`, `E01`, `CLASSIFICATION`; `FC-H3b-P01..P08`, `A01..A09`, `E01`, `CLASSIFICATION`.

## 5. Cross-case scope statement for the report

The four cases together would extend D-1 Q3-H1 (execute, class-age, n=1) by: one claim-leg case (FC-H1), one second-family execute case (FC-H2), and a non-isolating contrast (FC-H3). They remain same-lineage, same-subject, same-pin, Python 3.11.18 only, synthetic fixtures; no pin-export case (not reachable for profile-bearing families, `policy_binding_unsupported` constructor refusals); no result transfers to 8616d5f, main or Python 3.12. The masked-host limit text (CP docs at 8616d5f only; absent at 739efe7) concerns F4 scalars and ObservationPolicy values; the cases here are host PROFILE edits and are consistent with, not tests of, that limit.


---
# Appendix B: cases-eff.md (FXE-JOINT)

# FXE-JOINT: effective-profile digest JOINT transition (freshness-extension route), EXECUTE leg: draft case specification

Status: DRAFT by Worker C (same session lineage as the lead; NOT independent). Written from source reading only; nothing was executed (no case, no probe, no pytest run; only `py_compile` to a scratch path and `pytest --collect-only`, which imports and runs no test body). Not an acceptance claim. The lead freezes (hashes) `harness/test_bq_eff.py` and this file before first execution; invalid fixtures after the freeze are retained as BLOCKED/FAIL and corrected only by a versioned successor (protocol section 14).

Instrument: `/tmp/claude-0/work/bq/harness/test_bq_eff.py` (imports, read-only, `d1_lib.py` sha256 `5ec947ba...` and `orig_harness.py` sha256 `a5147412...`; both verified unchanged at the end of the draft).
Subject: CP `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69`; Registry pin `a40fe755e2384a99c37016fa9ad59396f1835900`; Python 3.11.18; `GovernedClassAgeWorkflow` (dedicated class-age workflow, no activation ledger).
Static sources: `/tmp/claude-0/work/f252/worker-c.md` section 10 (FXE-JOINT, CE4), merged dossier section 7, protocol skeleton section 15 item 7.

## 0. Mandatory scope statement (to be carried verbatim into README.md and limitations.md)

FXE-JOINT is JOINT evidence. It is NOT independently isolated `effective_profile_digest` evidence and must never be labelled so. By `02` section 4 line 48 (`effective_profile_digest` equals `catalogue_digest` for profile-bearing workflows, else null) and by construction (one `_resolve` call derives both from the one object `self.runtime_authority_profile`; the approval commitment preimage contains the profile dump), the base pair `{approval_commitment, catalogue_digest}` always moves together with the effective member. The case narrows the ECB diff to exactly `{digest, members.effective_profile_digest}` (no `families.*` leaf, no `host_profile_digest` leaf) and nothing more. The case decision rule `claim_for(...)` is expected to return `"joint"`; a result `"isolated end-to-end"` would itself be an adverse finding (impossible by I1-I4 of worker-c section 3).

What FXE-JOINT does NOT prove:
1. Live derivation sensitivity of the effective digest alone (nothing varies `effective_profile_digest` with `catalogue_digest` and `approval_commitment` held fixed; by contract that state does not exist on a live path).
2. Pin-export behaviour (profile-bearing governed workflows refuse the `policy_binding` pin-export requires; no pin-export leg exists here; do not add one).
3. Claim / provision / materialize behaviour (no claim leg).
4. That a mutant of the live derivation (for example live effective := host digest at `registry_f5_class_age_governance.py:260`) would be caught: no mutant is run in this protocol (section 13), and by source reading such a mutant is outcome-equivalent on this case (the base pair still refuses).
5. Behaviour on class-unreadable, joint, composed, revocation, irreversibility or anchor workflows; F4-dedicated (null/null) workflows; other revisions (`8616d5f`, `main`), Registry main, Python 3.12.
6. Persisted-side comparison sensitivity of the effective member (that is A19/G1/G2/P5 evidence, not rerun here).
7. That record 12 item 2 is discharged, or that "two independent fixtures" is satisfied (reading R1/R2 UNVERIFIED).
8. That a re-issued approval is a production-grade control: it uses the supported host duty `bind_approval`, in the harness resolver.

## 1. Fixture (frozen values)

| Item | Value | Source of the value |
|---|---|---|
| Workflow | `GovernedClassAgeWorkflow`, scope (`consumer-test`, `tenant-alpha`, tenant proposal action, operation `refund-issue-routine`) | D-1 `d1_lib.construct_f5` |
| Host profile | one class `synthetic-irreversible` (T1), `irreversible=True`, `max_status_age_seconds=60`, `on_unreadable=refuse`, `producer_keys`, `allow_synthetic_resolver=True`, `freshness=FreshnessProfile(max_age_extension_seconds=100)` (other FreshnessProfile fields default; no `anchor_deadline_to_inputs`), no `policy_binding` | `test_bq_eff.fx_host` (own), modelled on `d1_lib.host_profile` plus developer test `test_f5_class_age_governance.py::host_profile(freshness=...)` |
| SA | Registry F5 record `{T1: 70}`, effective T1 = min(60, 70) = 60, room = 70 - 60 = 10, composed extension limit = min(100, 10) = 10 | `compose_profile` `registry_f5_class_age_governance.py:117-127`, `derive_effective` `:169-172` |
| SB | Registry F5 record `{T1: 90}`, effective T1 = 60, room 30, composed limit = min(100, 30) = 30 | same |
| SA' (C2) | `{T1: 70}`, record text byte-identical to SA, selection re-signed with `selection_id="sel-test-2"`, `epoch=2` | `test_bq_eff.fx_material` (own copy of `d1_lib.f5_material` with the two overrides); developer test l05 pattern |
| SC (C3) | `{T1: 50}`, effective T1 = 50, room = max(0, 50 - 50) = 0, composed limit = 0 | same functions |
| Registry validity | an r08-v2 F5 value above the host is accepted and composes by `min`: Registry `compose_f5` at pin: `eff = min(base[k], reg[k])` with a `widens_host` note only (`registry_successor/v2_age_bounds.py:219-227`); CP `derive_effective` refuses only `effective > host` (impossible by `min`) | read at pin `a40fe755` |
| Clock | `H.patch_clock` (D-1; the only patch): `bounded._now` and the governed modules' `_now` fixed at `tba.NOW` (2026-10-05T19:00Z); the Registry effective window is 2026-10-01..2026-10-06 | D-1 |
| Resolver/destination | tenant resolver from `tba.tenant_resolver_for`, approvals via `bind_approval` (supported host duty), `CountingDestination` in-process stub; no network | D-1 |

Persisted vs live: persisted decision minted by workflow over SA in store directory S; the live world is a second workflow over SB over the SAME store S for execute, and the live binding for the complementary diff is minted by a third workflow over SB in a scratch store (the D-1 `live_binding` method; it uses the same resolver, same clock, same approval state).

Selection / record identity (answer to the lead's source question): SA and SB share `selection_id` `sel-test-1`, epoch 1, issuer, consumer, scope, operation, validity window and trust snapshot; they differ in record content (`payload.class_status_max_age_seconds` 70 vs 90), hence `record_digest`, record text and the signature over the statement. None of this enters the persisted decision binding (the binding carries only digests: `catalogue_digest`, `approval_commitment`, the ECB member digests) or the ECB members (`families[].effective_policy_digest` covers `{family, contract_version, effective map}` only; `v2_policy_identity.preimage_from_inputs` takes `{family, contract_version, effective}`). The case therefore does not rely on any selection-identity difference; the harness records both record digests as an OBSERVATION.

## 2. Predicted values (derivation, frozen before execution)

- Effective profile dump under SA = host dump with `actions.<aid>.max_status_age_seconds = 60` (unchanged) and `freshness.max_age_extension_seconds = 10`. Under SB: same with `30`. Dumps differ in exactly one leaf: `freshness.max_age_extension_seconds`.
- `catalogue_digest` (base) = commitment of the held effective profile dump (`runtime_authority.py:475`); ECB `effective_profile_digest` = `profile_digest(held)` = the same commitment (`registry_f5_class_age_governance.py:260`). `host_profile_digest` = commitment of the HOST dump (limit 100), identical in SA and SB.
- `approval_commitment` preimage contains the profile dump (`runtime_authority.py:236-242`), so it differs between the SA-bound and SB-bound approvals.
- `families.0.effective_policy_digest` covers only `{T1: 60}`: equal in SA and SB. `scope`, `f4_scalars`, `other_scalars`, `observation_policy`: equal.
- Base diff (persisted SA binding vs live SB binding): exactly `{runtime_authority.approval_commitment, runtime_authority.catalogue_digest}`.
- ECB diff: exactly `{effective_configuration.digest, effective_configuration.members.effective_profile_digest}` (prefix `runtime_authority.`).
- Execute (SB workflow, approval re-issued): guard order `_gl_reverify` passes (rebuilt workflow derives its own held state), approval matches the live profile, base reasons empty, ECB classification `mismatch`, `current != persisted.binding` at `bounded.py:1690` -> `PermissionError("authorization-critical inputs changed before effect")`, one durable `EffectTimeRefusal` with `reasons == ["authorization_binding_changed"]` (vocabulary `runtime-authority-reasons/0.1` since the code is not in `CODES_ADDED_IN_0_2`), no attempt row, destination untouched.
- No age-extension row is recorded anywhere in the case (`age_extensions` stays 0): the extension limit is configuration, not an extension use.

## 3. Reason strings and exception text frozen

- `authorization_binding_changed` (main, C3)
- `runtime_authority_approval_mismatch` (C1, alone)
- Exception type `PermissionError`, text exactly `authorization-critical inputs changed before effect` (main, C1, C3 where asserted)
- Reason vocabulary `runtime-authority-reasons/0.1`
- Candidate classifier (evidence only) values: `mismatch` (main), `bound` (C0, C2)

## 4. Evidence rows

Every assertion emits exactly one row in `$BQ_EVIDENCE_DIR/bq_evidence.jsonl` (protocol section 16 schema: `protocol, run, case_id=FXE-JOINT, assertion_id, kind, expected, observed, result, t_start, t_end, t`, plus `test`), and one D-1-style mirror row (`CHECK_PASS` / `CHECK_FAIL` / `BLOCKED` / `NOT_EXECUTED`, with `check`, `expected`, `observed`) via `d1_lib.rec` in `$D1_EVIDENCE_DIR/d1_evidence.jsonl` (case `FXE-JOINT/<test>`). `result` is `PASS`/`FAIL` for assertions and controls, `PASS`/`BLOCKED` for preconditions, `NOT EXECUTED` for planned ids not reached after an abort or BLOCKED gate. Additional rows per leg: SNAPSHOT (`journal_before`, `journal_after`: counts of decisions, refusals, attempts, age extensions; refusal rows with reasons and vocabulary; destination call count and snapshot), OBSERVATION (`fixture_material`, `complementary_diff` with full leaf sets, persisted and live ECB members, digests and independent recomputations, `execute_outcome`), EXCEPTION (the raised `PermissionError` with full text and traceback). Assertion ids: `FXE-JOINT-A01..A32` (main), `FXE-JOINT-C0-A01..A08`, `FXE-JOINT-C1-A01..A08`, `FXE-JOINT-C2-A01..A07`, `FXE-JOINT-C3-A01..A10`; preconditions `FXE-JOINT-P01..P12` and `FXE-JOINT-C<k>-P<nn>`.

Expected values are hard-coded literals except one disclosed class, marked ORACLE below: digest expectations are `own_commit(expected_dump)` where `expected_dump` is built by the harness from the HOST dump plus two literal integers (age, extension limit) and canonicalised by the harness's own `H.canon` (sha256 over sorted-key, compact, non-ASCII JSON; byte-compatible with `bounded._canonical_bytes`, re-implemented in `orig_harness.canon`). Nothing is computed from the product's observed digest. Equality assertions (`A05`, `A11`) compare two observed values with expected literal `True` (these express the contract equality `eff == catalogue_digest`).

## 5. Six dimensions (protocol section 11) for FXE-JOINT, per leg

| Leg | 1 Functional | 2 Member sensitivity | 3 Guard order | 4 End-to-end refusal | 5 Independent isolation | 6 Contract coverage |
|---|---|---|---|---|---|---|
| main | CAN (A01-A13: persisted and live eff digest equal the independent commitment of the harness-built expected profile; eff == catalogue_digest) | PARTIAL, JOINT (A14-A23: base diff exactly the pair, ECB diff exactly `{digest, effective_profile_digest}`; CANNOT show the member alone) | CANNOT (main alone does not show which guard fired first; C1 does) | CAN (A24-A32: durable refusal after the approval re-issue; joint) | CANNOT: JOINT evidence, NO independent isolation | CAN: execute leg, class-age dedicated workflow, freshness-extension route only |
| C0 | CAN (control executes once; empty diff; digest recomputes) | NOT APPLICABLE | NOT APPLICABLE | NOT APPLICABLE (acceptance control) | NOT APPLICABLE | validity control only |
| C1 | NOT APPLICABLE | NOT APPLICABLE (member not reached) | CAN: approval guard fires first, ECB not consulted (code absent) | CAN only to its boundary (refused before the ECB; says nothing about the member) | NOT APPLICABLE | execute leg guard-first |
| C2 | CAN (neutral rotation does not refuse) | NOT APPLICABLE (shows a non-member change is not sensitive) | NOT APPLICABLE | NOT APPLICABLE | NOT APPLICABLE | validity control: SA vs SB difference is not a selection-identity artefact |
| C3 | CAN (SC dump equals the harness prediction) | PARTIAL, JOINT (diff widens by exactly `families.0.effective_policy_digest`: the leaf is observable) | NOT APPLICABLE | CAN (joint) | CANNOT | execute leg, effective-map route |

## 6. Case FXE-JOINT-main: `test_FXE_JOINT_main`

Purpose: execute-leg fail-closed behaviour on a JOINT transition of the effective profile whose ECB diff is exactly `{digest, effective_profile_digest}` (the narrowest joint reachable on a supported live path).

### 6.1 Exact steps
1. World: tenant proposal/resolver, HOST profile (T1 age 60, FreshnessProfile limit 100), runtime-authority context prepared as D-1 (`prepare_runtime_authority`). Registry source SA (`{T1: 70}`).
2. P01: construct `fa` = `GovernedClassAgeWorkflow` over SA, store S; approval bound to `fa`'s effective profile (`bind_approval`). P02/P03: `fa.decide(...)` -> must return `authorized` (persisted decision, ECB member minted).
3. P04: construct `fb` over SB (`{T1: 90}`), same store S, approval RE-ISSUED to `fb`'s effective profile (`bind_approval`).
4. Preconditions P05-P10 (fixture material, identity maps, family digest equality, profile dump diff, commitment inequality).
5. P11/P12: a third workflow over SB in a scratch store mints a decision (`authorized`); its binding is the live binding for the complementary diff.
6. Gate (any failed precondition -> BLOCKED, case not interpreted).
7. Compute base diff / ECB diff of persisted SA binding vs live SB binding (harness-side), assertions A01-A23.
8. Execute: `fb.execute(proposal, persisted_decision, adapter_id, now=NOW)`; record journal before/after, exception, outcome; assertions A24-A32.

### 6.2 Validity preconditions (BLOCKED if they fail; never interpreted)
| Id | Precondition | Expected |
|---|---|---|
| P01 | `fa` constructed over SA (host limit 100) without Registry/construction refusal | `constructed` |
| P02 | `fa.decide` completes without raising | `completed` |
| P03 | SA decision result | `authorized` |
| P04 | `fb` constructed over SB; the Registry/adapter accepts a record value (90) above the host (60) (developer test x02 implies yes; UNVERIFIED at pin `a40fe755`) | `constructed` |
| P05 | parsed record class maps: SA `{T1:70}`, SB `{T1:90}` | `{"A":{T1:70},"B":{T1:90}}` |
| P06 | `registry_f5_policy_identity["effective"]`: both `{T1:60}` (effective profile values equal) | `{"A":{T1:60},"B":{T1:60}}` |
| P07 | identity `host` ages both `{T1:60}` | same shape |
| P08 | `effective_policy_digest` of the two flows equal | `True` |
| P09 | held effective profile dump leaf diff A vs B | `["freshness.max_age_extension_seconds"]` exactly |
| P10 | `own_commit(dump_A) != own_commit(dump_B)` (catalogue_digest differs) | `True` |
| P11 | live scratch mint completes without raising | `completed` |
| P12 | live SB mint result | `authorized` |

### 6.3 Assertion inventory

Legend for "does NOT establish": see section 0 for the global NOT list (never an isolation, never pin-export/claim, never live derivation sensitivity alone, no mutant). Dimensions: F functional, M member sensitivity, G guard order, E end-to-end refusal, I independent isolation, K contract coverage. "Eviden" rows: the assertion's own row plus the case-level SNAPSHOT/OBSERVATION/EXCEPTION rows of 6.4.

| Id | Expected (hard-coded) | Fails when | Establishes | Does NOT establish | Dimensions |
|---|---|---|---|---|---|
| A01 | held profile dump of `fa` == harness-built dump (host dump with age 60, limit 10) | the product composes anything other than limit 10 (including the host dump changed elsewhere) | F: the composition formula `min(host limit, room)` at SA, no other profile change; ORACLE-free (literal-built dump) | that the derivation is exercised by anything but these two points | F |
| A02 | held profile dump of `fb` == harness-built dump (age 60, limit 30) | limit != 30 or any other leaf differs | F: second profile point distinct from A01 (defeats a constant); the freshness-extension route is real | live effect on `effective_profile_digest` alone | F |
| A03 | persisted base `catalogue_digest` (SA) == `own_commit(exp_A)` | digest differs | F: base digest equals an independent commitment | member sensitivity | F |
| A04 | persisted ECB `members.effective_profile_digest` (SA) == `own_commit(exp_A)` (ORACLE: independent recomputation over literal-built dump) | member value differs | F: the minted member equals the independent commitment of the effective profile (not host, not null) | variation by itself (A10 gives the second point) | F |
| A05 | persisted eff == persisted `catalogue_digest` (observed equality; expected `True`) | members differ | the `02` line 48 equality on a profile-bearing workflow (supports why isolation is impossible) | that the equality is checked at runtime (it is not) | F, K |
| A06 | persisted ECB `host_profile_digest` == `own_commit(host dump)` (ORACLE) | differs | F: host member is the HOST profile (limit 100), not the effective | independent isolation of the host member | F |
| A07 | host digest != effective digest (`True`) | equal | the fixture separates host from effective (limit 100 vs 10) | masked-host limit | F |
| A08 | persisted ECB `digest` == `H.my_digest(members, version)` (independent re-implementation) | mismatch | F: the member's own digest recomputes | nothing about the live comparison | F |
| A09 | live (SB) base `catalogue_digest` == `own_commit(exp_B)` (ORACLE) | differs | F: live base digest equals independent commitment, second point | independence from the approval | F |
| A10 | live ECB eff (SB) == `own_commit(exp_B)` (ORACLE) | differs | F: live member tracks the profile at the second point; with A04 it shows the member is not a constant and not the host digest (host is constant 100) | live derivation sensitivity ALONE (no run holds catalogue/approval fixed) | F, M(partial) |
| A11 | live eff == live `catalogue_digest` (`True`) | differ | the equality holds live too | runtime check of the equality | F, K |
| A12 | live ECB `digest` == `H.my_digest` | mismatch | live member digest recomputes | - | F |
| A13 | live ECB `host_profile_digest` == `own_commit(host dump)` (ORACLE) | differs | the host member is unchanged between worlds (the diff cannot be a host effect) | - | F, M |
| A14 | base diff == `["runtime_authority.approval_commitment","runtime_authority.catalogue_digest"]` | any other leaf, or a leaf missing (for example empty: the premise "base moves" is false) | M(joint): base pair moves, nothing else in the base binding (no manifest/proposal/grant leaf) | that the pair is the cause of the refusal (see A22) | M |
| A15 | ECB diff == `{runtime_authority.effective_configuration.digest, ...members.effective_profile_digest}` exactly | any other leaf (for example `families.0...` or `host_profile_digest`), or a leaf missing | M(joint): the ECB leaf set is exactly two (the case's narrowing; CE4 confirmed) | independence (A14 shows the base pair moved too) | M |
| A16 | `members.families` equal persisted vs live | differs | the family digest leaf is NOT in the diff (the CE4 claim; contradicts D-1 reviewer F2 "always moves families.0") | other families | M |
| A17 | `members.host_profile_digest` equal | differs | host leaf not in the diff | - | M |
| A18 | `members.scope` equal | differs | scope unchanged | - | M |
| A19 | `members.f4_scalars` equal | differs | scalars unchanged | - | M |
| A20 | `members.other_scalars` equal | differs | scalars unchanged | - | M |
| A21 | `members.observation_policy` equal | differs | observation policy unchanged | - | M |
| A22 | `claim_for(base, ecb, "effective_profile_digest")` == `"joint"` | returns `"isolated end-to-end"` (base empty would be required: contradicts I1-I4: adverse finding) | the case is recorded as JOINT by the frozen decision rule | any isolation claim; the rule is a classification, not a proof | M, I |
| A23 | `members.families` has exactly one row, slot `class_age` | different count/slot | the dedicated F5 workflow's family structure (so `families.0` in C3 is the class-age row) | - | K |
| A24 | `execute` raised `PermissionError` (exact type name) | no exception, or another type (for example a Registry refusal type) | E: fail closed (exception) | durable row (A26) | E |
| A25 | exception text == `authorization-critical inputs changed before effect` | differs | E: the frozen text from `bounded.py` | member attribution | E |
| A26 | new durable refusal rows == `[["authorization_binding_changed"]]` (exactly one row, exactly one reason) | extra/missing row or reason (for example `runtime_authority_approval_mismatch` also present: approval re-issue failed) | E: durable `EffectTimeRefusal` with the contract code, only that code | attribution to the effective member (the code is generic: `current != persisted.binding`); attribution is only by A14/A15 | E, G(partial: approval guard passed) |
| A27 | refusal `reason_vocabulary_version` rows == `["runtime-authority-reasons/0.1"]` | differs | vocabulary label as D-1 | - | E |
| A28 | new attempt rows 0 and total attempts after == 0 | any attempt row | E: no attempt created | - | E |
| A29 | destination calls 0 and destination snapshot unchanged | any call or change | E: destination untouched | - | E |
| A30 | journal counts: decisions [1,1], refusals [0,1], age_extensions [0,0] | any other count | E: exactly one new durable refusal, no other store growth in these collections, no age-extension row involved | other collections (check events, resolution checks are expected to grow and are not asserted) | E |
| A31 | persisted decision binding identical before and after the leg | changed | the refusal did not rewrite the decision | tamper evidence (unsigned store) | E |
| A32 | candidate classifier `configuration_binding_status` == `mismatch` (EVIDENCE ONLY, never the oracle) | other value | corroboration that the stored member differs from the live member | independent oracle | M (evidence-only) |

### 6.4 Case-level rows (not assertions)
`SNP-journal_before`, `SNP-journal_after`, `OBS-fixture_material` (both record texts' digests, same selection id/epoch), `OBS-complementary_diff` (full leaf sets, persisted and live ECB members, `own_commit` of expected dumps), `OBS-execute_outcome`, `EXC-execute` (type, text, traceback), plus the D-1 PREFLIGHT row. A leg without all of them cannot be scored PASS (protocol section 16).

### 6.5 Predicted outcome and claim permitted if all pass
Predicted: all preconditions hold; A01-A32 PASS. Claim permitted: "On CP 739efe7 / Registry pin a40fe755 / Python 3.11.18, `GovernedClassAgeWorkflow` with a host outage-extension limit of 100 and class age 60: a decision minted under Registry selection `{T1:70}` is refused at execute under a rebuilt workflow over `{T1:90}` with the approval re-issued (`PermissionError`, one durable `EffectTimeRefusal [authorization_binding_changed]`, no attempt, destination untouched). The complementary diff is base `{approval_commitment, catalogue_digest}`, ECB `{digest, effective_profile_digest}`. JOINT with `catalogue_digest` and `approval_commitment`; not independently isolated. Bounded technical record, same-lineage, not acceptance."

## 7. Control C0: `test_FXE_JOINT_C0` (SA unchanged executes exactly once)

Steps: world SA; `fa` constructed (approval bound), decided (`authorized`); restart workflow `f0` over the same SA material, same host, same store, approval untouched; live scratch mint under SA; complementary diff; `f0.execute`.
Preconditions: P01 `fa` constructed; P02 decide completes; P03 `authorized`; P04 `f0` constructed; P05 scratch mint completes; P06 scratch mint `authorized`.
| Id | Expected | Fails when | Establishes | Does NOT establish |
|---|---|---|---|---|
| C0-A01 | base diff `[]` | any leaf | the instrument reports no difference when none exists (no spurious base leaf from freshness stamps) | sensitivity |
| C0-A02 | ECB diff `[]` | any leaf | same for the ECB (checks that freshness fields do not leak into the ECB) | sensitivity |
| C0-A03 | `raised` None and `attempt_status` `acknowledged` | exception or other status | functional: the freshness-enabled fixture executes end to end (precondition for interpreting main) | - |
| C0-A04 | new refusal rows `[]` | any row | no spurious refusal | - |
| C0-A05 | destination calls == 1 | 0 or more than 1 | exactly one destination call | - |
| C0-A06 | classifier `bound` (evidence only) | other | corroboration | oracle |
| C0-A07 | persisted ECB eff == `own_commit(exp_A)` (ORACLE) | differs | second independent confirmation of A04 in a fresh world | - |
| C0-A08 | persisted `catalogue_digest` == `own_commit(exp_A)` (ORACLE) | differs | same for the base digest | - |
Dimensions: F only. If C0 fails the case is not interpretable (the lead scores main BLOCKED per protocol section 10 "control did not hold"; the harness itself scores the failing control rows FAIL, not BLOCKED, because C0 is a separate test; the lead applies the BLOCKED reading).

## 8. Control C1: `test_FXE_JOINT_C1` (approval NOT re-issued: guard first)

Steps: world SA decided; `fb` over SB constructed with `rebind=False` (approval still bound to the SA profile); `fb.execute`.
Preconditions: P01 `fa` constructed; P02 decide completes; P03 `authorized`; P04 `fb` constructed (Registry accepts 90 > 60); P05 profile dump leaf diff A vs B == `["freshness.max_age_extension_seconds"]`.
| Id | Expected | Fails when | Establishes | Does NOT establish |
|---|---|---|---|---|
| C1-A01 | `PermissionError` | other | fails closed | - |
| C1-A02 | text `authorization-critical inputs changed before effect` | differs | same raise site as main | - |
| C1-A03 | new refusal rows `[["runtime_authority_approval_mismatch"]]` exactly | extra reason (for example `authorization_binding_changed`) or other | G: the base approval guard refuses first and alone | behaviour of the ECB member |
| C1-A04 | `authorization_binding_changed` absent from every new refusal | present | G: the ECB comparison did not add its code (not consulted) | proof the ECB was not evaluated internally (inferred from the code's absence, as D-1 Q3-E1) |
| C1-A05 | vocabulary `["runtime-authority-reasons/0.1"]` | differs | label | - |
| C1-A06 | new attempts 0, total attempts 0 | any | no attempt | - |
| C1-A07 | destination calls 0, unchanged | any | destination untouched | - |
| C1-A08 | journal decisions [1,1], refusals [0,1] | other | exactly one durable refusal | - |
Dimensions: G CAN, E CAN only to the guard boundary; M and I NOT APPLICABLE. This is guard-first evidence; it says nothing about the later effective-member comparison.

## 9. Control C2: `test_FXE_JOINT_C2` (neutral re-signed SA')

Steps: world SA decided; SA' = same record content re-signed under `selection_id sel-test-2`, `epoch 2`; workflow over SA' constructed (approval untouched, profile identical so commitment unchanged); scratch mint under SA'; complementary diff; execute.
Preconditions: P01 record texts equal, selection texts differ, ids `[sel-test-1, sel-test-2]`, epochs `[1,2]`; P02 `fa` constructed; P03 decide completes; P04 `authorized`; P05 SA' workflow constructed (Registry accepts the re-signed selection; UNVERIFIED at pin `a40fe755`, developer test l05 on pin `6f600ab1`); P06 held profile dump equal to SA's; P07 scratch mint completes; P08 `authorized`.
| Id | Expected | Fails when | Establishes | Does NOT establish |
|---|---|---|---|---|
| C2-A01 | base diff `[]` | any | rotation does not move the base binding | - |
| C2-A02 | ECB diff `[]` | any | rotation does not move the ECB (selection identity is not a member) | - |
| C2-A03 | executes `acknowledged`, no exception | other | rotation alone does not refuse | - |
| C2-A04 | new refusal rows `[]` | any | no refusal | - |
| C2-A05 | destination calls == 1 | other | - | - |
| C2-A06 | classifier `bound` (evidence only) | other | - | oracle |
| C2-A07 | identity `effective_policy_digest` equal SA vs SA' | differs | same effective policy identity | - |
Dimensions: F (control). Purpose: the SA vs SB difference in main is a record-CONTENT difference (raw value), not a selection-identity artefact.

## 10. Control C3: `test_FXE_JOINT_C3` (effective-map change widens the diff)

Steps: world SA decided; `fc` over SC (`{T1:50}`) constructed with the approval re-issued; scratch mint under SC; complementary diff; execute.
Preconditions: P01 `fa` constructed; P02 decide completes; P03 `authorized`; P04 `fc` constructed; P05 scratch mint completes; P06 `authorized`.
Derived exact diff (frozen): base `{runtime_authority.approval_commitment, runtime_authority.catalogue_digest}`; ECB `{digest, members.effective_profile_digest, members.families.0.effective_policy_digest}`. The profile dump differs from SA in `actions.<aid>.max_status_age_seconds` (50 vs 60) and `freshness.max_age_extension_seconds` (0 vs 10); `host_profile_digest` and the other members unchanged. This is the same ECB leaf set D-1 Q3-E2 observed (age 20, no freshness), so C3 doubles as a cross-check that adding the host freshness profile does not change the families leaf behaviour.
| Id | Expected | Fails when | Establishes | Does NOT establish |
|---|---|---|---|---|
| C3-A01 | held SC dump == harness-built dump (age 50, limit 0) | differs | F: formula at a third point incl. the `max(0, ...)` floor | - |
| C3-A02 | identity effective `{T1:50}` | differs | - | - |
| C3-A03 | base diff == base pair | other | joint base pair | - |
| C3-A04 | ECB diff == three leaves above | other | M(joint): the families leaf is observable and is what the main case removes | independent isolation |
| C3-A05 | `host_profile_digest` equal | differs | host leaf absent | - |
| C3-A06 | `claim_for(...)` == `joint` | other | classification | - |
| C3-A07 | `PermissionError` | other | E | - |
| C3-A08 | new refusal rows `[["authorization_binding_changed"]]` | other | E: durable refusal | attribution (generic code) |
| C3-A09 | new attempts 0 and total 0 | any | no attempt | - |
| C3-A10 | destination calls 0, unchanged | any | untouched | - |
Dimensions: M partial/joint, E CAN (joint), I CANNOT.

## 11. Failure conditions at case level (protocol section 12)
FAIL (case interpretable): any assertion A01-A32 failing; refusal reasons/exception differ from section 3; the destination is called; an attempt row appears; the base diff is not exactly the pair; the ECB diff is not exactly two leaves (or a families/host leaf appears: then the CE4 premise is falsified and that is the finding); `claim_for` returns `isolated end-to-end` (adverse; contradicts I1-I4); a control (C0..C3) assertion fails while its preconditions held.
BLOCKED (case not interpreted): any `P` precondition fails, in particular the Registry/adapter refuses a record value above the host (P04) or the extension limit is not composed as predicted so the dumps do not differ exactly in `freshness.max_age_extension_seconds` (P09), or construction/decide raises. The harness records a `BLOCKED` row, a `GATE` row, and `NOT EXECUTED` rows for the unreached ids, then stops the leg.
Never revised after the fact; correction only by a versioned successor.

## 12. Source uncertainties that could invalidate the fixture (UNVERIFIED, flagged)
1. U-A: a freshness-enabled GOVERNED workflow decides and executes on the tenant fixtures under `H.patch_clock`. Source support: `tests/test_final3_composed_binding.py::test_e01` (freshness profile, decide `authorized`, execute `acknowledged`) and `test_freshness.py` (non-governed). No developer test combines `GovernedClassAgeWorkflow` with a freshness profile through decide+execute (the F5 tests with freshness stop at profile checks and `selection_changed`). Mitigation: C0 (SA unchanged) is the control; its failure makes the case BLOCKED.
2. U-B: the pinned Registry `a40fe755` accepts r08-v2 record values above the host and a re-signed SA' (`epoch 2`). Source read: `compose_f5` `min` composition at the pin; developer tests g02/x02/l05 are on pin `6f600ab1`, not `a40fe755`.
3. U-C: `FreshnessProfile` in the host does not by itself add base-binding leaves (the binding carries `runtime_authority = extension` built from `profile`/`context` only; no freshness-derived member read in `_resolve`'s binding construction at `bounded.py:2560-2640`). C0-A01/A02 detect a spurious leaf.
4. U-D: the class age bound in decisions with freshness is `_class_age_bound` over zero extension rows (bound = 60); status ages in the tenant fixture equal NOW, so the status check passes. No extension row is recorded; A30 asserts `age_extensions` stays 0.
5. U-E: the refusal vocabulary label is `0.1` (code not in `CODES_ADDED_IN_0_2`); D-1 observed the same label for the same code without freshness; the label depends only on the reasons list.
6. U-F: a restart workflow over the same store with the same Registry material and approval executes (C0); same pattern as D-1 Q3-H0.
7. U-G: `age_extensions` attribute exists on the loaded run record (read via `getattr` with default 0; if absent, A30's age-extension component passes vacuously, which weakens only that sub-claim).
8. U-H: the candidate classifier values (`mismatch`, `bound`) are evidence only; a deviation there would FAIL A32/C0-A06/C2-A06 without implying a product defect in the refusal path.
9. U-I: the fresh-clock caveat: under freshness the dispatch gate compares the patched `_now` to a deadline computed from the same patched clock and also a real monotonic elapsed time (`bounded.py:1410-1432`); acceptable only if the control executes within the 60 s bound of real time (a slow runner could produce `check_expired_before_dispatch` in C0/C2, which the assertions would record as FAIL, not BLOCKED).
10. U-J: `bind_approval` mutates the shared resolver approvals; each test has its own world, so ordering across tests is irrelevant; inside main, the SA mint happens before the SB re-issue (by construction of the steps).
11. Same-lineage and non-blind: predictions informed by the dossier and D-1 (protocol section 2).

## 13. Exclusions honoured
No guard disabled, patched or bypassed; the only patch is the fixed synthetic clock of D-1; no store write, graft, reseal or forged member; no seam patch; approval re-issue only through `bind_approval`; no network; synthetic data; no pin-export or claim leg; no mutant.


---
# Appendix C: cases-domain.md (N-CLAIM-JOINT)

# N-CLAIM-JOINT - authority-domain natural JOINT refusal on the claim-issuance leg (Worker D draft, BOUNDED-v1 section 7.5)

Status: DRAFT for the lead's freeze; written from source only, nothing executed (allowed: reading source, `py_compile`, `pytest --collect-only`). Same session lineage as the lead: NOT independent. Implements `harness/test_bq_domain.py` 1:1 (every expected value is a literal in that file; none is computed from an observation).
Subject: Control Plane `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69`, Registry pin `a40fe755`, Python 3.11.18. Instruments reused unmodified: `d1_lib.py` (sha256 `5ec947ba...`), `orig_harness.py`.

## 0. What this case is, and is not

**JOINT evidence.** It does **NOT** establish independently isolated `scope.authority_domain` evidence: on every supported route a changed domain also moves `manifest_digest` and `proposal_commitment` (the domain lives in the manifest, which the proposal commits to), so the base binding differs too. It is the claim-leg analogue of D-1 Q2-A2(ii). It is not a pin-export case, not a graft, not a seam patch, and discharges nothing under Registry record 12 item 1 (which asks for execute AND pin-export).

It does NOT prove: (a) that the live derivation of the ECB leaf alone is what causes the refusal (the refusal would occur with the leaf deleted, because the base diff is non-empty); (b) live-derivation sensitivity of the leaf alone (no mutant is run); (c) anything about pin-export; (d) anything about graft or stamping-side mutants; (e) the `provision_*` atomic-sink profile beyond "sink not called on refusal" (record 12 item 7, Class B); (f) other families, `policy_binding` claims, the profile-bearing claim branch (journal mode), other Python versions, other commits.

## 1. Source derivation (739efe7; `CP` = `src/agent_control_plane/`)

Fixture: D-1 `domain_world` over the F4-dedicated `GovernedAgeWorkflow` (no runtime-authority profile, no policy_binding). Claim call chain: `materialize_local_execution_claim` / `provision_local_execution_claim` -> `_materialize_under_handoff` (`CP/local_authority_effect.py:404-565`).

1. Persisted-decision entry guards (`:426-430`): `workflow.records.decision(id) == decision`, `authorized`, binding present. Both legs pass the decision read through the Y workflow's own store reader.
2. No `_gl_revalidate` / `_gl_reverify` on this leg (only `GovernedLifecycle.execute/decide` call them, `registry_governed_lifecycle.py:330-338`): so no `manifest_authority_changed` / `selection_changed` guard. A Y workflow over the X store is admitted at construction only (Registry selection must be signed for Y, else `RegistrySelectionRefused` at construction = BLOCKED here).
3. `journal = workflow.runtime_authority_profile is not None` is False (`:443`): `workflow._resolve(frozen_proposal, now, inputs=inputs)` is called with default `stage="decision"`, `decision=None`.
4. Base resolve = `BoundedAuthorizationWorkflow._resolve_inputs` (`bounded.py:2239-2606`): reasons ACCUMULATE; any reason => `return sorted(set(reasons)), None` (`:2567-2568`). Reasons relevant here: `manifest_digest_mismatch` (`:2618-2619`, computed first via `_manifest_mismatches`, `:2266`), `authority_domain_mismatch` (`:2297-2298`), per-record `*_binding_mismatch` (`_same_institution`), `approval_operation_binding_mismatch` (`:2509-2510`).
5. Governed override (`registry_governed_lifecycle.py:263-285`): `if reasons or binding is None: return` (`:267-268`) - ECB never consulted when a base reason exists. Otherwise `target = decision if decision is not None else _EXEC_DECISION.get()` is `None` outside `execute` (contextvar default None, `:35`); `stage == "decision" and target is None` => **MINT branch** (`:273-274`): the live ECB member is stamped into the rebuilt binding and returned with NO classification and NO `authorization_binding_changed` reason. This is the "claim non-journal branch" (Worker D static report section 4.1; D-2 called it unexercised; original A17 control shows a claim IS issuable on this fixture family, `A17_bad_types_claim_route_no_profile control_unperturbed_claim = claimed`).
6. `_binding_issuance_reasons` is skipped (no `policy_binding`/`expected_*`). Then `workflow._record_check(inputs, now, reasons, "claim")` (`:454`) -> `BoundedRecordStore.record_resolution_check` (`bounded.py:627-661`): UNCONDITIONALLY appends one `ResolutionCheck(stage="claim", reasons=<sorted reasons>)` row and advances `input_time_floors` (also without a profile). This row is written BEFORE the comparison, so it is also written on refusal.
7. Comparison `reasons or current is None or current != decision.binding` (`:455`); on refusal the branch at `:456-457` needs `binding_reasons` (none) so the message is the generic `PermissionError("authorization-critical inputs changed before claim issuance")` (`:458`), type exactly `PermissionError`. No `EffectTimeRefusal` is appended anywhere on this leg (that is execute-only, `bounded.py:1694-1711`); no attempt, no claim, no `provision(claim)` call (`:565-566` is after the snapshot validation and claim construction, which are after the raise).
8. Consequence for "which reason names the binding change on the claim path": **none**. On this branch the binding change surfaces ONLY as the equality at `:455`; the exception text is generic, the claim `ResolutionCheck.reasons` is `[]` (no base reason), and `authorization_binding_changed` is not emitted (it is added only at `registry_governed_lifecycle.py:283-284` in the non-mint branch). Attribution to the ECB leaf is by the complementary diff only (D-1 convention).
9. Which commitments move for P_Y vs D_X on the claim path: the rebuilt binding for P_Y is produced by the same `_resolve_inputs` + mint as `decide` (default stage, same fixtures, same clock), so the complementary instrument `d1_lib.live_binding` (genuine `decide` of P_Y in world Y over a scratch store) is the claim path's `current`. Derived: base diff `{manifest_digest, proposal_commitment}` (domain is inside the committed manifest, `bounded.py:86-88`; proposal commits to `manifest_digest`, `:2476`); approval commitment fields do not exist on the no-profile binding (`runtime_authority` extension is None apart from the ECB), `binding_digest`/`catalogue_digest`/`approval_commitment` are pin-fixture-only and absent here. Matches D-1 Q2-A1/A2(ii) (same fixtures, same worlds). ECB diff `{digest, members.scope.authority_domain}` (domain is the only ECB member that depends on the manifest; `registry_governed_lifecycle.py:199-206`, `effective_configuration_binding.py:130-132`). Not moved: other ECB members (scalars are host constants identical across worlds; `families` none declared; `host_profile_digest`/`effective_profile_digest` constant null in F4-dedicated).

## 2. World construction (main)

* World X: `L.domain_world(E, tmp, "x", "customer-refunds")`, `L.domain_mint` -> genuine authorized D_X (persisted in `x/run.json`).
* World Y: `L.domain_world(E, tmp, "y", "other-domain")`: manifest action authority_context.authority_domain = Y (valid manifest: proposal manifest_digest = H(M_Y)); resolver with every domain-bearing record retargeted to Y; Registry F4 selection re-signed for Y (disclosed fixture signing, `H.f4_material(..., domain=Y)`); proposal P_Y with `manifest_digest = H(M_Y)`; approvals re-issued: the resolver is built FOR P_Y so its approval records carry `commitment(P_Y)` (P04 checks this; no `bind_approval` is needed because the no-profile F4 fixture has no profile commitment). Genuinely minted in its own store (P02).
* Claim leg: a COPY of the X store directory (`shutil.copytree`, a filesystem copy of a genuine production-written store; no write into any store, no edit of any row), restarted under the Y workflow `L.construct_domain(E, w2, copy)` (the same supported restart as D-1 Q2-A2(ii)); persisted D_X read with `flow.records.decision`; claim issuance for **P_Y** against **D_X**.

## 3. Validity preconditions (BLOCKED if any fails; no outcome assertion is evaluated after a failed gate)

| id | precondition | expected |
|---|---|---|
| P01 | X mints authorized | `{"result":"authorized","reasons":[]}` |
| P02 | Y mints authorized for its own proposal | same |
| P03 | manifest domains | `["customer-refunds","other-domain"]` |
| P04 | approvals re-issued for Y: all Y approvals bound to commitment(P_Y); commitment(P_X) != commitment(P_Y); P_Y.manifest_digest == H(M_Y) (subject's `commitment`); P_X.manifest_digest != P_Y.manifest_digest | all four true |
| P05 | genuine `decide(P_Y)` in world Y (scratch store) | authorized, reasons `[]` |
| C01 | inline control: unperturbed X claim via `provision_local_execution_claim` over a separate copy issues exactly one claim (sink called once, `verify_local_execution_claim` True) | `{"issued":true,"sink_calls":1,"verified":true}` |
| P06 | D_X readable by the Y workflow's store reader, authorized | `{"found":true,"result":"authorized"}` |
| P07 | the claim path reached the comparison: the claim `ResolutionCheck` row written by the leg has stage `claim` and `reasons == []` (no earlier base reason; also excludes `input_observation_time_regressed`) | `{"n_new":1,"stage":"claim","reasons":[]}` |
| P08 | same as P07 for route 2 (provision) | same |

Construction failure (exception while building X/Y worlds, `construct_domain` over the copy, e.g. `RegistrySelectionRefused`) is recorded as `P00`/EXCEPTION and is BLOCKED, never a product FAIL. No guard may be disabled to get past a precondition (stop condition).

## 4. Steps (main), exact order

1. Build+mint X, build+mint Y (P01-P04). 2. `live_binding(decide(P_Y), Y world, scratch)`; P05; persisted binding of D_X from `x/run.json`; `split_diff` => `(base, ecb)`; classification `claim_for(base,ecb)`; SNAPSHOT S01. 3. Inline control C01 on `ctl_x` (copy of X store, X workflow, provision route, claim id `bq-claim-main-ctl`). 4. Copy `claim_main`; Y workflow over it; P06. 5. Route 1: `materialize_local_execution_claim(flow_y, P_Y, D_X, now=E.NOW, claim_id="bq-claim-main-m")`, store before/after docs, destination snapshot, exception captured; P07. 6. Route 2 on a second fresh copy `claim_main_prov`: `provision_local_execution_claim(..., provision=sink.append, claim_id="bq-claim-main-p")`; P08. 7. Assertions A01-A15 (route 1 + diff), A20-A23 (route 2). 8. Evidence-only O01 (candidate classifier, never scored), O02 (input_time_floors movement).
Controls (separate tests): **C0** unperturbed X claim (materialize and provision) incl. live X diff == `[]`/`[]`; **C1** world Y with P_X (guard-first); **C2** neutral rebuild (second X world, same domain, new objects) claims; **CY** (supplementary, not a precondition of main) Y issues a claim for its own decision.

## 5. Frozen reason strings and messages

* Claim refusal exception: type exactly `PermissionError`, `str == "authorization-critical inputs changed before claim issuance"` (main, route 2, C1). Same text for base-reason refusals and for the binding-equality refusal; it cannot discriminate between them.
* Main: claim `ResolutionCheck.reasons == []` (the binding change is NOT a reason on this branch); **no** refusal token anywhere; `authorization_binding_changed` must NOT appear in the exception text or the check reasons (A09). The binding change is named only by the complementary diff.
* C1 (X proposal P_X in the consistent Y world; Y approvals bound to P_Y not P_X): claim `ResolutionCheck.reasons == ["approval_operation_binding_mismatch","manifest_digest_mismatch"]` (sorted; derived from `bounded.py:2509-2510`, `:2618-2619`; identical to D-1 Q2-A2(i) observed). First guard in CODE order: `manifest_digest_mismatch` (`_manifest_mismatches`, first call in `_resolve_inputs`, `bounded.py:2266`); the sorted reason list is what is observable. Frozen as ABSENT: `authority_domain_mismatch` (resolver and manifest agree on Y; it appears only on the A25(a)-style inconsistent route, D-1 Q2-A2(iii)) and `authorization_binding_changed`.

## 6. ASSERTION INVENTORY - main (`test_N_CLAIM_JOINT_main`)

Dimension key: 1 functional correctness, 2 member sensitivity, 3 guard-order evidence, 4 end-to-end refusal, 5 independent isolation, 6 contract coverage. Row ids are `N-CLAIM-JOINT-<id>`; evidence rows carry `assertion_id`, `bq_kind`, `expected`, `observed`, `result`. A failing assertion with all P/C01 rows passed = FAIL.

| id | expected (literal) | fails when | establishes (dim) | does NOT establish |
|---|---|---|---|---|
| A01 | exception type `"PermissionError"` | claim returned, or a subclass/other type (e.g. `RegistrySelectionRefused`, `ValueError`) | 4 (fails closed, as an exception of the contract type); 3 (not a construction-time Registry refusal) | which guard refused |
| A02 | message `"authorization-critical inputs changed before claim issuance"` | any other text (e.g. "policy binding refused ...", "decision is not ...") | 4, 6 (claim leg, no-binding branch of `:455-458`) | attribution to the ECB leaf (same text for base reasons) |
| A03 | `claim_returned == false` | a claim object returned | 4 (no claim emitted) | - |
| A04 | refusals delta `0` | any `EffectTimeRefusal`/refusal row | 4, 6 (successor 06/11 claim semantics: no refusal write) | that the frozen-literal 03 expectation (durable refusal) is met (it is not required on the claim leg) |
| A05 | non-zero store deltas `== {"resolution_checks": 1}` | any attempt/decision/observation/reconciliation/closeout/new ledger row, or resolution_checks != +1 | 4 (no state widened; only the pre-existing journal row) | that the journal write is desirable |
| A06 | persisted `decisions` section byte-equal before/after | any decision rewritten | 4 (no authorization widening) | - |
| A07 | top-level store key set unchanged | a new section appears | 4 | - |
| A08 | destination calls delta `0` and snapshot unchanged | any destination call or change | 4 (destination untouched) | - |
| A09 | binding-change token absent in exception text and in claim check reasons (`{false,false}`) | `authorization_binding_changed` appears | 3 (documents that no reason code names the ECB change on this branch) | - |
| A10 | base diff `== ["manifest_digest","proposal_commitment"]` | any other leaf set (empty would mean the instrument is wrong or the domain were not in the manifest digest) | 2 (JOINT: base moved), 3 (shows why isolation is impossible here) | isolation (it is the proof of non-isolation) |
| A11 | ECB diff `== [".digest", ".members.scope.authority_domain"]` under `runtime_authority.effective_configuration` | extra or missing leaf (e.g. a scalar or families leaf) | 2 (member sensitivity at the diff level: the domain leaf and digest moved, nothing else in the ECB) | that the leaf alone causes the refusal |
| A12 | ECB diff contains the `scope.authority_domain` leaf | missing | 2 | - |
| A13 | classification `"joint"` | `"isolated end-to-end"` (would contradict structure) | 2, 5 (records the non-isolation verdict) | - |
| A14 | persisted leaf `"customer-refunds"`, live leaf `"other-domain"` | other values | 1, 2 (component: leaf equals the manifest domain of each world) | - |
| A15 | persisted and live ECB digests equal the independent recomputation `H.my_digest` | mismatch | 1 | - |
| A20 | route 2: `["PermissionError", <generic message>]` | other | 4, 6 (provision interface also refuses) | provision atomic profile beyond refusal |
| A21 | route 2: sink calls `0`, no claim returned | sink called | 4 ("no provision call") | - |
| A22 | route 2: store deltas `{"resolution_checks":1}`, refusals `0`, decisions byte-equal | any other write | 4 | - |
| A23 | route 2: destination calls `0`, unchanged | any call | 4 | - |

Preconditions P01-P08/C01 are rows too (kind PRECONDITION/CONTROL). SNAPSHOT rows: `main-m.leg`, `main-p.leg`, `C01.leg` (store deltas, new ResolutionCheck rows (stage, reasons), destination calls, sink calls, claim summary, exception type/text, row counts before/after, `input_time_floors` equality), `S01` (base_diff, ecb_diff, classification). EXCEPTION rows carry type, `str`, full traceback (an expected `PermissionError` too). OBSERVATION rows O01/O02 are evidence only (classifier status in the Y workflow expected "mismatch" by source reading, NOT scored).

Predicted outcome (frozen): all of A01-A23 PASS; classification `joint`; ECB reached by the equality at `local_authority_effect.py:455` with zero base reasons.
Claim permitted if all pass: "On the claim-issuance leg, F4-dedicated fixture, a natural supported rebuild of the live domain (Y) with re-issued approvals makes the persisted X decision unclaimable (`PermissionError`, no claim, no refusal write, sink and destination untouched), with the base binding differing in `{manifest_digest, proposal_commitment}` and the ECB in `{digest, members.scope.authority_domain}`: JOINT, not isolated."
Case-level dimension table (all PASS): 1 ESTABLISHED (control claims; leaf equals manifest domain; digests recompute); 2 PARTIAL/JOINT (ECB diff exactly digest+leaf, base diff also moved); 3 ESTABLISHED for "base guards pass, comparison is the refuser, no reason code names it" on this branch; 4 ESTABLISHED (claim leg, successor semantics); **5 NOT ESTABLISHED (JOINT, no independent isolation)**; 6 claim leg, F4-dedicated no-profile (mint branch), natural joint; NOT pin-export, NOT graft, NOT seam-patch, NOT profile/journal branch, NOT frozen-literal 03.

## 7. ASSERTION INVENTORY - controls

**C0** (`test_N_CLAIM_JOINT_C0`): C0-P01/P02 (X mints; live decide authorized). C0-A00 base `[]`, ECB `[]` (unperturbed live X == persisted). For each route r in {m = materialize, p = provision+sink} with prefix `C0-m-`/`C0-p-`: A01 claim issued (type `TenantLocalExecutionClaim`, no exception); A02 `verify_local_execution_claim` True; A03 claim fields `{decision_id: D_X id, authority_domain: "customer-refunds", manifest_digest: P_X digest, tenant_id: "tenant-alpha", claim_id: <given>, profile: "urn:cognous:profiles:local-authority-effect:0.1.0-proposed"}`; A04 exactly one new `ResolutionCheck` row, stage `claim`, reasons `[]`; A05 non-zero deltas `{"resolution_checks":1}`; A06 decisions byte-equal; A07 destination calls 0 and unchanged; A08 sink: materialize none; provision called once with the returned claim. Fails -> if main's C01 also fails, main is BLOCKED; C0 FAIL means the unperturbed claim did not behave (BLOCKED for the whole case).
**C1** (`test_N_CLAIM_JOINT_C1`): P01-P04 plus C1-P05. A01 `["PermissionError", generic message]`; A02 no claim; A03 one new claim check row with `reasons == ["approval_operation_binding_mismatch","manifest_digest_mismatch"]`; A04 `authority_domain_mismatch` and the binding-change token absent; A05 only `resolution_checks +1`, refusals 0, decisions byte-equal; A06 destination untouched. O01 (evidence only): genuine `decide(P_X)` in Y (scratch) result/reasons. Establishes dimension 3 guard-first (base guard refuses before the ECB equality can matter); NOT member sensitivity.
**C2** (`test_N_CLAIM_JOINT_C2`): C2-P01-P03 (neutral rebuild: same domain/proposal/manifest commitments, distinct resolver objects; live decide authorized). C2-A00 base `[]`, ECB `[]`; A01-A08 as C0 (materialize). Establishes that the restart/copy/rebuild path is neutral (a claim issues), so in main the difference is the domain.
**CY** (`test_N_CLAIM_JOINT_CY`, supplementary; the lead may drop it): Y claims for its own decision over a copy of Y's store; A01-A08 as C0 with domain `"other-domain"`. Not a precondition of main; shows the Y fixture supports the claim interface at all. A failure is recorded and does not change main's interpretation.

## 8. Failure conditions (case level)

FAIL (preconditions and C01 held): any A-row fails: claim issued; exception other than `PermissionError` with the generic text; any refusal/attempt/claim/decision row written; sink or destination called; base diff or ECB diff leaf set differs from the frozen set; classification `isolated end-to-end`.
BLOCKED: any P/C01 row fails, including P07/P08 (a base reason exists, e.g. `input_observation_time_regressed`, so the ECB equality was not what refused); construction/mint failure of either world; control claim not issued; Y Registry selection refused at construction. STOP: any need to disable/patch a guard, any network use, any store write other than production writes (the claim's own `ResolutionCheck` row is a production write).

## 9. Evidence rows written

Per assertion one row via `d1_lib.rec(case="N-CLAIM-JOINT", kind=CHECK_PASS|CHECK_FAIL, check=<id>, ...)` with `protocol, run, case_id, test, assertion_id, bq_kind (PRECONDITION|CONTROL|ASSERTION|OBSERVATION|SNAPSHOT|EXCEPTION), desc, expected, observed, result (PASS|FAIL|n/a)`; BLOCKED row `kind=BLOCKED, failed_preconditions`; preflight OBSERVATION. Rows go to `$D1_EVIDENCE_DIR/d1_evidence.jsonl` (the lead's wrapper maps to `bq_evidence.jsonl`). Counts (main): 9 P/C01 rows (P01-P08, C01) + 19 assertions (A01-A15, A20-A23) + 6 SNAPSHOT/EXCEPTION/OBSERVATION groups.

## 10. Source uncertainties that could invalidate the fixture (all UNVERIFIED by execution)

1. **Claim control on the domain-world fixture.** Original A17 shows a claim on the stock F4 world (`H.new_case`); `domain_world` X is built differently (`L.domain_world`, manifest copy, proposal rebuilt with `type(p0)(**...)`) and has never issued a claim. If `_validate_issuance_snapshot` or the resolver handoff refuses there, C01/C0/C2 fail => BLOCKED (not a product FAIL).
2. **Claim on the retargeted Y fixture (CY).** Not needed for main (refusal precedes snapshot validation `:460-466`); CY may fail on retargeted snapshot data. Supplementary only.
3. **`input_observation_time_regressed`** could be added by `record_resolution_check` if the copied X store's floors exceed the Y resolver's `observed_at` (all fixtures use `NOW.isoformat()`, so equal; D-1 Q2-A2(ii) reached the ECB equality on the same shape for execute). P07/P08 detect it => BLOCKED.
4. **Equivalence of the instrument.** The live binding is measured by `decide(P_Y)` in a scratch store; the claim path's own `current` is not directly observable (no public accessor). Equality of the two is a source inference (same `_resolve_inputs`, same mint branch, same clock). A divergence would surface as A10/A11 mismatching and would not be detectable as "wrong instrument" without a patch (not allowed).
5. **ResolutionCheck write on refusal** (`record_resolution_check` unconditional) is a source reading; A04-A08 are written against it. If a contrary write order exists, the store-delta assertions fail (a prediction error, scored FAIL).
6. **`provision_local_execution_claim` over the no-profile governed workflow** has never been exercised (record 12 item 7, Class B). Route 2 is separate so a surprise there is isolated to A20-A23/P08 (P08 failure BLOCKS the case; consider moving route 2 to a separate test if the lead wants main independent of it).
7. **Registry material for Y**: `H.f4_material(..., domain=Y)` re-signed with the disclosed fixture key; verification at construction is production code. A `selection_scope_mismatch` would BLOCK.
8. `L.retarget` replaces only values exactly equal to `"customer-refunds"`; a domain-bearing field it misses would produce `authority_domain_mismatch`/`*_binding_mismatch` in `decide` => P02/P05 fail => BLOCKED. D-1 Q2-A1/A2 already minted and executed on the same Y world, so the risk is for claim-specific records only (`authority_effect_snapshot`).
9. Wording: the dossier says "approvals re-issued" - realized here by building the Y resolver for P_Y, exactly as D-1 `domain_world` (no `bind_approval`; the no-profile fixture has no profile commitment). C1 uses "X proposal, Y approvals bound to P_Y"; it does not replay X-domain approvals (those would add `approval_binding_mismatch`, a different route).

