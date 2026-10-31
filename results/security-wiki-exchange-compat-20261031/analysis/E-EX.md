# E-EX adversarial review (fresh context, no independence claim)
Exchange branch exchange/current-stack-profile-20261031 @ 05ba99ba5458d5b03da36c1a8a20f239f6fbf8b6. Scratch: /tmp/claude-0/sec/scratch-E-EX/ (clone; originals untouched).

## Findings
| id | severity | status | evidence | recommendation |
|---|---|---|---|---|
| E1 | HIGH | VERIFIED (OBSERVED) | Replay importers.py:681-682 accepts only CONTROL_PLANE_REVISION + CONTROL_PLANE_SUPPORTED_V2_REVISIONS (line 96, ends at P2 CP 7a4bcd40); b19c47dd absent from Replay src (grep). Diag log: 39 failed/2 passed, 36x ImportContractError "unsupported Control Plane revision", 2 assertion failures embedding it, 1 more asserting on it. | Do not merge/select the profile as a working generation. Stop. |
| E2 | MEDIUM | VERIFIED | ODES common.py:96-105 SECURITY_RUNTIME_GENERATIONS and Pack importer.py:96-104 P2_REVISIONS key only CP 7a4bcd40/Runtime c5e97e87 (newest). The diag never reached them (Replay fails first), so "INCOMPATIBLE at ODES/Pack" is INFERENCE from source, not observed. | Word as "Replay observed; ODES/Pack by source inspection". |
| E3 | MEDIUM | VERIFIED | Wiki test TC-L06-039 (test_wp_g5...:463-480): `else: assert exc is not None` plus `attempt()` swallows; [plain] and [urgent_administrator] pass on the Replay refusal; effects()==[] is trivially true. Vacuous. | Classify NOT-PASS/INCONCLUSIVE; count 0 of 41 as exercised. |
| E4 | LOW | VERIFIED | Profile comment says it "does not certify the tuple": honest. But a merged profile that no Replay accepts is dead/misleading config; it also widens SECURITY_RUNTIME_PROFILES/STRICT_SOURCE_PROFILES. | Keep unmerged. |
| E5 | LOW | VERIFIED | Untracked in /home/claude/wt-wiki: process/zz-diag-profile.json (identical to cs-diag/profile-diag.json) and results/security-wiki-exchange-compat-20261031/. results/security-wiki-current-stack-20261031 and tracked files clean. | Ensure diag profile is not committed as a qualification profile. |
| E6 | LOW | VERIFIED | test_current_profile_accepts_the_correct_tuple still passes with the frozenset entry dropped (fixtures monkeypatch constants), so it is not sensitive to that entry; other tests are. Full 144-test run with entry dropped did not finish in >5 min (INFERENCE: strict check bypassed, some tests slow/hang); I killed it. | Optional. |

## Lettered verdicts
a) No unsupported compatibility claim in comment/tests (comment disclaims certification; Registry stated not consumed). PASS.
b) Exact-string `==` chain; env var only selects profile name; no env override of pins; case/whitespace/empty/wildcard/unknown names all raise "unsupported GAX runtime compatibility profile" (observed in tests and by direct env runs). PASS.
c) All 6 constants equal the intended 40-char values (script check vs block text, and diag profile/obs). PASS.
d) FAIL RISK: 2 vacuous passes (E3). Remaining 39 fail visibly.
e) No hidden handler in the diff; only Wiki test helpers swallow (E3). The Replay refusal is raised inside Replay, not converted by Exchange.
f) Diff = 6 constants block + 1 frozenset entry (git diff main..HEAD); no logic change. PASS.
g) No new authority propagation; profile requires trusted runtime_authority_profile (test asserts ValueError). PASS.
h) Historical evidence unaltered (E5 only untracked additions). PASS.
i) Mutations (scratch): ODES last-char typo -> 1 fail (test_current_profile_selects_the_exact_tuple...); Manifest typo -> same 1 fail; drop frozenset entry -> 11 fail/10 pass of the 21 `-k current` tests (exact_tuple, default_profile, 4 mixed_tuple, 2 missing_identity, substituted, tampered, manifest_other). Baseline 144 passed. Mutation-sensitive, with the E6 caveat.
j) Lead's conclusion justified for Replay (observed). Diagnostic valid: cs-diag/exchange HEAD 05ba99ba, runtime file byte-identical to branch; profile json names the profile and traceback shows control_plane_revision='b19c47dd...' reaching Replay, so the env/profile did reach gax_ref_runtime and the Exchange source check passed (obs 83 calls, 0 raises); component SHAs equal the intended tuple. ODES/Pack part is inference (E2).

Verdict: INCOMPATIBLE confirmed (Replay gate OBSERVED; ODES/Pack by source). Do not merge; stop.
