# Reliance inspection: does any relied-upon interface treat CP pin-export as effecting, or require durable EffectTimeRefusal / `authorization_binding_changed` token on pin-export or claim paths?

Read-only. No repo modified. Revisions: CP 739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69 ("739") and 8616d5f64a901b8f858359809193961a1124b5f6 ("861"); Registry 517062529f0507be81a8ac5e457a009db98f8d90 (HEAD); Hub 2f3dcd55ff2b6345d774f8868fa83d62e1bc2f3e (HEAD). `git status` of the three clones was clean at inspection.

## 1. Commands and counts (line hits; `P` = `-i -E 'pin.export|pin_export|assess_authorization_pin'`, `T` = `authorization_binding_changed`)
Commands: `git -C <repo> grep -n -i -E 'pin.export|pin_export|assess_authorization_pin' <rev> [-- <dir>]`, `git -C <repo> grep -n 'authorization_binding_changed' <rev> [-- <dir>]`.

| Repo / rev | P lines | P files | T lines | T files |
|---|---|---|---|---|
| CP 739 | 75 | 33 | 34 | 31 |
| CP 861 | 77 | 33 | 35 | 31 |
| Registry HEAD | 100 | 29 | 41 | 14 |
| Hub HEAD | 21 | 5 | 98 | 53 |

CP by directory (P / T), 739 -> 861: src 5/4 -> 6/4; tests 28/6 -> 28/6; docs (incl. evidence) 41/19 -> 42/20 of which docs/evidence 34/11 (both); schemas 0/3; conformance 0/0; examples 0/0; tools 0/0; collateral 0/0; CHANGELOG.md 1/2 (both revs); README, .github: 0/0. (`git grep P` on 739 vs 861 differs by exactly +1 src line, +1 doc line, both from the 2026-10-29 clarification; `authorization_pin_export.py` itself is byte-identical in the diff stat: the only src diff is the docstring of `registry_governed_policy.py`.)
Registry: all 100 P and 41 T hits are under `docs/`. Registry code outside docs (registry_adapters, registry_conformance, registry_consumer, registry_contract, registry_records, registry_successor, tests, tools, baseline): **0 P hits, 0 T hits**. (Only broader-term hit: `tests/test_contract_amendment_4_pins.py` reads `docs/f-a1-authorization-pin/*.md` paths; no pin-export refusal assertion.) Registry docs by area: final-three/ (incl. annex, assignments) 8+ files, post-migration/ 5, g0/ 6, g1-preparation/ 6, v09/ 3, audit/ 1, s02-evidence/ 1 (T only).
Hub: P in results/third-party (3 files, 14 lines) and suites/tier1-v08-fa1 (2 files, 7 lines); P in hub docs/: 0; P in hub schemas/conformance/tools: 0. T: docs/registry-v1-scope-assessment/data (2 files, 6 lines, crosswalk rows citing execute re-resolution), results/third-party (2 files, 3 lines), suites/wiki-derived (1), results/v1-validation junit XML (48 files, 88 lines, captured CP test output).
CP `pyproject.toml` has one console script `acp = agent_control_plane.cli:main`; `git grep authorization_pin_export <861> -- src` outside the module itself returns 0 lines, so the CLI and no other src module imports/calls pin-export.

## 2. Classification (outside tests/evidence)
(a) read-only/non-authorizing description, (b) effecting/execute-path reference, (c) typed-only reason registration, (d) historical/design record, (e) REQUIRES durable pin-export refusal or token on pin-export/claim.

| file:line (rev) | content | class |
|---|---|---|
| CP src/agent_control_plane/authorization_pin_export.py:1-17 (both) | "NON-AUTHORIZING ... makes no authorization decision"; no `append_refusal`, no `EffectTimeRefusal`, no `provision` (grep of the file for append_refusal/EffectTimeRefusal: 0) | a |
| CP authorization_pin_export.py:91-100,181-188 (both) | docstring "Read-only assessment"; mismatch returns `_unknown(...)` (payload None) | a |
| CP docs/authorization-pin-export.md:1-13 (both, identical) | "NON-AUTHORIZING", "read-only", states active/terminal/unknown | a |
| CP src/.../registry_governed_policy.py:28-29 (739) | "`execute` and the pin-export claim refuse `authorization_binding_changed`" (no durable wording) | d (superseded; wording loose, not "durable") |
| CP registry_governed_policy.py:28-30 (861) | "Pin-export ... non-authorizing assessment (state not `active`, payload suppressed ... no `EffectTimeRefusal` is added)" | a |
| CP src/bounded.py:1693 (both) | `refusal_reasons=["authorization_binding_changed"]` inside `execute` (appends EffectTimeRefusal at ~1694) | b |
| CP src/effective_configuration_binding.py:40; registry_governed_lifecycle.py:36 | constant for registered reason | c |
| CP schemas/runtime_authority_reasons_0_1/0_2/0_3.json:68 | `"authorization_binding_changed": {"reason_kind": "typed_only", ...}` - registration only, no path scoping | c |
| CP docs/effective-configuration-binding.md:50 (739) | "Check on execute and on the pin-export / claim path ... mismatch yields ... `authorization_binding_changed` as a durable `EffectTimeRefusal`" | d/e-internal (overclaim; corrected at 861, see 3) |
| same :50 (861) | "On the read-only pin-export path it yields a non-`active` result with no payload and writes no `EffectTimeRefusal`; at claim issuance no claim is issued and no `EffectTimeRefusal` is written ... (Correction 2026-10-29 ...)" | a |
| same :101 (739) | "REFUSE, durable `EffectTimeRefusal`; execute and pin-export both" | d/e-internal (overclaim; corrected at 861) |
| same :101 (861) | "Pin export (read-only assessment): fails closed, state not `active`, payload `None`, no `EffectTimeRefusal` written. Claim issuance: no claim issued (`PermissionError`), no `EffectTimeRefusal` written." | a |
| same :113 (739) | "Durable ...: `authorization_binding_changed` as an `EffectTimeRefusal` ... On the pin-export path the result is not `active` and carries no payload" | b + a (consistent with read-only) |
| same :113, :126, :127 (861) | adds "writes no `EffectTimeRefusal`", state `unknown`; :127 live-malformed -> adapter code `configuration_binding_invalid`, "not a durable reason code, no refusal row", pin export reports `unknown` | a |
| same :79, :97 (both) | status table / legacy -> refuse with the reason code (generic, path-unscoped) | c/b |
| CP CHANGELOG.md:6 (739) | "`execute` and the pin-export claim path refuse with the registered `authorization_binding_changed` (durable `EffectTimeRefusal`)" | d (overclaim) |
| CP CHANGELOG.md:6 (861) | "the pin-export claim path reports a non-`active` result with no payload and issues no pin, and claim issuance issues no claim, in each case without an `EffectTimeRefusal`" | a |
| CP CHANGELOG.md:9 (both) | follow-up, dedicated workflows, same reason | b/c |
| CP docs/governed-workflow-consolidation.md:34 (739) | "`execute` and the pin-export claim refuse `authorization_binding_changed` on any difference" (not "durable") | d |
| same (861) | "read-only pin-export and claim-issuance paths fail closed without an `EffectTimeRefusal`" | a |
| CP docs/final3-consumers.md:11 (both) | adapter codes; "NO new durable reason code" | c |
| Registry docs/family-migration/final-three/03-f3-qualification-expectations-F3A-F3B-2026-10-29.md:23 | "every member perturbed ... makes execute AND pin-export refuse with `authorization_binding_changed` and a durable `EffectTimeRefusal`" | **e-literal (frozen qualification ORACLE text; not an interface, see 4)** |
| Registry .../02-architect-authorization-and-contract-freeze-2026-10-29.md:31 | D-06.6 "Reuse the registered `authorization_binding_changed` (durable `EffectTimeRefusal`)" (not path-scoped) | c/b (ambiguous) |
| Registry .../02-...:52 | "Execute and pin-export claim recompute the live member and compare ... refuse `authorization_binding_changed`" (no "durable", no "token required on pin-export") | b/ambiguous; looser than 03:23 |
| Registry .../00-consolidated-decision-record-...:9,13 | design recommendation | d |
| Registry .../06-f3a-dev-pe-1-interpretation-v1.0:18-20,22,25-26,29-30,35-36,41-44,50,65 | successor interpretation: pin-export read-only; token obligation of effecting path only; CA21 states a prior search found no relied-upon interface; Status line 3: "ADOPTED IN PRINCIPLE ... subject to final source review; documentation only" | a (+ records the e-literal conflict, see 4) |
| Registry .../07-f3a-readjudication-handoff:12-16,21-24; 08-ci-scope-declaration:11; 10-fresh-qualifier-prompt:21,23,55 | process/assignment text, stop condition "an external interface requires durable pin-export refusal evidence" | d |
| Registry .../annex/A-d06-...-design.md (12 P / 12 T lines: 30-36,85-92,111,121,133-136,150-159) | "pin export claim path refuses", line 90 "(durable EffectTimeRefusal ...)" for execute; :92 "also the pin export claim path refuses" | d (design record; interpretation-06:22 says it is not an external commitment) |
| Registry .../annex/B-d07-temporal...md:59,91 | "pin-export behaviour" read only | d |
| Registry final-three/assignments/readjudication-packet.json (16P/5T), remediation-packet.json (15P/5T); docs/post-migration/assignments/F3-A.assignment.json, build_assignments.py | machine-generated copies of assignment text quoting 03:23/06 | d |
| Registry docs/post-migration/annex/A-f3-source-binding-and-coverage-map-developer-record.md:97,117 | coverage map restating oracle expectation 1 ("execute AND pin-export refuse with token and durable ...") and which tests cover pin-export | e-literal (restates 03:23) / d |
| Registry docs/post-migration/annex/C-...:57 | "only `authorization_binding_changed` ... is emitted into durable state" | c |
| Registry docs/post-migration/01-f3a-f3b-...handoff:40 | coverage limits: "pin-export refusal is not driven for every perturbed member" | d |
| Registry docs/s02-evidence/W7.md:26 | bounded.py effect-time refusal row, `execute` | b |
| Registry docs/family-migration/g0/*, g1-preparation/*, v09/*, audit/* (P only, ~20 lines) | file inventories, S02 coverage notes, candidate manifest hash (`authorization_pin_export.py` blob 37c43dcb...) | d |
| Registry docs/r08-v2-contract-amendment-4.md (grep 'export|refus') | specifies `export_authorization_pin` (design name) and says: "no pin" if grant/approval no longer supports it (l.94); installer appends terminal pins from the export (l.168). No refusal-row / token requirement on export. | a |
| Hub results/third-party/cp-739efe7-f3-independent-20261029/PROTOCOL-F3-v1.md:31 (R2) | qualification protocol criterion (b): literal 03 L23 for pin-export tagged CONTRACT-LITERAL | e-literal (qualification criterion, source = 03:23) |
| Hub .../verdict.md:16-24 | FAIL DEV-PE-1: observed state `unknown`, payload None, no refusal row, no code token; says corrective owner may be Architect interpretation | d (historical verdict; consequence of 03:23) |
| Hub .../README.md:19,30 | summary of the FAIL | d |
| Hub suites/tier1-v08-fa1/_fa1.py:6,29,36,83; test_fa1_software.py:596-598 | uses `assess_authorization_pin` to feed the real installer; asserts refused iff `PermissionError/ValueError` or `payload=none`; installer given `state: unknown, payload None` outcome "refused". No assertion on refusal row or token. | a (consumer depends only on state != active / payload None / PermissionError) |
| Hub suites/wiki-derived/test_wp_a_grant_lifecycle.py:773 | `[x.reasons for x in journal().refusals] == [['authorization_binding_changed']]` after `seq.run(req)` (execute route A) | b |
| Hub docs/registry-v1-scope-assessment/data/canonical-scenario-crosswalk.{csv,json} (6 T lines) | "execute re-resolution (authorization_binding_changed)" | b |
| Hub results/v1-validation/**/junit-attempt1.xml (88 T lines) | captured CP pytest output of reason-vocabulary tests | c |
| Hub docs/ and results/ (other than above): P hits 0 | | |

## 3. Quoted pin-export outcome text
`docs/authorization-pin-export.md` (identical at 739 and 861): lines 1-13:
- "Status: candidate, NON-AUTHORIZING."
- "It is read-only with respect to authorization state: it builds no claim, calls no `provision`, creates no decision, grant, approval or policy record, and has no claim or `expected_*` parameter. (The existing resolution step journals a resolution check in the Control Plane record store, as claim issuance does.)"
- "`active`: `payload` holds exactly the 17 Control Plane sourced pin members ..."
- "`terminal`: persisted authority positively shows the decision is no longer supported. `terminal_status` is `revoked` ..., `superseded` ... or `withdrawn` ..."
- "`unknown`: unreadable, unresolved, ambiguous, expired or unmapped. No pin change."
- Mismatch inputs "raise `PermissionError`".
Source: `_result()` sets `payload` to deep copy only when `state == "active"`, else `None` (authorization_pin_export.py:57-59); mismatch of persisted binding -> `_unknown(decision_id, "authority not supported but not positively terminal: ...binding changed")`.

`docs/effective-configuration-binding.md`:
- 739 :50 "...so a mismatch yields the registered reason `authorization_binding_changed` as a durable `EffectTimeRefusal`, and `execute` raises the existing `PermissionError`" (applied to "execute and ... the pin-export / claim path").
- 739 :101 "new record, different configuration (any member) -> new reader | REFUSE, durable `EffectTimeRefusal`; execute and pin-export both".
- 739 :113 "On the pin-export path the result is not `active` and carries no payload (`test_g02`, `test_c04`)."
- 739 :126 only execute is called durable; :127 "the pin export reports `unknown`".
- 861 :101 "Pin export (read-only assessment): fails closed, state not `active`, payload `None`, no `EffectTimeRefusal` written. Claim issuance: no claim issued (`PermissionError`), no `EffectTimeRefusal` written."
- 861 :113 "On the pin-export path the result is not `active`, carries no payload and writes no `EffectTimeRefusal` (`test_g02`, `test_c04` assert the first two; the absence of a refusal row follows from the source, `authorization_pin_export.py` never calls `append_refusal`) ... The pin export still journals its ordinary `ResolutionCheck` row (stage `claim`)."
- 861 :126 "On the pin-export path the same defect gives a non-`active` result with no payload (state `unknown`) and no `EffectTimeRefusal`; at claim issuance, no claim."
- 861 :50 contains explicit "(Correction 2026-10-29: this sentence previously attributed the durable refusal to the pin-export / claim path as well; the code has always behaved as stated here.)"
Verified in source (not just docs): the pin-export module has zero `append_refusal`/`EffectTimeRefusal` references at both revisions; it calls `workflow._resolve(stage="claim")` and `_record_check` (ResolutionCheck journaling only); claim issuance (local_authority_effect.py ~443-466) raises `PermissionError("authorization-critical inputs changed before claim issuance")` with no refusal append; only `bounded.py` execute (~1690-1711) appends `EffectTimeRefusal`.
Caveat for an adversarial reader: tests `test_g02`, `test_g03`, `test_b03`, `test_c04`, `test_d01` assert only `state != "active" and payload is None` (and ECB status); no CP test asserts the ABSENCE of a refusal row on pin-export (861 doc admits this). Behavior is source-derived. Registry 06:36 and the qualifier raw observation ("no refusal row") corroborate empirically.

## 4. What a downstream consumer could depend on re pin-export refusal rows
- CLI (`acp`): does not import pin-export (0 src hits). No dependence.
- CP conformance/ (decision-input-commitment-vectors.json), examples/, tools/, collateral/: 0 hits for pin export or the token.
- CP schemas/: only `runtime_authority_reasons_0_1/0_2/0_3.json` register the token as `typed_only` (a vocabulary entry; nothing path-specific, no schema for pin-export results or refusal rows). The pin-export result is an unschematized closed dict `{profile, decision_id, state, payload, terminal_status, reason}`; a consumer can depend on: `profile == "ocs-s4/authorization-pin-export/0.1"`, `state in {active,terminal,unknown}`, `payload` None unless active, free-text `reason`.
- Real consumer in repos: the Runtime installer (`apply_assessment`) as driven by hub `suites/tier1-v08-fa1`: it accepts the dict, refuses `unknown`/garbage. No reading of a refusal row or token.
- Registry Amendment 4 (docs/r08-v2-contract-amendment-4.md): installer logs its own outcomes (`pending_blocked|complete|refused`) in an installer-owned log; the CP export is only required to yield "no pin" for unsupported authority. The installer's own durable refusal evidence is the installer log, not a CP EffectTimeRefusal.
- Anything keyed on `EffectTimeRefusal.reasons == ['authorization_binding_changed']` (hub wiki-derived test :773; crosswalk rows) is on the execute path only.

## 5. Adverse-case determination
Class (e) in the strict sense, an interface (schema, conformance vector, CLI, installer, consumer code, or Amendment 4 contract) that REQUIRES a durable pin-export/claim refusal row or machine token: **none found** at either CP revision, in Registry code (0 hits outside docs), or in hub suites/docs.

Class (e)-literal, text that says it in prose, found and must be disclosed (adversarial finding):
1. Registry `docs/family-migration/final-three/03-f3-qualification-expectations-F3A-F3B-2026-10-29.md:23` (frozen qualification oracle expectation 1): "makes execute AND pin-export refuse with `authorization_binding_changed` and a durable `EffectTimeRefusal`". This is a qualification expectation, not an external runtime interface, but it does literally require it and the frozen oracle is NOT amended (06 Status line: does not amend/edit/retroactively reinterpret 03/02). Restated at Registry `docs/post-migration/annex/A-f3-source-binding-and-coverage-map-developer-record.md:97`, copied into assignment/packet JSONs, and applied literally by hub `PROTOCOL-F3-v1.md:31` (R2), producing the DEV-PE-1 FAIL (verdict.md:17).
2. CP 739 own docs/CHANGELOG over-stated durable refusal on pin-export (effective-configuration-binding.md:50 and :101; CHANGELOG.md:6). Corrected at 861 with an explicit correction note. A reader of 739 only would see a documented durable pin-export refusal that the code never produced.
3. Registry 02:31/02:52 are ambiguous (D-06.6 "durable" not path-scoped; rule 2 names pin-export claim but not "durable"/"token"). Not class (e).
4. The interpretation (06) is "ADOPTED IN PRINCIPLE ... subject to final source review"; it governs only after the Architect confirms an exact revision (its section 9); I did not verify whether that confirmation exists (outside the three repos' searched text).

Conclusion: no relied-upon external INTERFACE requires it (hypothesis "no such reliance" holds for interfaces); the only requirement is the frozen qualification oracle text 03:23 (+ derivatives), which is exactly what the successor interpretation reconciles, plus 739's superseded overclaiming prose. Whether 03:23 counts as a "relied-upon external interface" is a verdict-owner judgement; I give no verdict.
