# Negative matrix (tested head ecee20fb)

Letter rows A-S and G2 must be REFUSED_AS_EXPECTED; `*-limit` rows are documented non-refusals (NOT_APPLICABLE), asserted but not claimed as refusals.

| Row | Label | Expected code | Observed code | Verifier calls |
|---|---|---|---|---|
| A | passed | registry_evidence_unverified:signature_invalid | registry_evidence_unverified:signature_invalid | 1 |
| B | passed | registry_evidence_scope_mismatch | registry_evidence_scope_mismatch | 1 |
| C | passed | registry_evidence_scope_mismatch | registry_evidence_scope_mismatch | 1 |
| D | passed | registry_evidence_scope_mismatch | registry_evidence_scope_mismatch | 0 |
| E | passed | registry_evidence_unverified:selection_expired | registry_evidence_unverified:selection_expired | 1 |
| F | passed | registry_evidence_unverified:issuer_key_revoked | registry_evidence_unverified:issuer_key_revoked | 1 |
| G | passed | registry_evidence_unverified:selection_epoch_stale | registry_evidence_unverified:selection_epoch_stale | 1 |
| H | passed | registry_evidence_effective_digest_mismatch | registry_evidence_effective_digest_mismatch | 0 |
| I | passed | registry_evidence_effective_digest_mismatch | registry_evidence_effective_digest_mismatch | 1 |
| I | passed | registry_evidence_effective_digest_mismatch | registry_evidence_effective_digest_mismatch | 1 |
| I | passed | registry_evidence_effective_digest_mismatch | registry_evidence_effective_digest_mismatch | 1 |
| J | passed | registry_evidence_unverified:record_digest_mismatch | registry_evidence_unverified:record_digest_mismatch | 1 |
| J-limit | skipped | None | None | None |
| K | passed | registry_evidence_unverified:record_digest_mismatch | registry_evidence_unverified:record_digest_mismatch | 1 |
| L | passed | registry_evidence_trust_malformed | registry_evidence_trust_malformed | 0 |
| L-limit | skipped | None | None | None |
| M | passed | registry_evidence_input_echo_mismatch | registry_evidence_input_echo_mismatch | 1 |
| N | passed | registry_evidence_verdict_malformed | registry_evidence_verdict_malformed | 1 |
| O | passed | registry_evidence_input_echo_mismatch | registry_evidence_input_echo_mismatch | 1 |
| O-limit | skipped | None | None | None |
| P | passed | selection_evidence_missing | selection_evidence_missing | 0 |
| Q | passed | registry_evidence_unsupported_profile | registry_evidence_unsupported_profile | 0 |
| R | passed | registry_evidence_family_set_mismatch | registry_evidence_family_set_mismatch | 0 |
| S | passed | registry_evidence_unverified:json_duplicate_key | registry_evidence_unverified:json_duplicate_key | 2 |
| S-limit | skipped | None | None | None |
| G2 | passed | registry_evidence_unverified:record_digest_mismatch | registry_evidence_unverified:record_digest_mismatch | 1 |
