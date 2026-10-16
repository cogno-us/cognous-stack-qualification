# Runtime authority implementation dashboard

This is a separate nonselected candidate for the supplied engineering addendum
K1–K6. It does not modify the hub lock or release authority. The exact component
set and remaining closeout order are recorded in
[the candidate manifest](../process/runtime-authority-candidate-2026-10-15.json).

| Stage | Status | Reviewable result |
|---|---|---|
| Source reproduction and bounded contract | Complete | Control Plane base c7f122ba and runtime base cb437f86 inspected; existing expiry access already expects an expiry, so absence is now a typed hold rather than an alleged newly permitted behavior |
| K1 K2 K4 and required-input binding | Implemented and tested | [Control Plane PR 33](https://github.com/cogno-us/cognous-control-plane/pull/33) |
| K3 transactional destination precondition | Implemented and tested | [Runtime PR 89](https://github.com/cogno-us/cognous-execution-runtime/pull/89) |
| K5 and lossless Replay | Implemented and tested | [Replay PR 27](https://github.com/cogno-us/cognous-replay-bundle/pull/27) |
| Evidence Pack mapping and reason reporting | Implemented and tested | [Evidence Pack PR 27](https://github.com/cogno-us/cognous-governance-evidence-pack/pull/27) |
| Actual component qualification | 20 local cases pass | New suite and exact-source runner in this PR; hosted results are separate evidence |
| K6 paired scorer | Implemented and arithmetically tested | [PRP PR 9](https://github.com/cogno-us/portable-reasoning-protocol/pull/9); behavioral runs UNEXECUTED |
| Integration of approved PRs | Pending | Control Plane, runtime, Replay, Evidence Pack, then qualification; requalify actual merged revisions |
| Final security safety and IP review | Deferred | After engineering integration and final tests, before final publication acceptance |

## Verification

Local Python 3.12 component outcomes: Control Plane 298 passed and one optional
AGT SDK test skipped; runtime 138 passed; Replay 183 passed; Evidence Pack 127
tracked native tests passed. PRP 25 deterministic tests passed; package validation
passed seven JSON files, three YAML files and 120 local Markdown links/anchors.
These counts are separate test populations, not a unified operational trial.

The actual-component suite has 20 passing cases without skips. It asserts
unchanged destination state for refused actions, exact source retention and
reconstruction, real SQLite commit conditions, lost acknowledgement remaining
unknown until observation/reconciliation, and rejection of journal omission,
refusal vocabulary loss and falsified Evidence Pack counts. Native CP JSON,
executor export, Replay, destination SQLite/observation and Evidence Pack files
are retained under the run directory with a SHA256 inventory.

Use the supported exact checkouts as `components/control_plane`,
`components/runtime`, `components/replay` and `components/evidence_pack`, then run:

```bash
python tools/run_runtime_authority.py --components components --out results/runtime-authority
```

The runner verifies actual Git heads and refuses modified, untracked or ignored
files and hidden index flags before execution, so use fresh runner-owned clones
(see [security residuals](security-residuals-20261016.md)). Its JSON receipt records versions, trees, command, return code and
artifact digests. The workflow performs pinned checkouts on Python 3.11 and 3.12.
Passing a candidate does not select it. After merges, their different merge SHAs
need an explicitly requalified compatibility mapping; do not relabel these pins.

The final control-plane check also prevents a later resolver outage from using a
cached positive after a recorded revocation/suspension of the same grant revision.

Runtime's first hosted packaged-worker test exposed an unconditional optional
module import in the legacy minimal image. PR 89 now loads the module only for an
explicit or activated profile and adds a focused regression. The rerun must pass
at the updated exact head. Local broad Node lint could not bootstrap because the
installed pnpm policy rejects upstream `libsignal`; that policy is unchanged.

## Source scenario crosswalk

All source scenario identifiers are preserved in owning component tests. The
original synthetic cross-component cases extend them rather than copying a
parallel legacy harness.

| Source | Owning test path | Required scenarios |
|---|---|---|
| K1 | control-plane tests/test_runtime_authority.py | resolver_returns_none_distinct_code; resolver_raises_refusal_recorded; process_dies_mid_resolve_reads_interrupted; irreversible_class_refuses_on_unreadable_reversible_tolerates_bounded_age; holder_cannot_reclassify_action; revoked_code_requires_snapshot |
| K2 | control-plane tests/test_runtime_authority.py | evidence_count_below_criterion_holds; evidence_set_outside_approved_manifest_holds; agent_rewritten_validator_record_holds |
| K3 | runtime tests/test_effective_grant.py and control-plane tests/test_runtime_authority.py | role_widened_between_read_and_commit_refused; input_dropped_from_list_holds |
| K4 | control-plane tests/test_runtime_authority.py | grant_bound_to_closed_case_holds; reopened_case_does_not_revive_grant; purpose_source_unreachable_irreversible_refuses |
| K5 | control-plane tests/test_runtime_authority.py | refusal_row_carries_vocabulary_version; code_split_produces_vocabulary_change_row |
| K6 | PRP tests/test_paired_evaluation.py | prp_pair_scored_jointly; prp_expected_loss_with_delay_cost; prp_perturbed_model_direction_only |

## Limits and deferred closeout

Authority atomicity covers only the new local SQLite permission table and effect
transaction with cooperating trusted writers. Remote policy/purpose/grant stores
and actual cloud identity/credential controls are outside it. Purpose outages
currently hold for every class; no purpose-outage grace is claimed. The journal
is same-host Linux storage and process-exit recovery, not power-loss qualification.
No human-oversight evaluation or independent institutional outcome is established.

No new ODES or GAX mapping is included in this candidate; those optional consumers
must reject unsupported revisions rather than silently reuse a historical profile.
This candidate cannot claim their interoperability. Existing selected mappings are
unchanged. Component reviews, actual merged-source requalification and operational
acceptance remain separate from this implementation.

Carry forward the existing closeout instruction: after engineering and all final
tests, freeze the exact final hub revision, component-lock digest, selected pins
and proposed release bytes. Then perform the fresh security review, tracked-file
inventory, review receipts, dependency/workflow and authorization boundary review,
and release-byte credentials/customer data/proprietary IP review. Preserve private
findings and matched values. Disposition remaining issues from actual evidence,
then complete publication acceptance. Do not run this deferred final review now,
create an automation, or infer approval from this dashboard.

## Provenance and rights

Source: supplied Cognous Engineering Addendum Moltbook 101526_A, dated 15 October
2026; the manifest commits its exact source hash. The 5 October consolidated
recommendations supply architecture boundaries, not current defect status.
These are original synthetic fixtures and code under the existing Apache-2.0
licenses. No third-party implementation or discussion text is copied into tests;
thread instructions are treated as untrusted data. Local and hosted results prove
only their named conditions and exact source revisions.
