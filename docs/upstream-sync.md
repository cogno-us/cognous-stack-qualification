# Linking Wiki updates to qualification scenarios

A fork or submodule alone does not adapt updated tests, preserve verdicts or rerun qualification. This repository uses an exact source lock and a reproducible importer. The lock records the commit, license hash, attribution, source file hashes, redistributed hashes and case IDs.

## Available now

From **Actions → Upstream Wiki refresh → Run workflow**, a maintainer can fetch current upstream main, run only this repository's importer, validate regenerated files and open a pull request with the generated update for maintainer review. The workflow never merges it. No offline file editing is required. The importer reads Markdown as data and does not execute upstream code or attack payloads. The weekly workflow follows the same process. It does not execute qualification scenarios, change component selection or rewrite earlier results.

A license change, missing authors, removal of previously credited page authors or removed case IDs stops the refresh for explicit review. New IDs and changed procedures appear in the generated diff for the reviewer. Past results remain bound to their previous source commits and scenario bytes; an updated specification needs fresh execution evidence.

The job needs Actions enabled and GitHub's repository setting **Allow GitHub Actions to create and approve pull requests** enabled for automatic PR creation (the workflow creates PRs; it never approves them). Branch protection remains applicable. If the organization disables that setting, GitHub will reject PR creation; maintainers must enable the supported setting or use a separately approved GitHub App. No personal access token is required by this implementation. An update PR created with GITHUB_TOKEN may not trigger other workflows automatically; this job runs the checks itself and records that limitation in its PR body. If protected checks require a separate PR event, use a GitHub App token or maintainer-initiated dispatch.

## Weekly automatic polling

Weekly polling is enabled for **Mondays at 14:17 UTC** in `.github/workflows/upstream-wiki-refresh.yml`. Each run checks upstream main and, when validation succeeds and the generated files differ, opens a refresh PR for maintainer review. The workflow never merges it. Manual dispatch remains available. License changes, attribution removal and case retirement still require explicit review.

GitHub schedules run in UTC, can be delayed and may be disabled for inactive public repositories. For event-driven updates without polling, the upstream maintainer would need to send an authenticated `repository_dispatch` (or use a separately installed GitHub App) when their default branch changes. That requires cooperation or installation; this repository alone cannot subscribe its Actions workflow directly to every upstream push.

## Pull request boundary

The refresh validates and opens a PR for maintainer review; it never merges. Only generated files under `scenarios/ai-security-wiki/` and `sources/ai-security-wiki.lock.json` are staged, and the workflow refuses to publish a change to any other path. It validates provenance, license and attribution retention and the importer's rejection behaviour first, pushes a branch named after the upstream commit and opens the PR. The PR body states that it is not merged automatically. A maintainer reviews the generated diff and merges it under the repository's branch rules; the workflow requests no merge, no auto-merge and no approval. The workflow's own change history shows that an earlier version merged the generated PR itself; that behaviour was removed on 2026-10-18 (see the [16 October note](security-residuals-20261016.md), update of 2026-10-18).

Old results retain their original source identities. Imported text remains reference specifications with NOT RUN status; merging a specification does not qualify Cognous or run upstream attack payloads. Applicability to the stack's declared scope is recorded in `scenarios/ai-security-wiki/applicability.json` for the current snapshot (20 APPLICABLE, 45 PARTLY_COVERED, 591 NOT_APPLICABLE); a case that appears in a later refresh has no classification until a maintainer assesses it.

## Maintainer reproduction

The GitHub workflow performs the equivalent of:

```bash
git clone --depth 1 https://github.com/nachi065/AI-Security-Wiki.git /tmp/ai-security-wiki
python3 tools/sync_ai_security_wiki.py --source-dir /tmp/ai-security-wiki --accept-revision
python3 tools/validate_catalog.py
python3 -m unittest discover -s tests -v
```

For reproduction at the existing lock, check out its exact commit in the upstream checkout and use `--check` instead of `--accept-revision`. Do not modify generated imported pages directly; maintain source mappings or importer changes in a reviewed PR. Changes to the license digest require an actual rights review, not an automatic hash update.
