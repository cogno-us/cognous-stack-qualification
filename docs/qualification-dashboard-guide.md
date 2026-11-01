# Qualification dashboard operations

[Browse the GitHub dashboard](qualification-dashboard.md). It separates proposed scenario-to-test associations from actual GitHub-reported workflow outcomes. The 40 Cognous catalog cases remain NOT RUN; 33 have supporting test references, including the deferred H01 reference. None has complete accepted coverage. Wiki specifications remain separately attributed, NOT RUN and applicability-unassessed.

## Maintain everything through GitHub

1. Edit scenarios or `scenarios/coverage-map.json` in a pull request. Each mapping pins the scenario bytes/version, actual test symbols and file hashes, a suite commit, original source provenance, license and unresolved gaps. Changing a requirement or mapped test invalidates the mapping until explicitly reviewed and updated.
2. Use **Actions → Capture qualification run metadata → Run workflow**. Choose one inventoried public repository and enter its GitHub Actions run ID. This reads metadata only: it does not execute code from that run or download raw logs/artifact bytes.
3. The workflow captures the specified attempt, validates metadata, adds a content-addressed snapshot and regenerates the Markdown dashboard in a results PR. Review and merge that PR. It does not change catalog verdicts or automatically adopt component versions. The repository must permit GitHub Actions to create pull requests; if organization policy blocks it, the validated capture bundle is still retained as an artifact and the PR step reports failure.
4. The Dashboard build workflow checks the catalog, coverage commitments and result snapshots and builds a searchable static HTML artifact. The generated Markdown view remains directly browsable in GitHub.

There is no background polling of component repositories in this change. A capture is an explicitly initiated GitHub workflow. Existing weekly Wiki refresh behavior remains separate. Running or capturing a workflow does not make its review independent.

## Hosting the interactive view

The optional Publish qualification dashboard workflow builds the same data and deploys it through official GitHub Pages actions. An administrator must first enable **Settings → Pages → Build and deployment → Source: GitHub Actions**, then run that workflow. No PAT is committed or requested by this project. Repository administration is not exposed by the connected GitHub tools used for this change, so Pages activation is not claimed. The GitHub Markdown dashboard requires no hosting setup.

## Manifest contract

[Schema](../schemas/run-manifest-v1.schema.json) · [Validator and normalization](../tools/qualification_results.py)

Version 1 is execution telemetry. It records the provider-reported workflow head SHA (or the exact disposable command checkout SHA), exposed suite SHAs, observation time, execution outcome, jobs and declared/unknown environment and profile information. It preserves evidence links, provider-reported hashes, expiry and limitations. Null expected/observed destination state and NOT ASSESSED integrity/business/authority dimensions are intentional when no authoritative oracle was captured. The loaded component set remains UNVERIFIED. A passing workflow, skipped job or green JUnit file does not fill those gaps.

`scenario_results` must be empty in v1. A future versioned evaluator must establish per-case execution, pinned loaded components, containment/reset, expected/observed destination state and the three verdict dimensions before this repository can accept scenario verdicts. Imported metadata cannot authorize a release or production deployment.

Pending runs retain RUNNING outcomes. Completed GitHub conclusions map success to PASS, failure/timeouts to FAIL, cancellation to CANCELLED, and skipped/neutral/unknown conclusions to INCONCLUSIVE. Those labels apply only to execution. GitHub's updated timestamp is retained as last_updated_at, not misrepresented as a run completion time.

## Immutable history and retention

Each normalized snapshot lives at `results/workflows/<run-id>/<sha256-of-json>.json`. Recapturing a run appends a new snapshot; it never overwrites a failed or incomplete predecessor. The dashboard displays the latest observed snapshot per run/attempt; all prior snapshots remain in Git and in the static data download. Different attempts are distinct records, not silently combined trials.

A committed manifest is durable metadata. A SHA or URL does not preserve artifact bytes, prove their meaning or establish independence. Actions artifacts expire. Before relying on release evidence, preserve a screened artifact durably in an approved store or GitHub release asset, verify its bytes and record the durable URL and hash. No release asset is created automatically here, and no raw logs or customer/private content are imported.

## Disposable command runs

`tools/run_suite.py` retains the existing explicit-command interface and now writes `manifest.json` alongside source-identity.json, execution.log and command-result.json. It records timeout, spawn/setup errors, exact source/suite identities and declared profile information without adopting scenario verdicts. A failure before exact source identity is available produces setup-error.json instead of inventing a valid manifest. Local output references are marked LOCAL_ONLY until a real artifact publisher supplies durable references.

```bash
python tools/run_suite.py --suite cognous-open-control-stack \
  --source-root /path/to/cognous-open-control-stack \
  --results-dir /tmp/cognous-test-run \
  -- python -m unittest discover -s tests -p test_full_candidate_gate.py -v
```

A declared profile supplied with `--profile` is hashed and retained as declared input. It does not certify that every dependency loaded at those revisions. Actual component integrations still require the original suite's pinned dependency preparation.

## Initial captured population

The initial nine records are real GitHub run metadata from the migration's tested heads: seven completed successful workflows, one retained full-reference diagnostic failure and one in-progress runtime application CI run at capture time. They are examples of actual execution telemetry, not synthetic dashboard demonstrations and not evidence that the 40 catalog cases have been accepted. Later captures may show changed status for the same run while preserving these snapshots.

The subsequent dashboard snapshot adds the passing Nonselected reference compatibility run from qualification PR #4 and a later observation of the same runtime CI attempt. The dashboard therefore currently displays ten distinct runs and retains eleven immutable snapshots. The older failing diagnostic remains a failure for its original workflow head; the newer repair result does not rewrite it.
