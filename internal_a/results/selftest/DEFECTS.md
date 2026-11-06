# Self-test findings (Worker D) - evaluator at 236cd63f

Each item has a failing test (no skips/xfails). Nothing in ia_eval/ or oracle/ was changed.

| # | Sev | Location | Minimal reproducer | Failing test |
|---|-----|----------|--------------------|--------------|
| D1 | med | ia_eval/pointer.py:25-36 (resolve) | QA-01 cp_record `/decisions/0/binding` = null. `resolve` descends into None -> MISSING, so the five binding observations (QA-01.13-16) are "unevaluable": QA-01 INCONCLUSIVE, not FAIL. An explicit wrong value is reported as missing evidence. Still non-PASS. | test_architect_list.py::test_native_binding_set_null_in_pos_is_fail |
| D2 | low | ia_eval/predicates.py:77 (op_len_eq) | QA-01 cp_record `/attempts` (or `/observations`, `/reconciliations`) = "" or {} -> `len_eq 0` holds, QA-01 PASS. Zero-length str/dict accepted as "no attempts" list. | test_est.py::test_est03_cp_empty_list_counters_of_wrong_type_never_pass[""/{}-*] (6 params) |
| D3 | low | ia_eval/freeze.py:27 + :73 (verify -> hash_scope -> list_files) ; cli.py:38 | A symlink anywhere in the package: `freeze.verify` raises ValueError instead of returning a problem. CLI `evaluate` then dies with a traceback, exit 1 (= FAIL code), not a FREEZE_DRIFT block with exit 2. | test_security_regressions.py::test_freeze_symlink_in_scope_is_reported_not_raised, ::test_cli_symlink_planted_in_package_is_a_freeze_block_not_a_crash |
| D4 | low | ia_eval/cli.py:41 | `evaluate --oracle <missing file>`: unhandled FileNotFoundError, exit 1 (= FAIL code). | test_security_regressions.py::test_cli_missing_oracle_file_is_exit_2_not_a_traceback |
| D4b | low | ia_eval/cli.py:49 | `--out` inside a directory that does not exist: report computed, then open(out,"x") raises, exit 1 (= FAIL code), nothing written. | test_security_regressions.py::test_cli_out_in_missing_directory_is_exit_2_not_a_traceback |
| D5 | low | ia_eval/predicates.py:7 (_SHA) | `$` also matches before a trailing newline: op_sha256_format("sha256:" + "a"*64 + "\n") is True (QA-01.9 / QA-02.9 effect_id). Use `\Z` or fullmatch. | test_security_regressions.py::test_sha256_format_rejects_trailing_characters[\n] |

## Notes that are not defects (design, recorded so nobody is surprised)
- OBS deviation => overall FAIL but claim_basis PASS (OBS is claim_gated False). Tested as by-design in test_est.py::test_est11_claim_basis_identical_whether_obs_pass_or_not_run.
- Pairing: QA-03/QA-05/QA-27 are paired with QA-02, the other RI cases with QA-01 (oracle). Breaking QA-01 does NOT downgrade QA-03/05; breaking QA-02 does. Tests assert the oracle's pairing.
- Control not executed => dependents INCONCLUSIVE => overall INCONCLUSIVE (INCONCLUSIVE outranks NOT RUN).
- Malformed oracle pointer (no leading "/") is not caught by O.validate; the engine fails closed as INCONCLUSIVE EVALUATOR_ERROR (test_malformed_oracle_pointer_fails_closed).
- freeze skips top-level `results/` and any `__pycache__`/`.pytest_cache` directory (only *.pyc is flagged). Test pins the `results/` exemption.
- Equivalent mutants (not observable through the engine): M09 zero-executed rule (combine already yields NOT RUN), M22 raw size cap in _Raw._load (load_json_strict repeats it), M37 combine([]) PASS (engine never passes empty), G7 effect-name regex (allow-list already refuses; regex unit-tested directly).

## Possibly vacuous / weak oracle observations (cannot fail on a hostile but self-consistent driver)
- QA-01.9 / QA-02.9 effect_id: format-only (sha256_format), any well-formed string passes.
- All `returned` observations (QA-11.1, QA-17.1, QA-26.1, QA-26.2): satisfied by any hash-verified JSON raw, content unchecked.
- QA-09.1 / QA-09.2: both sides of the relation are driver-supplied fields (`raw_commitment` is not recomputed by the evaluator).
- QA-S1/S2/S3/E1: compare driver-reported identities to pinned literals; the evaluator does not recompute them (identity.hash_files is not on the evaluate path). Known residual trust.
- QA-26.3 / relation obs: two boundaries may alias the same raw file (determinism trivially true); not detectable by hash.
