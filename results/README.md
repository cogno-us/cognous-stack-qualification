# Qualification results

No scenario execution results have been produced in this repository. All initial scenarios are NOT RUN. Catalog validation is a structure check, not a qualification result.

A future result manifest must contain a unique run and trial ID, scenario ID/version, start and end times, exact source/configuration identities from the execution contract, commands and exit outcomes, containment/reset evidence, expected and observed state, separate integrity/business/authority verdicts, overall verdict and reason, missing visibility, artifact hashes and retrievable evidence references, evaluator identity/configuration, and residual limitations.

Use append-only run directories such as `results/<run-id>/manifest.json` for real executions. Preserve failed, inconclusive, skipped and not-applicable trials. Corrections must reference their predecessor instead of silently rewriting history. Never populate a real run with plausible placeholder observations.

Keep compact redacted manifests and reports in Git. Retain larger logs as GitHub artifacts with explicit expiry. Preserve release-accepted evidence in durable GitHub release assets or another approved controlled store, recording immutable identity and hashes; do not rely on expired Actions links. Sensitive data belongs in access-controlled storage, with redacted references here. Do not commit credentials, customer content or private methodology.

Future workflows should automate capture and publication through GitHub; no manual offline report collection is required. Such workflows are not implemented yet.
