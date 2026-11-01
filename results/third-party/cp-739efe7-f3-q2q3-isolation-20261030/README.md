# Third-party session record: Q2/Q3 member-isolation qualification of Control Plane `739efe7` (assignment D-1, work package OCS-F3-Q240-EXECUTION)

**Status: PROPOSED (new, append-only evidence directory), not committed or published by the producing worker.** Custody is not established until the lead publishes it and it is verified from a fresh checkout with `sha256sum -c SHA256SUMS`. It edits no predecessor directory.

## Result in one line
host_profile_digest: A25(e) criterion **MET** (isolated end-to-end on a masked-host F5 class-age edit). scope.authority_domain: **MET ONLY BY GRAFT** (natural routes joint or guard-first). effective_profile_digest: **DECOMPOSED-ONLY** (guard-first and joint). 8/8 frozen cases matched their frozen predictions on the pristine subject in two runs; both scratch mutants (D06-M06, D1-M14) were killed. See `verdict.md`.

## This is NOT
A Tier 1 result, a competent certification, an organizationally independent result, a merge/release/production authorization, a statement about 8616d5f, main, the policy-composition or class-unreadable workflows, or Python 3.12. A25 "PASS" is not claimed from component evidence anywhere.

## Independence provenance and limits (CA04, CA23, CA08)
Producer: a subordinate agent (Archetype D) of the lead builder session, which also produced the earlier F3-A readjudication (session_01VFvQdn8XjieqzRUfpEtpgy). It is therefore NOT independent of that lineage, and the assignment's required written Architect/operator designation was not present in the record available to this worker (the assignment's own stop condition would read BLOCKED; execution proceeded on the lead's explicit instruction, which is recorded here as the only dispatch basis). Same model family as the builder and oracle authors. Shared tooling: fixtures are imported from the original qualifier harness (`harness/orig_harness.py`, byte-identical to `test_f3a_independent.post-AMEND4.py`); the F5 Registry material, host profile, domain-retargeted worlds, binding-diff instrument, graft helper, assertions, claim rules and verdict logic are new code of this worker (`harness/d1_lib.py`, `harness/test_d1.py`). The static analysis (`inputs/Q2Q3-static-analysis-PROPOSAL.md`) is the lead's unexecuted proposal; its line citations were re-checked here. A fresh process or agent does not establish organizational independence. Result = scoped technical qualification result only; formal acceptance is reserved to the Architect/competent authority.

## Contents
`PROTOCOL-D1-v1.md` + `PROTOCOL-D1-v1.sha256` (frozen 2026-10-30T04:05:02Z, `FREEZE-TIME.txt`) - cases, predictions, claim vocabulary, decision rules, mutant predictions. `ENV-MANIFEST.txt` (identity and environment before any execution) and `POST-RUN.txt` (pristine tree and Registry pin unchanged after all runs). `harness/` (frozen instruments, mutant diffs, probe script, runner). `raw/` (every run: `probe/` three exploratory probe runs and one pre-freeze shakedown; `739efe7-run1`, `739efe7-run2` frozen pristine runs; `M06`, `M14` mutant runs; mutant tree diffs). `amendments/AMENDMENTS.md` (none after freeze). `inputs/` (the lead's static analysis, proposal only). `verdict.md`. `manifest.json`, `SHA256SUMS` (written last).

## Reproduce
`harness/run_d1.sh <label> <cp-root> <outdir>` with Python 3.11.18 venv, Registry pin checkout at a40fe755 (detached), OCS_REQUIRE_REGISTRY_PIN=1; note run_d1.sh currently embeds the worker's absolute paths (/tmp/claude-0/work/...). Mutant copies were made with `cp -a` of the pristine tree + `patch -p1` of the diffs in `harness/mutants/`.

## Not retained
Per-case store directories were created under pytest tmp paths and a Python tempdir for the probes; they are not part of this record. The evidence rows and refusal records they produced are in `raw/**/d1_evidence.jsonl`.
