# Runtime manifest notes (Execution Runtime half)

Pin: cognous-execution-runtime c5e97e87dd239c821b1b4a406a55dcd03c5bc61f (confirmed via .git/refs/heads/main and packed-refs). 24 rows. Planning proposals only; no test outcomes restated.
Validation: Bash was unavailable (classifier error) when the rows were written, so JSON was first validated by a strict whole-line regex (all 24 lines match the 19-key ordered shape, no inner quotes or backslashes), not by json.loads. The rows are now loaded and checked by `method/build_extraction_manifest.py`.

## Verified directly at the pin
- LocalExecutionPolicy fields, __post_init__, _target_allowed, check order and reason texts (safe_executor.py:358-430); number validators (252-276); _admit_plain_data (147-184); validate_snapshot incl. tenant bound (286-340); cumulative count (810-815).
- control_plane_adapter.py trusted-context check and where trusted values come from (44-136, 245-265, 428-436); atomic_local_control_plane_executor.py:69 policy.check.
- permissions.py and engine.py (legacy AgentEngine); openshell_environment.py budgets and OpenShellConfig (28-107, 115-118, 210); local_authority_effect.py budget lines (413, 697-725, 845-856).
- README.md:82-86 and OCS tools/mvp_ingress/synthetic_host.py:126-130 (OCS clone read; its HEAD not verified).
- Grep of Runtime *.py: no redaction (F11), no refusal_trends (F10), no tool lists (F8), no registry hook.

## Taken from lane D / crosswalk, not re-read
- Control Plane side claims (bounded.py:2570, 2682, 2735; five CP tenant copies; strict_json/cli_run bounds), S02/R07/D-ruling text, test IDs and their NOT RUN / historical states, test_add_c2c_bi.py line numbers, CHANGELOG.md:20 (long line not fully read), engine/permissions.json sample contents.

## Families with no Runtime row (by design)
- F10, F11, F8: enforcing code lives in Control Plane only (grep of Runtime found nothing). No F8 NOT_RELEVANT_TO_V1 row was written because F8 does not live in the Runtime; the Control Plane half carries it. Zero NOT_RELEVANT_TO_V1 rows on the Runtime side.
- F7 (dedupe_ttl_seconds default 600, dedupe_destination.py:105; positive-int check :44) is in Runtime but outside the requested family list; not rowed. Flag for the lead (D12 open).

## Discrepancies with lane D / crosswalk
1. Lane D says Route A compares operation to "separately supplied trusted_institution_id/authority_domain constructor values". At the pin the values are derived inside PinnedControlPlaneExecutor.execute from the CP resolver authority_context (or manifest action authority_context when runtime_authority_profile is set), control_plane_adapter.py:245-265; reconcile() passes the operation's own values (430-431). Handled as RT-F1b-03 (guardrail). Not traced: whether reconcile reaches anything beyond observe/apply (which call the check at 99, 136).
2. permissions.py at pin: is_allowed accepts list, tuple or set entries (line 21); lane D says list. Behaviour otherwise as described; malformed JSON still uncaught.
3. Crosswalk A04 enforcement text says "tenant length <=1"; code is 1 <= len <= 128 (safe_executor.py:319). Treated as typo.
4. Lane D cites local_authority_effect.py:848 for the atomic budget; at the pin the check is at 845-856 (851-856 refusal). Consistent with a range, noted for line accuracy.
5. Lane D: no qualification test varies target_match (search of suites/). Qualification repo process/adversarial/tests/test_t05_target_equivalence.py:51 does pass target_match (outside suites/ and outside the crosswalk). Run state not assessed; listed as a candidate only.
6. C11 is mapped to F1c, but its tests cover max_amount only (lane D: max_effects not in POLICY_DIMS); C11 is therefore not attached to RT-F1c-02.
7. Lane D labels W1-007/W1-008 admission guards CONFIGURABLE-CANDIDATE (Tier 1); R07 proposal says admission guards not eligible; RT-F3-01/02 are rowed CODE_OWNED_GUARDRAIL on that basis (extractability clause (a) also fails: literals).

## Crosswalk mappings where a scenario was attached with a caveat
- C02 (F1a), C18 (F1b,F1c), D02 (F1b,F1c): their enforcement text is mainly Control Plane (_manifest_mismatches, delegation, identity binding) plus Runtime adapter proposal-commitment checks, not LocalExecutionPolicy.check. Attached to F1a/F1b rows as crosswalk-mapped regression context; they exercise no registry-supplied Runtime value.
- TC-L06-013 (F1a,F6): attached to RT-F1a-01 only; its crosswalk text says permissions.py is NOT on this route (per-agent rights = CP grant permissions), so not attached to F6 rows.
- SL:fix2-probes:manifest-effect-limits and SL:fix2-probes:verifier-effective-max-effects-binding (F1c): enforcement is CP/verifier, no Runtime field; not attached.
- SL:v1-probes:scan-fix-runtime-profile-separation (F1c): attached only to the exact-amount guardrail row RT-F1c-04.

## Scenarios mapped to a Runtime family in the crosswalk with NO configurable Runtime field found
- None of the F1a/F1b/F1c/F1d/F3/F6/F9 scenarios was left unmapped, but these attach only to guardrail rows: SL:cognous-execution-runtime:atomic-commit-budget-concurrency (RT-F1c-05), C10 (RT-F3-03/04 only; its path-confinement enforcement is code), SL:v1-probes:scan-fix-runtime-profile-separation.
- Scenario IDs NONE: RT-F1d-02, RT-F1d-03 (no mapped test varies target_match), RT-F6-02 (new question, no scenario).
- UNMAPPED/F4/F5/F7/F10/F11 crosswalk rows were not considered here (not Runtime-owned fields in the requested set).

## Not confirmed
- Registry-side numeric encoding for max_amount (UNVERIFIED, P0 G3 open); registry-side string bounds for allowed sets (S03 1-128 chars from lane D).
- How a production operator builds LocalExecutionPolicy (no production caller exists in sources read).
- Whether any Runtime-local test (tests/test_route_a_local_policy_reason.py, tests/test_exact_target_matching.py) covers the isolated effect-count refusal; not read.
- engine/permissions.json contents and CHANGELOG.md:20 full text.

## Decision dependencies used
D6 (RT-F1c-01 conditional, RT-F1c-02 unresolved), D1 (W8-091 on F1c-02; W1-029 on F1d; W2-082 on F3-04), D5 (RT-F6-01/02), D9 (F1d, ruled deferred), D4 (scalar direction/cap per field), D2/D3/D7/D11/D13 respected (F1a/F1b DIRECT assumes authenticated selection, mandatory-participation design-only, independent qualifier undesignated). W8-014 and D12 not touched by any Runtime field in this set.
