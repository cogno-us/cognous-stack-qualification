# Expected versus observed (run1; run2 has the identical assertion sequence and results)

Expected values are the literals frozen in the instruments before execution (see PROTOCOL.md). Rows listed in execution order; observed values truncated to 220 characters (full values in raw/run1/*.jsonl).

| Case | Assertion | Kind | Result | Expected | Observed |
|---|---|---|---|---|---|
| N-CLAIM-JOINT | N-CLAIM-JOINT-P01 | CHECK_PASS | PASS | {"reasons": [], "result": "authorized"} | {"reasons": [], "result": "authorized"} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-P02 | CHECK_PASS | PASS | {"reasons": [], "result": "authorized"} | {"reasons": [], "result": "authorized"} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-P03 | CHECK_PASS | PASS | ["customer-refunds", "other-domain"] | ["customer-refunds", "other-domain"] |
| N-CLAIM-JOINT | N-CLAIM-JOINT-P04 | CHECK_PASS | PASS | {"X_and_Y_proposal_commitments_differ": true, "X_manifest_digest_differs_from_Y": true, "Y_manifest_digest_is_commitment_of_Y_manifest": true, "y_approvals_bound_to_Y_proposal": true} | {"X_and_Y_proposal_commitments_differ": true, "X_manifest_digest_differs_from_Y": true, "Y_manifest_digest_is_commitment_of_Y_manifest": true, "y_approvals_bound_to_Y_proposal": true} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-P05 | CHECK_PASS | PASS | {"reasons": [], "result": "authorized"} | {"reasons": [], "result": "authorized"} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C01 | CHECK_PASS | PASS | {"issued": true, "sink_calls": 1, "verified": true} | {"issued": true, "sink_calls": 1, "verified": true} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-P06 | CHECK_PASS | PASS | {"found": true, "result": "authorized"} | {"found": true, "result": "authorized"} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-P07 | CHECK_PASS | PASS | {"n_new": 1, "reasons": [], "stage": "claim"} | {"n_new": 1, "reasons": [], "stage": "claim"} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-P08 | CHECK_PASS | PASS | {"n_new": 1, "reasons": [], "stage": "claim"} | {"n_new": 1, "reasons": [], "stage": "claim"} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-A01 | CHECK_PASS | PASS | PermissionError | PermissionError |
| N-CLAIM-JOINT | N-CLAIM-JOINT-A02 | CHECK_PASS | PASS | authorization-critical inputs changed before claim issuance | authorization-critical inputs changed before claim issuance |
| N-CLAIM-JOINT | N-CLAIM-JOINT-A03 | CHECK_PASS | PASS | false | false |
| N-CLAIM-JOINT | N-CLAIM-JOINT-A04 | CHECK_PASS | PASS | 0 | 0 |
| N-CLAIM-JOINT | N-CLAIM-JOINT-A05 | CHECK_PASS | PASS | {"resolution_checks": 1} | {"resolution_checks": 1} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-A06 | CHECK_PASS | PASS | true | true |
| N-CLAIM-JOINT | N-CLAIM-JOINT-A07 | CHECK_PASS | PASS | true | true |
| N-CLAIM-JOINT | N-CLAIM-JOINT-A08 | CHECK_PASS | PASS | {"calls": 0, "unchanged": true} | {"calls": 0, "unchanged": true} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-A09 | CHECK_PASS | PASS | {"in_check_reasons": false, "in_exception_text": false} | {"in_check_reasons": false, "in_exception_text": false} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-A10 | CHECK_PASS | PASS | ["manifest_digest", "proposal_commitment"] | ["manifest_digest", "proposal_commitment"] |
| N-CLAIM-JOINT | N-CLAIM-JOINT-A11 | CHECK_PASS | PASS | ["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.scope.authority_domain"] | ["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.scope.authority_domain"] |
| N-CLAIM-JOINT | N-CLAIM-JOINT-A12 | CHECK_PASS | PASS | true | true |
| N-CLAIM-JOINT | N-CLAIM-JOINT-A13 | CHECK_PASS | PASS | joint | joint |
| N-CLAIM-JOINT | N-CLAIM-JOINT-A14 | CHECK_PASS | PASS | ["customer-refunds", "other-domain"] | ["customer-refunds", "other-domain"] |
| N-CLAIM-JOINT | N-CLAIM-JOINT-A15 | CHECK_PASS | PASS | {"live": true, "persisted": true} | {"live": true, "persisted": true} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-A20 | CHECK_PASS | PASS | ["PermissionError", "authorization-critical inputs changed before claim issuance"] | ["PermissionError", "authorization-critical inputs changed before claim issuance"] |
| N-CLAIM-JOINT | N-CLAIM-JOINT-A21 | CHECK_PASS | PASS | {"claim_returned": false, "sink_calls": 0} | {"claim_returned": false, "sink_calls": 0} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-A22 | CHECK_PASS | PASS | {"decisions_equal": true, "nonzero": {"resolution_checks": 1}, "refusals": 0} | {"decisions_equal": true, "nonzero": {"resolution_checks": 1}, "refusals": 0} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-A23 | CHECK_PASS | PASS | {"calls": 0, "unchanged": true} | {"calls": 0, "unchanged": true} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C0-P01 | CHECK_PASS | PASS | {"reasons": [], "result": "authorized"} | {"reasons": [], "result": "authorized"} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C0-P02 | CHECK_PASS | PASS | {"reasons": [], "result": "authorized"} | {"reasons": [], "result": "authorized"} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C0-A00 | CHECK_PASS | PASS | {"base": [], "ecb": []} | {"base": [], "ecb": []} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C0-m-A01 | CHECK_PASS | PASS | {"claim_type": "TenantLocalExecutionClaim", "raised": null} | {"claim_type": "TenantLocalExecutionClaim", "raised": null} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C0-m-A02 | CHECK_PASS | PASS | true | true |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C0-m-A03 | CHECK_PASS | PASS | {"authority_domain": "customer-refunds", "claim_id": "bq-claim-C0-m", "decision_id": "3368c9a9-05e1-44ed-9c02-c19c01534a1d", "manifest_digest": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac", " | {"authority_domain": "customer-refunds", "claim_id": "bq-claim-C0-m", "decision_id": "3368c9a9-05e1-44ed-9c02-c19c01534a1d", "manifest_digest": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac", " |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C0-m-A04 | CHECK_PASS | PASS | {"n_new": 1, "reasons": [], "stage": "claim"} | {"n_new": 1, "reasons": [], "stage": "claim"} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C0-m-A05 | CHECK_PASS | PASS | {"resolution_checks": 1} | {"resolution_checks": 1} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C0-m-A06 | CHECK_PASS | PASS | true | true |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C0-m-A07 | CHECK_PASS | PASS | {"calls": 0, "unchanged": true} | {"calls": 0, "unchanged": true} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C0-m-A08 | CHECK_PASS | PASS | {"calls": 0, "is_returned_claim": null} | {"calls": 0, "is_returned_claim": null} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C0-p-A01 | CHECK_PASS | PASS | {"claim_type": "TenantLocalExecutionClaim", "raised": null} | {"claim_type": "TenantLocalExecutionClaim", "raised": null} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C0-p-A02 | CHECK_PASS | PASS | true | true |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C0-p-A03 | CHECK_PASS | PASS | {"authority_domain": "customer-refunds", "claim_id": "bq-claim-C0-p", "decision_id": "3368c9a9-05e1-44ed-9c02-c19c01534a1d", "manifest_digest": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac", " | {"authority_domain": "customer-refunds", "claim_id": "bq-claim-C0-p", "decision_id": "3368c9a9-05e1-44ed-9c02-c19c01534a1d", "manifest_digest": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac", " |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C0-p-A04 | CHECK_PASS | PASS | {"n_new": 1, "reasons": [], "stage": "claim"} | {"n_new": 1, "reasons": [], "stage": "claim"} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C0-p-A05 | CHECK_PASS | PASS | {"resolution_checks": 1} | {"resolution_checks": 1} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C0-p-A06 | CHECK_PASS | PASS | true | true |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C0-p-A07 | CHECK_PASS | PASS | {"calls": 0, "unchanged": true} | {"calls": 0, "unchanged": true} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C0-p-A08 | CHECK_PASS | PASS | {"calls": 1, "is_returned_claim": true} | {"calls": 1, "is_returned_claim": true} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-P01 | CHECK_PASS | PASS | {"reasons": [], "result": "authorized"} | {"reasons": [], "result": "authorized"} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-P02 | CHECK_PASS | PASS | {"reasons": [], "result": "authorized"} | {"reasons": [], "result": "authorized"} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-P03 | CHECK_PASS | PASS | ["customer-refunds", "other-domain"] | ["customer-refunds", "other-domain"] |
| N-CLAIM-JOINT | N-CLAIM-JOINT-P04 | CHECK_PASS | PASS | {"X_and_Y_proposal_commitments_differ": true, "X_manifest_digest_differs_from_Y": true, "Y_manifest_digest_is_commitment_of_Y_manifest": true, "y_approvals_bound_to_Y_proposal": true} | {"X_and_Y_proposal_commitments_differ": true, "X_manifest_digest_differs_from_Y": true, "Y_manifest_digest_is_commitment_of_Y_manifest": true, "y_approvals_bound_to_Y_proposal": true} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C1-P05 | CHECK_PASS | PASS | {"found": true, "result": "authorized"} | {"found": true, "result": "authorized"} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C1-A01 | CHECK_PASS | PASS | ["PermissionError", "authorization-critical inputs changed before claim issuance"] | ["PermissionError", "authorization-critical inputs changed before claim issuance"] |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C1-A02 | CHECK_PASS | PASS | false | false |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C1-A03 | CHECK_PASS | PASS | {"n_new": 1, "reasons": ["approval_operation_binding_mismatch", "manifest_digest_mismatch"], "stage": "claim"} | {"n_new": 1, "reasons": ["approval_operation_binding_mismatch", "manifest_digest_mismatch"], "stage": "claim"} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C1-A04 | CHECK_PASS | PASS | {"authority_domain_mismatch": false, "authorization_binding_changed": false} | {"authority_domain_mismatch": false, "authorization_binding_changed": false} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C1-A05 | CHECK_PASS | PASS | {"decisions_equal": true, "nonzero": {"resolution_checks": 1}, "refusals": 0} | {"decisions_equal": true, "nonzero": {"resolution_checks": 1}, "refusals": 0} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C1-A06 | CHECK_PASS | PASS | {"calls": 0, "unchanged": true} | {"calls": 0, "unchanged": true} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C2-P01 | CHECK_PASS | PASS | {"reasons": [], "result": "authorized"} | {"reasons": [], "result": "authorized"} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C2-P02 | CHECK_PASS | PASS | {"distinct_resolver_objects": true, "same_domain": true, "same_manifest_commitment": true, "same_proposal_commitment": true} | {"distinct_resolver_objects": true, "same_domain": true, "same_manifest_commitment": true, "same_proposal_commitment": true} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C2-P03 | CHECK_PASS | PASS | {"reasons": [], "result": "authorized"} | {"reasons": [], "result": "authorized"} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C2-A00 | CHECK_PASS | PASS | {"base": [], "ecb": []} | {"base": [], "ecb": []} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C2-A01 | CHECK_PASS | PASS | {"claim_type": "TenantLocalExecutionClaim", "raised": null} | {"claim_type": "TenantLocalExecutionClaim", "raised": null} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C2-A02 | CHECK_PASS | PASS | true | true |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C2-A03 | CHECK_PASS | PASS | {"authority_domain": "customer-refunds", "claim_id": "bq-claim-C2", "decision_id": "2944fbce-8996-4879-b12e-71cb0b93863b", "manifest_digest": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac", "pr | {"authority_domain": "customer-refunds", "claim_id": "bq-claim-C2", "decision_id": "2944fbce-8996-4879-b12e-71cb0b93863b", "manifest_digest": "sha256:4d1ad6c96bc242c63998231b4df3ad7c86dc2e5e59cdae63afe7bff86e60f6ac", "pr |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C2-A04 | CHECK_PASS | PASS | {"n_new": 1, "reasons": [], "stage": "claim"} | {"n_new": 1, "reasons": [], "stage": "claim"} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C2-A05 | CHECK_PASS | PASS | {"resolution_checks": 1} | {"resolution_checks": 1} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C2-A06 | CHECK_PASS | PASS | true | true |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C2-A07 | CHECK_PASS | PASS | {"calls": 0, "unchanged": true} | {"calls": 0, "unchanged": true} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-C2-A08 | CHECK_PASS | PASS | {"calls": 0, "is_returned_claim": null} | {"calls": 0, "is_returned_claim": null} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-P01 | CHECK_PASS | PASS | {"reasons": [], "result": "authorized"} | {"reasons": [], "result": "authorized"} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-P02 | CHECK_PASS | PASS | {"reasons": [], "result": "authorized"} | {"reasons": [], "result": "authorized"} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-P03 | CHECK_PASS | PASS | ["customer-refunds", "other-domain"] | ["customer-refunds", "other-domain"] |
| N-CLAIM-JOINT | N-CLAIM-JOINT-P04 | CHECK_PASS | PASS | {"X_and_Y_proposal_commitments_differ": true, "X_manifest_digest_differs_from_Y": true, "Y_manifest_digest_is_commitment_of_Y_manifest": true, "y_approvals_bound_to_Y_proposal": true} | {"X_and_Y_proposal_commitments_differ": true, "X_manifest_digest_differs_from_Y": true, "Y_manifest_digest_is_commitment_of_Y_manifest": true, "y_approvals_bound_to_Y_proposal": true} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-CY-A01 | CHECK_PASS | PASS | {"claim_type": "TenantLocalExecutionClaim", "raised": null} | {"claim_type": "TenantLocalExecutionClaim", "raised": null} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-CY-A02 | CHECK_PASS | PASS | true | true |
| N-CLAIM-JOINT | N-CLAIM-JOINT-CY-A03 | CHECK_PASS | PASS | {"authority_domain": "other-domain", "claim_id": "bq-claim-CY", "decision_id": "69faf7d4-b2b0-46c2-96f9-bb9ada94fe9f", "manifest_digest": "sha256:16c8f8999d73c9560d10f49469b7a316ba4f2b8f636c3593ccf719a5eec32b22", "profil | {"authority_domain": "other-domain", "claim_id": "bq-claim-CY", "decision_id": "69faf7d4-b2b0-46c2-96f9-bb9ada94fe9f", "manifest_digest": "sha256:16c8f8999d73c9560d10f49469b7a316ba4f2b8f636c3593ccf719a5eec32b22", "profil |
| N-CLAIM-JOINT | N-CLAIM-JOINT-CY-A04 | CHECK_PASS | PASS | {"n_new": 1, "reasons": [], "stage": "claim"} | {"n_new": 1, "reasons": [], "stage": "claim"} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-CY-A05 | CHECK_PASS | PASS | {"resolution_checks": 1} | {"resolution_checks": 1} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-CY-A06 | CHECK_PASS | PASS | true | true |
| N-CLAIM-JOINT | N-CLAIM-JOINT-CY-A07 | CHECK_PASS | PASS | {"calls": 0, "unchanged": true} | {"calls": 0, "unchanged": true} |
| N-CLAIM-JOINT | N-CLAIM-JOINT-CY-A08 | CHECK_PASS | PASS | {"calls": 0, "is_returned_claim": null} | {"calls": 0, "is_returned_claim": null} |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P01 | CHECK_PASS | PASS | constructed | constructed |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P02 | CHECK_PASS | PASS | completed | completed |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P03 | CHECK_PASS | PASS | authorized | authorized |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P04 | CHECK_PASS | PASS | constructed | constructed |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P05 | CHECK_PASS | PASS | {"A": {"synthetic-irreversible": 70}, "B": {"synthetic-irreversible": 90}} | {"A": {"synthetic-irreversible": 70}, "B": {"synthetic-irreversible": 90}} |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P06 | CHECK_PASS | PASS | {"A": {"synthetic-irreversible": 60}, "B": {"synthetic-irreversible": 60}} | {"A": {"synthetic-irreversible": 60}, "B": {"synthetic-irreversible": 60}} |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P07 | CHECK_PASS | PASS | {"A": {"synthetic-irreversible": 60}, "B": {"synthetic-irreversible": 60}} | {"A": {"synthetic-irreversible": 60}, "B": {"synthetic-irreversible": 60}} |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P08 | CHECK_PASS | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P09 | CHECK_PASS | PASS | ["freshness.max_age_extension_seconds"] | ["freshness.max_age_extension_seconds"] |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P10 | CHECK_PASS | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P11 | CHECK_PASS | PASS | completed | completed |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P12 | CHECK_PASS | PASS | authorized | authorized |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A01 | CHECK_PASS | PASS | {"actions": {"urn:cognous:action:refund-issue-routine-v1": {"class_id": "synthetic-irreversible", "irreversible": true, "max_status_age_seconds": 60, "on_unreadable": "refuse"}}, "allow_synthetic_resolver": true, "catalo | {"actions": {"urn:cognous:action:refund-issue-routine-v1": {"class_id": "synthetic-irreversible", "irreversible": true, "max_status_age_seconds": 60, "on_unreadable": "refuse"}}, "allow_synthetic_resolver": true, "catalo |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A02 | CHECK_PASS | PASS | {"actions": {"urn:cognous:action:refund-issue-routine-v1": {"class_id": "synthetic-irreversible", "irreversible": true, "max_status_age_seconds": 60, "on_unreadable": "refuse"}}, "allow_synthetic_resolver": true, "catalo | {"actions": {"urn:cognous:action:refund-issue-routine-v1": {"class_id": "synthetic-irreversible", "irreversible": true, "max_status_age_seconds": 60, "on_unreadable": "refuse"}}, "allow_synthetic_resolver": true, "catalo |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A03 | CHECK_PASS | PASS | sha256:3890bb78a2a28ec8d9fc23d04c1ae565ed82bef5c0f19e1cc26928cfe4f8c278 | sha256:3890bb78a2a28ec8d9fc23d04c1ae565ed82bef5c0f19e1cc26928cfe4f8c278 |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A04 | CHECK_PASS | PASS | sha256:3890bb78a2a28ec8d9fc23d04c1ae565ed82bef5c0f19e1cc26928cfe4f8c278 | sha256:3890bb78a2a28ec8d9fc23d04c1ae565ed82bef5c0f19e1cc26928cfe4f8c278 |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A05 | CHECK_PASS | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A06 | CHECK_PASS | PASS | sha256:4fa513a2c3cf277bdd48cf9d75b62d1c96386e8f29564ed04133bd2f6b1ad380 | sha256:4fa513a2c3cf277bdd48cf9d75b62d1c96386e8f29564ed04133bd2f6b1ad380 |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A07 | CHECK_PASS | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A08 | CHECK_PASS | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A09 | CHECK_PASS | PASS | sha256:1e789f717b6bd1b3cbda968024bbef58ca11c777f3f712fae3ac7a9b501991ce | sha256:1e789f717b6bd1b3cbda968024bbef58ca11c777f3f712fae3ac7a9b501991ce |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A10 | CHECK_PASS | PASS | sha256:1e789f717b6bd1b3cbda968024bbef58ca11c777f3f712fae3ac7a9b501991ce | sha256:1e789f717b6bd1b3cbda968024bbef58ca11c777f3f712fae3ac7a9b501991ce |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A11 | CHECK_PASS | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A12 | CHECK_PASS | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A13 | CHECK_PASS | PASS | sha256:4fa513a2c3cf277bdd48cf9d75b62d1c96386e8f29564ed04133bd2f6b1ad380 | sha256:4fa513a2c3cf277bdd48cf9d75b62d1c96386e8f29564ed04133bd2f6b1ad380 |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A14 | CHECK_PASS | PASS | ["runtime_authority.approval_commitment", "runtime_authority.catalogue_digest"] | ["runtime_authority.approval_commitment", "runtime_authority.catalogue_digest"] |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A15 | CHECK_PASS | PASS | ["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.effective_profile_digest"] | ["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.effective_profile_digest"] |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A16 | CHECK_PASS | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A17 | CHECK_PASS | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A18 | CHECK_PASS | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A19 | CHECK_PASS | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A20 | CHECK_PASS | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A21 | CHECK_PASS | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A22 | CHECK_PASS | PASS | joint | joint |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A23 | CHECK_PASS | PASS | {"n": 1, "slot": "class_age"} | {"n": 1, "slot": "class_age"} |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A24 | CHECK_PASS | PASS | PermissionError | PermissionError |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A25 | CHECK_PASS | PASS | authorization-critical inputs changed before effect | authorization-critical inputs changed before effect |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A26 | CHECK_PASS | PASS | [["authorization_binding_changed"]] | [["authorization_binding_changed"]] |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A27 | CHECK_PASS | PASS | ["runtime-authority-reasons/0.1"] | ["runtime-authority-reasons/0.1"] |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A28 | CHECK_PASS | PASS | {"new_attempts": 0, "total_attempts_after": 0} | {"new_attempts": 0, "total_attempts_after": 0} |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A29 | CHECK_PASS | PASS | {"dest_calls": 0, "dest_unchanged": true} | {"dest_calls": 0, "dest_unchanged": true} |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A30 | CHECK_PASS | PASS | {"age_extensions": [0, 0], "decisions": [1, 1], "refusals": [0, 1]} | {"age_extensions": [0, 0], "decisions": [1, 1], "refusals": [0, 1]} |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A31 | CHECK_PASS | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A32 | CHECK_PASS | PASS | mismatch | mismatch |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-P01 | CHECK_PASS | PASS | constructed | constructed |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-P02 | CHECK_PASS | PASS | completed | completed |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-P03 | CHECK_PASS | PASS | authorized | authorized |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-P04 | CHECK_PASS | PASS | constructed | constructed |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-P05 | CHECK_PASS | PASS | completed | completed |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-P06 | CHECK_PASS | PASS | authorized | authorized |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-A01 | CHECK_PASS | PASS | [] | [] |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-A02 | CHECK_PASS | PASS | [] | [] |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-A03 | CHECK_PASS | PASS | {"attempt_status": "acknowledged", "raised": null} | {"attempt_status": "acknowledged", "raised": null} |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-A04 | CHECK_PASS | PASS | [] | [] |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-A05 | CHECK_PASS | PASS | 1 | 1 |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-A06 | CHECK_PASS | PASS | bound | bound |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-A07 | CHECK_PASS | PASS | sha256:3890bb78a2a28ec8d9fc23d04c1ae565ed82bef5c0f19e1cc26928cfe4f8c278 | sha256:3890bb78a2a28ec8d9fc23d04c1ae565ed82bef5c0f19e1cc26928cfe4f8c278 |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-A08 | CHECK_PASS | PASS | sha256:3890bb78a2a28ec8d9fc23d04c1ae565ed82bef5c0f19e1cc26928cfe4f8c278 | sha256:3890bb78a2a28ec8d9fc23d04c1ae565ed82bef5c0f19e1cc26928cfe4f8c278 |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-P01 | CHECK_PASS | PASS | constructed | constructed |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-P02 | CHECK_PASS | PASS | completed | completed |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-P03 | CHECK_PASS | PASS | authorized | authorized |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-P04 | CHECK_PASS | PASS | constructed | constructed |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-P05 | CHECK_PASS | PASS | ["freshness.max_age_extension_seconds"] | ["freshness.max_age_extension_seconds"] |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-A01 | CHECK_PASS | PASS | PermissionError | PermissionError |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-A02 | CHECK_PASS | PASS | authorization-critical inputs changed before effect | authorization-critical inputs changed before effect |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-A03 | CHECK_PASS | PASS | [["runtime_authority_approval_mismatch"]] | [["runtime_authority_approval_mismatch"]] |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-A04 | CHECK_PASS | PASS | false | false |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-A05 | CHECK_PASS | PASS | ["runtime-authority-reasons/0.1"] | ["runtime-authority-reasons/0.1"] |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-A06 | CHECK_PASS | PASS | {"new_attempts": 0, "total_attempts_after": 0} | {"new_attempts": 0, "total_attempts_after": 0} |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-A07 | CHECK_PASS | PASS | {"dest_calls": 0, "dest_unchanged": true} | {"dest_calls": 0, "dest_unchanged": true} |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-A08 | CHECK_PASS | PASS | {"decisions": [1, 1], "refusals": [0, 1]} | {"decisions": [1, 1], "refusals": [0, 1]} |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-P01 | CHECK_PASS | PASS | {"epoch": [1, 2], "record_text_equal": true, "selection_id": ["sel-test-1", "sel-test-2"], "selection_text_equal": false} | {"epoch": [1, 2], "record_text_equal": true, "selection_id": ["sel-test-1", "sel-test-2"], "selection_text_equal": false} |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-P02 | CHECK_PASS | PASS | constructed | constructed |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-P03 | CHECK_PASS | PASS | completed | completed |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-P04 | CHECK_PASS | PASS | authorized | authorized |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-P05 | CHECK_PASS | PASS | constructed | constructed |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-P06 | CHECK_PASS | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-P07 | CHECK_PASS | PASS | completed | completed |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-P08 | CHECK_PASS | PASS | authorized | authorized |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-A01 | CHECK_PASS | PASS | [] | [] |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-A02 | CHECK_PASS | PASS | [] | [] |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-A03 | CHECK_PASS | PASS | {"attempt_status": "acknowledged", "raised": null} | {"attempt_status": "acknowledged", "raised": null} |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-A04 | CHECK_PASS | PASS | [] | [] |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-A05 | CHECK_PASS | PASS | 1 | 1 |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-A06 | CHECK_PASS | PASS | bound | bound |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-A07 | CHECK_PASS | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-P01 | CHECK_PASS | PASS | constructed | constructed |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-P02 | CHECK_PASS | PASS | completed | completed |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-P03 | CHECK_PASS | PASS | authorized | authorized |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-P04 | CHECK_PASS | PASS | constructed | constructed |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-P05 | CHECK_PASS | PASS | completed | completed |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-P06 | CHECK_PASS | PASS | authorized | authorized |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-A01 | CHECK_PASS | PASS | {"actions": {"urn:cognous:action:refund-issue-routine-v1": {"class_id": "synthetic-irreversible", "irreversible": true, "max_status_age_seconds": 50, "on_unreadable": "refuse"}}, "allow_synthetic_resolver": true, "catalo | {"actions": {"urn:cognous:action:refund-issue-routine-v1": {"class_id": "synthetic-irreversible", "irreversible": true, "max_status_age_seconds": 50, "on_unreadable": "refuse"}}, "allow_synthetic_resolver": true, "catalo |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-A02 | CHECK_PASS | PASS | {"synthetic-irreversible": 50} | {"synthetic-irreversible": 50} |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-A03 | CHECK_PASS | PASS | ["runtime_authority.approval_commitment", "runtime_authority.catalogue_digest"] | ["runtime_authority.approval_commitment", "runtime_authority.catalogue_digest"] |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-A04 | CHECK_PASS | PASS | ["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.effective_profile_digest", "runtime_authority.effective_configuration.members.families.0.effective_policy_digest"] | ["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.effective_profile_digest", "runtime_authority.effective_configuration.members.families.0.effective_policy_digest"] |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-A05 | CHECK_PASS | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-A06 | CHECK_PASS | PASS | joint | joint |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-A07 | CHECK_PASS | PASS | PermissionError | PermissionError |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-A08 | CHECK_PASS | PASS | [["authorization_binding_changed"]] | [["authorization_binding_changed"]] |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-A09 | CHECK_PASS | PASS | {"new_attempts": 0, "total_attempts_after": 0} | {"new_attempts": 0, "total_attempts_after": 0} |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-A10 | CHECK_PASS | PASS | {"dest_calls": 0, "dest_unchanged": true} | {"dest_calls": 0, "dest_unchanged": true} |
| FC-H1 | FC-H1-P01 | PRECONDITION_PASS | PASS | authorized | authorized |
| FC-H1 | FC-H1-P02 | PRECONDITION_PASS | PASS | urn:cognous:action:refund-issue-routine-v1 | urn:cognous:action:refund-issue-routine-v1 |
| FC-H1 | FC-H1-P03 | PRECONDITION_PASS | PASS | authorized | authorized |
| FC-H1 | FC-H1-P04 | PRECONDITION_PASS | PASS | issued | issued |
| FC-H1 | FC-H1-C01 | CHECK_PASS | PASS | [] | [] |
| FC-H1 | FC-H1-C02 | CHECK_PASS | PASS | [] | [] |
| FC-H1 | FC-H1-C03 | CHECK_PASS | PASS | true | true |
| FC-H1 | FC-H1-C04 | CHECK_PASS | PASS | ["d62c0069-f526-4d6b-b484-d858e875a846", "bq-fc-h1-control"] | ["d62c0069-f526-4d6b-b484-d858e875a846", "bq-fc-h1-control"] |
| FC-H1 | FC-H1-C05 | CHECK_PASS | PASS | false | false |
| FC-H1 | FC-H1-C06 | CHECK_PASS | PASS | [1, 0, true] | [1, 0, true] |
| FC-H1 | FC-H1-C07 | CHECK_PASS | PASS | {"attempts": 0, "decisions": 0, "refusals": 0} | {"attempts": 0, "decisions": 0, "refusals": 0} |
| FC-H1 | FC-H1-P05 | PRECONDITION_PASS | PASS | authorized | authorized |
| FC-H1 | FC-H1-P06 | PRECONDITION_PASS | PASS | [60, 61] | [60, 61] |
| FC-H1 | FC-H1-P07 | PRECONDITION_PASS | PASS | ["actions.urn:cognous:action:refund-issue-routine-v1.max_status_age_seconds"] | ["actions.urn:cognous:action:refund-issue-routine-v1.max_status_age_seconds"] |
| FC-H1 | FC-H1-P08 | PRECONDITION_PASS | PASS | true | true |
| FC-H1 | FC-H1-P09 | PRECONDITION_PASS | PASS | true | true |
| FC-H1 | FC-H1-P10 | PRECONDITION_PASS | PASS | true | true |
| FC-H1 | FC-H1-P11 | PRECONDITION_PASS | PASS | [10, 10] | [10, 10] |
| FC-H1 | FC-H1-P12 | PRECONDITION_PASS | PASS | authorized | authorized |
| FC-H1 | FC-H1-P13 | PRECONDITION_PASS | PASS | [true, true, true] | [true, true, true] |
| FC-H1 | FC-H1-A01 | CHECK_PASS | PASS | [] | [] |
| FC-H1 | FC-H1-A02 | CHECK_PASS | PASS | ["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.host_profile_digest"] | ["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.host_profile_digest"] |
| FC-H1 | FC-H1-A03 | CHECK_PASS | PASS | PermissionError | PermissionError |
| FC-H1 | FC-H1-A04 | CHECK_PASS | PASS | true | true |
| FC-H1 | FC-H1-A05 | CHECK_PASS | PASS | authorization-critical inputs changed before claim issuance | authorization-critical inputs changed before claim issuance |
| FC-H1 | FC-H1-A06 | CHECK_PASS | PASS | false | false |
| FC-H1 | FC-H1-A07 | CHECK_PASS | PASS | 0 | 0 |
| FC-H1 | FC-H1-A08 | CHECK_PASS | PASS | 0 | 0 |
| FC-H1 | FC-H1-A09 | CHECK_PASS | PASS | {"closeouts": 0, "decisions": 0, "observations": 0, "reconciliations": 0} | {"closeouts": 0, "decisions": 0, "observations": 0, "reconciliations": 0} |
| FC-H1 | FC-H1-A10 | CHECK_PASS | PASS | [0, true] | [0, true] |
| FC-H1 | FC-H1-A11 | CHECK_PASS | PASS | [] | [] |
| FC-H1 | FC-H1-A12 | CHECK_PASS | PASS | 1 | 1 |
| FC-H1 | FC-H1-A13 | CHECK_PASS | PASS | [["claim", []]] | [["claim", []]] |
| FC-H1 | FC-H1-A14 | CHECK_PASS | PASS | true | true |
| FC-H2 | FC-H2-P01 | PRECONDITION_PASS | PASS | authorized | authorized |
| FC-H2 | FC-H2-P02 | PRECONDITION_PASS | PASS | urn:cognous:action:refund-issue-routine-v1 | urn:cognous:action:refund-issue-routine-v1 |
| FC-H2 | FC-H2-P03 | PRECONDITION_PASS | PASS | authorized | authorized |
| FC-H2 | FC-H2-C01 | CHECK_PASS | PASS | [] | [] |
| FC-H2 | FC-H2-C02 | CHECK_PASS | PASS | [] | [] |
| FC-H2 | FC-H2-C03 | CHECK_PASS | PASS | ["acknowledged", null] | ["acknowledged", null] |
| FC-H2 | FC-H2-C04 | CHECK_PASS | PASS | [] | [] |
| FC-H2 | FC-H2-C05 | CHECK_PASS | PASS | 1 | 1 |
| FC-H2 | FC-H2-P04 | PRECONDITION_PASS | PASS | authorized | authorized |
| FC-H2 | FC-H2-P05 | PRECONDITION_PASS | PASS | [false, false] | [false, false] |
| FC-H2 | FC-H2-P06 | PRECONDITION_PASS | PASS | ["bounded_tolerance", "refuse"] | ["bounded_tolerance", "refuse"] |
| FC-H2 | FC-H2-P07 | PRECONDITION_PASS | PASS | ["actions.urn:cognous:action:refund-issue-routine-v1.on_unreadable"] | ["actions.urn:cognous:action:refund-issue-routine-v1.on_unreadable"] |
| FC-H2 | FC-H2-P08 | PRECONDITION_PASS | PASS | true | true |
| FC-H2 | FC-H2-P09 | PRECONDITION_PASS | PASS | true | true |
| FC-H2 | FC-H2-P10 | PRECONDITION_PASS | PASS | true | true |
| FC-H2 | FC-H2-P11 | PRECONDITION_PASS | PASS | ["refuse", "refuse"] | ["refuse", "refuse"] |
| FC-H2 | FC-H2-P12 | PRECONDITION_PASS | PASS | authorized | authorized |
| FC-H2 | FC-H2-P13 | PRECONDITION_PASS | PASS | [true, true, true, true] | [true, true, true, true] |
| FC-H2 | FC-H2-P14 | PRECONDITION_PASS | PASS | [["class_unreadable"], ["class_unreadable"]] | [["class_unreadable"], ["class_unreadable"]] |
| FC-H2 | FC-H2-A01 | CHECK_PASS | PASS | [] | [] |
| FC-H2 | FC-H2-A02 | CHECK_PASS | PASS | ["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.host_profile_digest"] | ["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.host_profile_digest"] |
| FC-H2 | FC-H2-A03 | CHECK_PASS | PASS | PermissionError | PermissionError |
| FC-H2 | FC-H2-A04 | CHECK_PASS | PASS | authorization-critical inputs changed before effect | authorization-critical inputs changed before effect |
| FC-H2 | FC-H2-A05 | CHECK_PASS | PASS | [["authorization_binding_changed"]] | [["authorization_binding_changed"]] |
| FC-H2 | FC-H2-A06 | CHECK_PASS | PASS | ["runtime-authority-reasons/0.1"] | ["runtime-authority-reasons/0.1"] |
| FC-H2 | FC-H2-A07 | CHECK_PASS | PASS | 0 | 0 |
| FC-H2 | FC-H2-A08 | CHECK_PASS | PASS | [0, true] | [0, true] |
| FC-H3a | FC-H3a-P01 | PRECONDITION_PASS | PASS | authorized | authorized |
| FC-H3a | FC-H3a-P02 | PRECONDITION_PASS | PASS | urn:cognous:action:refund-issue-routine-v1 | urn:cognous:action:refund-issue-routine-v1 |
| FC-H3a | FC-H3a-P03 | PRECONDITION_PASS | PASS | [60, 5] | [60, 5] |
| FC-H3a | FC-H3a-P04 | PRECONDITION_PASS | PASS | ["actions.urn:cognous:action:refund-issue-routine-v1.max_status_age_seconds"] | ["actions.urn:cognous:action:refund-issue-routine-v1.max_status_age_seconds"] |
| FC-H3a | FC-H3a-P05 | PRECONDITION_PASS | PASS | [10, 5] | [10, 5] |
| FC-H3a | FC-H3a-P06 | PRECONDITION_PASS | PASS | true | true |
| FC-H3a | FC-H3a-P07 | PRECONDITION_PASS | PASS | true | true |
| FC-H3a | FC-H3a-A01 | CHECK_PASS | PASS | PermissionError | PermissionError |
| FC-H3a | FC-H3a-A02 | CHECK_PASS | PASS | authorization-critical inputs changed before effect | authorization-critical inputs changed before effect |
| FC-H3a | FC-H3a-A03 | CHECK_PASS | PASS | [["runtime_authority_approval_mismatch"]] | [["runtime_authority_approval_mismatch"]] |
| FC-H3a | FC-H3a-A04 | CHECK_PASS | PASS | ["runtime-authority-reasons/0.1"] | ["runtime-authority-reasons/0.1"] |
| FC-H3a | FC-H3a-A05 | CHECK_PASS | PASS | 0 | 0 |
| FC-H3a | FC-H3a-A06 | CHECK_PASS | PASS | [0, true] | [0, true] |
| FC-H3a | FC-H3a-A07 | CHECK_PASS | PASS | false | false |
| FC-H3b | FC-H3b-P01 | PRECONDITION_PASS | PASS | authorized | authorized |
| FC-H3b | FC-H3b-P02 | PRECONDITION_PASS | PASS | urn:cognous:action:refund-issue-routine-v1 | urn:cognous:action:refund-issue-routine-v1 |
| FC-H3b | FC-H3b-P03 | PRECONDITION_PASS | PASS | [60, 5] | [60, 5] |
| FC-H3b | FC-H3b-P04 | PRECONDITION_PASS | PASS | ["actions.urn:cognous:action:refund-issue-routine-v1.max_status_age_seconds"] | ["actions.urn:cognous:action:refund-issue-routine-v1.max_status_age_seconds"] |
| FC-H3b | FC-H3b-P05 | PRECONDITION_PASS | PASS | [10, 5] | [10, 5] |
| FC-H3b | FC-H3b-P06 | PRECONDITION_PASS | PASS | true | true |
| FC-H3b | FC-H3b-P07 | PRECONDITION_PASS | PASS | true | true |
| FC-H3b | FC-H3b-P08 | PRECONDITION_PASS | PASS | authorized | authorized |
| FC-H3b | FC-H3b-A01 | CHECK_PASS | PASS | ["runtime_authority.approval_commitment", "runtime_authority.catalogue_digest"] | ["runtime_authority.approval_commitment", "runtime_authority.catalogue_digest"] |
| FC-H3b | FC-H3b-A02 | CHECK_PASS | PASS | ["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.effective_profile_digest", "runtime_authority.effective_configuration.members.families.0.effective_policy_digest", " | ["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.effective_profile_digest", "runtime_authority.effective_configuration.members.families.0.effective_policy_digest", " |
| FC-H3b | FC-H3b-A03 | CHECK_PASS | PASS | joint | joint |
| FC-H3b | FC-H3b-A04 | CHECK_PASS | PASS | PermissionError | PermissionError |
| FC-H3b | FC-H3b-A05 | CHECK_PASS | PASS | authorization-critical inputs changed before effect | authorization-critical inputs changed before effect |
| FC-H3b | FC-H3b-A06 | CHECK_PASS | PASS | [["authorization_binding_changed"]] | [["authorization_binding_changed"]] |
| FC-H3b | FC-H3b-A07 | CHECK_PASS | PASS | ["runtime-authority-reasons/0.1"] | ["runtime-authority-reasons/0.1"] |
| FC-H3b | FC-H3b-A08 | CHECK_PASS | PASS | 0 | 0 |
| FC-H3b | FC-H3b-A09 | CHECK_PASS | PASS | [0, true] | [0, true] |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P01 | PRECONDITION | PASS | constructed | constructed |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P02 | PRECONDITION | PASS | completed | completed |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P03 | PRECONDITION | PASS | authorized | authorized |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P04 | PRECONDITION | PASS | constructed | constructed |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P05 | PRECONDITION | PASS | {"A": {"synthetic-irreversible": 70}, "B": {"synthetic-irreversible": 90}} | {"A": {"synthetic-irreversible": 70}, "B": {"synthetic-irreversible": 90}} |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P06 | PRECONDITION | PASS | {"A": {"synthetic-irreversible": 60}, "B": {"synthetic-irreversible": 60}} | {"A": {"synthetic-irreversible": 60}, "B": {"synthetic-irreversible": 60}} |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P07 | PRECONDITION | PASS | {"A": {"synthetic-irreversible": 60}, "B": {"synthetic-irreversible": 60}} | {"A": {"synthetic-irreversible": 60}, "B": {"synthetic-irreversible": 60}} |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P08 | PRECONDITION | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P09 | PRECONDITION | PASS | ["freshness.max_age_extension_seconds"] | ["freshness.max_age_extension_seconds"] |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P10 | PRECONDITION | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P11 | PRECONDITION | PASS | completed | completed |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-P12 | PRECONDITION | PASS | authorized | authorized |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A01 | ASSERTION | PASS | {"actions": {"urn:cognous:action:refund-issue-routine-v1": {"class_id": "synthetic-irreversible", "irreversible": true, "max_status_age_seconds": 60, "on_unreadable": "refuse"}}, "allow_synthetic_resolver": true, "catalo | {"actions": {"urn:cognous:action:refund-issue-routine-v1": {"class_id": "synthetic-irreversible", "irreversible": true, "max_status_age_seconds": 60, "on_unreadable": "refuse"}}, "allow_synthetic_resolver": true, "catalo |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A02 | ASSERTION | PASS | {"actions": {"urn:cognous:action:refund-issue-routine-v1": {"class_id": "synthetic-irreversible", "irreversible": true, "max_status_age_seconds": 60, "on_unreadable": "refuse"}}, "allow_synthetic_resolver": true, "catalo | {"actions": {"urn:cognous:action:refund-issue-routine-v1": {"class_id": "synthetic-irreversible", "irreversible": true, "max_status_age_seconds": 60, "on_unreadable": "refuse"}}, "allow_synthetic_resolver": true, "catalo |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A03 | ASSERTION | PASS | sha256:3890bb78a2a28ec8d9fc23d04c1ae565ed82bef5c0f19e1cc26928cfe4f8c278 | sha256:3890bb78a2a28ec8d9fc23d04c1ae565ed82bef5c0f19e1cc26928cfe4f8c278 |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A04 | ASSERTION | PASS | sha256:3890bb78a2a28ec8d9fc23d04c1ae565ed82bef5c0f19e1cc26928cfe4f8c278 | sha256:3890bb78a2a28ec8d9fc23d04c1ae565ed82bef5c0f19e1cc26928cfe4f8c278 |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A05 | ASSERTION | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A06 | ASSERTION | PASS | sha256:4fa513a2c3cf277bdd48cf9d75b62d1c96386e8f29564ed04133bd2f6b1ad380 | sha256:4fa513a2c3cf277bdd48cf9d75b62d1c96386e8f29564ed04133bd2f6b1ad380 |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A07 | ASSERTION | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A08 | ASSERTION | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A09 | ASSERTION | PASS | sha256:1e789f717b6bd1b3cbda968024bbef58ca11c777f3f712fae3ac7a9b501991ce | sha256:1e789f717b6bd1b3cbda968024bbef58ca11c777f3f712fae3ac7a9b501991ce |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A10 | ASSERTION | PASS | sha256:1e789f717b6bd1b3cbda968024bbef58ca11c777f3f712fae3ac7a9b501991ce | sha256:1e789f717b6bd1b3cbda968024bbef58ca11c777f3f712fae3ac7a9b501991ce |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A11 | ASSERTION | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A12 | ASSERTION | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A13 | ASSERTION | PASS | sha256:4fa513a2c3cf277bdd48cf9d75b62d1c96386e8f29564ed04133bd2f6b1ad380 | sha256:4fa513a2c3cf277bdd48cf9d75b62d1c96386e8f29564ed04133bd2f6b1ad380 |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A14 | ASSERTION | PASS | ["runtime_authority.approval_commitment", "runtime_authority.catalogue_digest"] | ["runtime_authority.approval_commitment", "runtime_authority.catalogue_digest"] |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A15 | ASSERTION | PASS | ["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.effective_profile_digest"] | ["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.effective_profile_digest"] |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A16 | ASSERTION | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A17 | ASSERTION | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A18 | ASSERTION | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A19 | ASSERTION | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A20 | ASSERTION | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A21 | ASSERTION | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A22 | ASSERTION | PASS | joint | joint |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A23 | ASSERTION | PASS | {"n": 1, "slot": "class_age"} | {"n": 1, "slot": "class_age"} |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A24 | ASSERTION | PASS | PermissionError | PermissionError |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A25 | ASSERTION | PASS | authorization-critical inputs changed before effect | authorization-critical inputs changed before effect |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A26 | ASSERTION | PASS | [["authorization_binding_changed"]] | [["authorization_binding_changed"]] |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A27 | ASSERTION | PASS | ["runtime-authority-reasons/0.1"] | ["runtime-authority-reasons/0.1"] |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A28 | ASSERTION | PASS | {"new_attempts": 0, "total_attempts_after": 0} | {"new_attempts": 0, "total_attempts_after": 0} |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A29 | ASSERTION | PASS | {"dest_calls": 0, "dest_unchanged": true} | {"dest_calls": 0, "dest_unchanged": true} |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A30 | ASSERTION | PASS | {"age_extensions": [0, 0], "decisions": [1, 1], "refusals": [0, 1]} | {"age_extensions": [0, 0], "decisions": [1, 1], "refusals": [0, 1]} |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A31 | ASSERTION | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_main | FXE-JOINT-A32 | ASSERTION | PASS | mismatch | mismatch |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-P01 | PRECONDITION | PASS | constructed | constructed |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-P02 | PRECONDITION | PASS | completed | completed |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-P03 | PRECONDITION | PASS | authorized | authorized |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-P04 | PRECONDITION | PASS | constructed | constructed |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-P05 | PRECONDITION | PASS | completed | completed |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-P06 | PRECONDITION | PASS | authorized | authorized |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-A01 | CONTROL | PASS | [] | [] |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-A02 | CONTROL | PASS | [] | [] |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-A03 | CONTROL | PASS | {"attempt_status": "acknowledged", "raised": null} | {"attempt_status": "acknowledged", "raised": null} |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-A04 | CONTROL | PASS | [] | [] |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-A05 | CONTROL | PASS | 1 | 1 |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-A06 | CONTROL | PASS | bound | bound |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-A07 | CONTROL | PASS | sha256:3890bb78a2a28ec8d9fc23d04c1ae565ed82bef5c0f19e1cc26928cfe4f8c278 | sha256:3890bb78a2a28ec8d9fc23d04c1ae565ed82bef5c0f19e1cc26928cfe4f8c278 |
| FXE-JOINT/test_FXE_JOINT_C0 | FXE-JOINT-C0-A08 | CONTROL | PASS | sha256:3890bb78a2a28ec8d9fc23d04c1ae565ed82bef5c0f19e1cc26928cfe4f8c278 | sha256:3890bb78a2a28ec8d9fc23d04c1ae565ed82bef5c0f19e1cc26928cfe4f8c278 |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-P01 | PRECONDITION | PASS | constructed | constructed |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-P02 | PRECONDITION | PASS | completed | completed |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-P03 | PRECONDITION | PASS | authorized | authorized |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-P04 | PRECONDITION | PASS | constructed | constructed |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-P05 | PRECONDITION | PASS | ["freshness.max_age_extension_seconds"] | ["freshness.max_age_extension_seconds"] |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-A01 | CONTROL | PASS | PermissionError | PermissionError |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-A02 | CONTROL | PASS | authorization-critical inputs changed before effect | authorization-critical inputs changed before effect |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-A03 | CONTROL | PASS | [["runtime_authority_approval_mismatch"]] | [["runtime_authority_approval_mismatch"]] |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-A04 | CONTROL | PASS | false | false |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-A05 | CONTROL | PASS | ["runtime-authority-reasons/0.1"] | ["runtime-authority-reasons/0.1"] |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-A06 | CONTROL | PASS | {"new_attempts": 0, "total_attempts_after": 0} | {"new_attempts": 0, "total_attempts_after": 0} |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-A07 | CONTROL | PASS | {"dest_calls": 0, "dest_unchanged": true} | {"dest_calls": 0, "dest_unchanged": true} |
| FXE-JOINT/test_FXE_JOINT_C1 | FXE-JOINT-C1-A08 | CONTROL | PASS | {"decisions": [1, 1], "refusals": [0, 1]} | {"decisions": [1, 1], "refusals": [0, 1]} |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-P01 | PRECONDITION | PASS | {"epoch": [1, 2], "record_text_equal": true, "selection_id": ["sel-test-1", "sel-test-2"], "selection_text_equal": false} | {"epoch": [1, 2], "record_text_equal": true, "selection_id": ["sel-test-1", "sel-test-2"], "selection_text_equal": false} |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-P02 | PRECONDITION | PASS | constructed | constructed |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-P03 | PRECONDITION | PASS | completed | completed |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-P04 | PRECONDITION | PASS | authorized | authorized |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-P05 | PRECONDITION | PASS | constructed | constructed |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-P06 | PRECONDITION | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-P07 | PRECONDITION | PASS | completed | completed |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-P08 | PRECONDITION | PASS | authorized | authorized |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-A01 | CONTROL | PASS | [] | [] |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-A02 | CONTROL | PASS | [] | [] |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-A03 | CONTROL | PASS | {"attempt_status": "acknowledged", "raised": null} | {"attempt_status": "acknowledged", "raised": null} |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-A04 | CONTROL | PASS | [] | [] |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-A05 | CONTROL | PASS | 1 | 1 |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-A06 | CONTROL | PASS | bound | bound |
| FXE-JOINT/test_FXE_JOINT_C2 | FXE-JOINT-C2-A07 | CONTROL | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-P01 | PRECONDITION | PASS | constructed | constructed |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-P02 | PRECONDITION | PASS | completed | completed |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-P03 | PRECONDITION | PASS | authorized | authorized |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-P04 | PRECONDITION | PASS | constructed | constructed |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-P05 | PRECONDITION | PASS | completed | completed |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-P06 | PRECONDITION | PASS | authorized | authorized |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-A01 | CONTROL | PASS | {"actions": {"urn:cognous:action:refund-issue-routine-v1": {"class_id": "synthetic-irreversible", "irreversible": true, "max_status_age_seconds": 50, "on_unreadable": "refuse"}}, "allow_synthetic_resolver": true, "catalo | {"actions": {"urn:cognous:action:refund-issue-routine-v1": {"class_id": "synthetic-irreversible", "irreversible": true, "max_status_age_seconds": 50, "on_unreadable": "refuse"}}, "allow_synthetic_resolver": true, "catalo |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-A02 | CONTROL | PASS | {"synthetic-irreversible": 50} | {"synthetic-irreversible": 50} |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-A03 | CONTROL | PASS | ["runtime_authority.approval_commitment", "runtime_authority.catalogue_digest"] | ["runtime_authority.approval_commitment", "runtime_authority.catalogue_digest"] |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-A04 | CONTROL | PASS | ["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.effective_profile_digest", "runtime_authority.effective_configuration.members.families.0.effective_policy_digest"] | ["runtime_authority.effective_configuration.digest", "runtime_authority.effective_configuration.members.effective_profile_digest", "runtime_authority.effective_configuration.members.families.0.effective_policy_digest"] |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-A05 | CONTROL | PASS | true | true |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-A06 | CONTROL | PASS | joint | joint |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-A07 | CONTROL | PASS | PermissionError | PermissionError |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-A08 | CONTROL | PASS | [["authorization_binding_changed"]] | [["authorization_binding_changed"]] |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-A09 | CONTROL | PASS | {"new_attempts": 0, "total_attempts_after": 0} | {"new_attempts": 0, "total_attempts_after": 0} |
| FXE-JOINT/test_FXE_JOINT_C3 | FXE-JOINT-C3-A10 | CONTROL | PASS | {"dest_calls": 0, "dest_unchanged": true} | {"dest_calls": 0, "dest_unchanged": true} |
