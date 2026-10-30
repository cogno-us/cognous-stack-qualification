# Adversarial review of D-1 (Q2/Q3 isolation) evidence, CP 739efe7
Reviewer: read-only subordinate of the lead builder session. NOT independent certification. No opinion on F3-A formal acceptance.
Evidence dir untouched (`sha256sum -c SHA256SUMS` clean before and after). One re-run done into a NEW scratch dir (see 5).

## Findings

F1 [should-fix] "Frozen predictions" were not blind. Oracle/expectations were formed after probes and after an all-pass shakedown.
- Evidence: raw/probe/probe-*040142Z.stdout already shows E1 = [runtime_authority_approval_mismatch] and E2 = [authorization_binding_changed] with the exact base/ECB split. raw/probe/shakedown-pre-freeze (04:03:50-52Z) passed 8/8 and 104 checks, identical to frozen runs; test_d1.py/run_d1.sh mtimes (04:03:50.88) coincide with the shakedown start; FREEZE 04:05:02. Protocol sec.4 headline says "predictions stated before the frozen runs"; verdict sec.1 says "All 8 frozen cases matched their frozen predictions".
- I found no outcome-directed edit (cannot see harness revisions before 04:03:50; the file history is not retained). Freeze time precedes all frozen runs (run1 start 04:05:08, M06 04:05:17, M14 04:05:19) and all mutant executions; mutant diffs exist from 04:02:38 but were unexecuted before freeze (supported by raw timestamps). The freeze time is a self-written text file with no external timestamp; protocol and its .sha256 have identical mtime.
- Consequence: the pristine 8/8 pass is a regression confirmation of already-observed behaviour, not a falsification test. Only the mutant kills carry discriminating power.
- Wording: replace "matched their frozen predictions" with "matched expectations that were fixed at freeze after pre-freeze probes and one all-pass shakedown had already observed the same behaviour; the pristine pass therefore confirms rather than tests them. Discrimination rests on the two mutant kills."

F2 [should-fix] Reason given for not attempting a graft for effective_profile_digest is wrong (verdict 2.3: "a graft with a donor of a different effective profile (would also move the base binding)").
- A graft rewrites only the persisted member; the persisted base binding is unchanged, so the base diff against the live mint stays empty exactly as in Q2-A3. What defeats isolation is that a donor member from a world with a different effective profile also differs in members.families.0.effective_policy_digest (see the E2 ECB diff, 3 leaves: digest, effective_profile_digest, families.0.effective_policy_digest; also registry_f5_class_age_governance.py _gl_bound/family_rows derive the family digest from the same effective values). A non-age host change moves host_profile_digest as well, and a catalogue change moves approval_commitment (guard-first).
- The DECOMPOSED-ONLY conclusion is probably right but is argued from an untested and mis-stated premise. Not run: the graft attempt itself.
- Wording: "A graft with a donor of a different effective profile was not run; by source reading its ECB diff would also contain families.0.effective_policy_digest (as in Q3-E2), so it would not meet the isolated rule. Not executed."

F3 [should-fix] "MET" is relative to a criterion and decision rules that the worker wrote (protocol sec.5), and the table row is unqualified.
- A25(a)/(e) is paraphrased in the protocol; the original text is not reproduced or cited by line. MET for host_profile_digest is shown only for GovernedClassAgeWorkflow with a masked-host edit (single case, single workflow); policy-composition and class-unreadable workflows (same pattern, registry_governed_policy.py:482-486 per verdict) are listed as not covered but the table cell says MET for the member.
- The kill evidence for host is the worker's own mutant M14, which only touches the F5 class-age site.
- Wording: "host_profile_digest: MET under PROTOCOL-D1-v1 sec.5 on the F5 class-age masked-host route only; not shown for other governed workflows."

F4 [should-fix] Graft validity: honestly labelled but the table/README one-liners could be read as a reachability claim; reachability under admission contracts is NOT shown.
- Source: effective_id covers only proposal/grant (bounded.py:2010-2015), so the store re-read at execute compares the object with itself; docs/effective-configuration-binding.md:152-153 explicitly says the binding does not defend against a store writer who can forge "a whole decision, a member". The grafted state (member domain d1 inside a decision whose base manifest_digest/proposal belong to d2) is a state production code never mints; it is accepted only because the store is unsigned. The verdict says this ("not a natural-reachability claim", sec.2.2 and 4) and "no guard disabled" is true (store reader, constructor, classifier "mismatch" not "invalid" are checked). So the claim is honest; I do not recommend downgrading to NOT MET, but "MET ONLY BY GRAFT" is only a statement that the comparison/derivation are member-sensitive under an out-of-model write.
- Suggested wording for the one-liner: "scope.authority_domain: member sensitivity demonstrated only under an unsigned-store write (outside the documented threat model, effective-configuration-binding.md sec. limits); no natural or supported-write route isolates it. This is not evidence that the member is independently enforced in operation."
- Related note: the verdict's "(a)-(e) shows the candidate state is otherwise valid" shows only consistency with the same-proposal base binding, not that the state could arise by any legitimate sequence.

F5 [note] Source-to-evidence correspondence confirmed for the three members.
- host: registry_f5_class_age_governance.py:260 builds host_profile_digest from self._f5_host, effective from held; compose_profile (:117-126) overwrites class age so host 61 vs Registry 10 yields equal effective dumps; H1 asserts equal dumps, equal independent commitments (own_commit via canonical sha256 of model_dump, not candidate profile_digest), differing host commitments, and effective age == 10. H2 compares the persisted members to those own commitments. The refusal path is bounded.py:1690-1693 (`current != persisted.binding`, code emitted only when no other reason).
- scope.authority_domain: registry_governed_lifecycle.py:81/199 reads authority from the manifest; manifest_digest (bounded.py:2619) and domain (2298) guards confirmed; lifecycle _resolve returns base reasons unchanged. A1 independently checks the member against the manifest literal.
- effective: runtime_authority.py:475 catalogue_digest = commitment(profile dump); approval guard :332-335. Confirmed.
- The complementary binding diff is computed from the persisted store file vs a binding minted by a fresh genuine `decide` of the same live world (d1_lib.live_binding/split_diff/leaf_diff), not from the candidate classifier (classifier used only as labelled "evidence-only" extra checks). Limit: the live side is still candidate-minted, so the diff proves "which leaves differ" not "which leaf is correct"; correctness of member content rests on H2/A1 independent recomputation. Also the diff is against a scratch mint, not against the `current` binding built inside the execute call; equivalence is supported by the H0 control (empty diff and acknowledged) and not otherwise verified.
- Citation drift (note): execute checks are at 1675-1679 in this tree vs 1676/1678/1680 cited; effect-identity "1680 not 1679" statement in verdict sec.3 is the reverse of what I see (`persisted.effect_id != self._effect_id` is on the line before 1680). Harmless; recheck before publication.

F6 [should-fix] Mutant coverage is narrower than "killed" suggests; verdict sec.2.3 asserts an unverified outcome-equivalence.
- Both mutants alter live DERIVATION only (scope_identity constant; host digest := effective). Kill sets are discriminating and not for unrelated reasons: M06 fails only Q2 cases, with graft executing and A1 content checks; M14 fails only Q3-H1/H2/E2, with the host edit executing. Q3 cases pass under M06 and Q2 cases pass under M14 (good specificity). But no mutant in the COMPARISON/stamping side (e.g. classify comparing only some fields, `_gl_with_member` omitting the member, bounded.py:1690 comparison weakened) was run, so "comparison is member-sensitive" for execute rests on the pristine pass only. The M14 mutant is the author's; M06 is inherited from the earlier effort.
- "a mutant dropping this member is outcome-equivalent there (catalogue_digest carries the same information)" is a source-reading claim, unrun; mark as such.
- Wording: "Mutation coverage: two derivation-side mutants only; no comparison-side or stamping-side mutant was run; no effective_profile_digest mutant was run."

F7 [note] Negative/skipped cases are listed, adequate. Missing but worth stating: no negative control showing a host edit that is NOT masked (host below Registry value) behaving as joint; no case that H1's refusal is stable under a different clock; the A19 reseal rows used as layer P were not re-verified (disclosed). Kill criteria and failing-check sets were stated in the protocol before executing mutants and matched.

F8 [note] Harness weaknesses.
- run_d1.sh hard-codes /tmp/claude-0/work/...; README discloses this. I reproduced by exporting the same env vars manually (equivalent).
- Shared tooling: fixtures, canon, member_of, my_digest, Src, drive_execute come from orig_harness.py (byte-identical to the original qualifier's post-AMEND4); a bug there would be common-mode. d1_lib `retarget` replaces exact-string matches of the domain and uses deprecated pydantic instance access of model_fields (40 warnings); a missed non-exact occurrence would show as a refusal not as a false pass.
- Mutant trees were created under /tmp/claude-0/work/d1/scratch and are not in the evidence directory; the tree-diff files reference `scratch/mut-*`; replay needs `patch -p1` per README. Per-case stores not retained (disclosed).
- Soft-assert design records every check (good); a case could still pass with weak assertions, e.g. A2(iii) wraps construction errors into a recorded failed check (fine).
- Flakiness: none observed. Two evidence runs and my re-run have identical (case,kind,check) sequences.

F9 [note] Independence statements in README/verdict are candid (subordinate of lead builder; same family; shared fixtures; no written designation recorded; the assignment's own stop condition recorded as unsatisfied). I recommend keeping the BLOCKED/UNSATISFIED designation caveat at the top of verdict.md, not only in README and sec.7.

F10 [note] Minor overstatement: README "Result in one line" and verdict "Protocol-level result is therefore the predicted one" read as a success claim; with F1 it should say "consistent with expectations fixed at freeze".

## Reproduction (item 5)
One re-run of the frozen test_d1.py (sha fae0f036...) against the pristine tree, Registry pin a40fe755, venv311, same env vars as run_d1.sh but outputs to a new scratch dir (not the evidence): 8 passed in 1.31s; 110 evidence records; (case,kind,check) sequence identical to raw/739efe7-run1. Pristine tree has no __pycache__; PYTHONDONTWRITEBYTECODE=1 used.

## Not examined
- F3-A formal acceptance and any Architect/competent-authority matter (excluded by instruction).
- Contents of the original A19 reseal rows and original M06/A25 UNREACHABLE records (layer P reused by the worker; I did not verify them).
- Whether the D-1 worker's pre-freeze harness drafts were edited in response to probe results (no revision history retained).
- The mutant runs were not re-executed (only read: raw outputs, diffs, tree-diffs); I did not rebuild mutant trees.
- The lead's static-analysis PROPOSAL beyond the quoted R3/R5 passages; the policy-composition and class-unreadable workflows; freshness extension; 8616d5f, main, Python 3.12.
- Whole-file line-by-line audit of bounded.py/registry_governed_policy.py; only the cited paths were checked.
- Whether orig_harness.py helpers are themselves correct (common-mode risk); manifest.json/SHA256SUMS beyond a clean `sha256sum -c`.
