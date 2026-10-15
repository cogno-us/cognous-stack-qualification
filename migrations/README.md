# Cross component relocation validation

The public migration inventories 19 repositories and relocates 135 test/harness/support files from six owners, with 48 source workflows delegated to the testing repository. File bytes, original paths/commits, executable modes, pins and license notices are retained in the [manifest](cross-component-2026-10-15.json). The [suite index](../suites/README.md) is the entry point.

Local checks passed for 914 remaining component-local tests and 122 hub subtests, 16 relocation/importer tests, 53 actual producer/consumer refusal tests and 27 OpenShell helper tests in assembled source checkouts. Both original and suite file identities are retained by the assembly tooling. These counts describe different scopes and are not combined into an overall safety score.

A broader unprepared hub probe produced 21 passes and 68 setup errors in the transported release fixture. That is a nonpassing result; the full release environment and historical matrix were not qualified in this refactor. Use the original dependency preparation in the migrated workflow. No assertion was weakened or turned into a skip to make the move pass. See [machine-readable validation](validation-2026-10-15.json).

The source-removal PRs must point to a published immutable qualification commit before adoption. Source workflows retain their original triggers and dependency pins and pass their own exact source commit. Component-local CI stays local. Required status-check names may gain reusable-workflow prefixes; branch rules must not be bypassed to accommodate that change.

Private orchestrator integration suites remain private because the public destination has no public license grant for those sources. Private methodology and doctrine were not imported. All existing selected locks, nonselected candidate states and publication/production HOLD decisions remain with their owners.
