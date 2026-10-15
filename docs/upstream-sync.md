# Linking Wiki updates to qualification scenarios

A fork or submodule alone does not adapt updated tests, preserve verdicts or rerun qualification. This repository uses an exact source lock and a reproducible importer. The lock records the commit, license hash, attribution, source file hashes, redistributed hashes and case IDs.

## Available now

From **Actions → Upstream Wiki refresh → Run workflow**, a maintainer can fetch current upstream main, run only this repository's importer, validate regenerated files and create a review PR. No offline file editing is required. The importer reads Markdown as data and does not execute upstream code or attack payloads. This workflow does not execute tests against Cognous, merge the PR, change component selection or rewrite earlier results.

A license change, missing authors, removal of previously credited page authors or removed case IDs stops the refresh for explicit review. New IDs and changed procedures appear as a normal diff. A merge is the adoption decision. Past results remain bound to their previous source commits and scenario bytes; an updated specification needs fresh execution evidence.

The job needs Actions enabled and GitHub's repository setting **Allow GitHub Actions to create and approve pull requests** enabled for automatic PR creation (the workflow creates PRs; it never approves them). Branch protection remains applicable. If the organization disables that setting, GitHub will reject PR creation; maintainers must enable the supported setting or use a separately approved GitHub App. No personal access token is required by this implementation. An update PR created with GITHUB_TOKEN may not trigger other workflows automatically; this job runs the checks itself and records that limitation in its PR body. If protected checks require a separate PR event, use a GitHub App token or maintainer-initiated dispatch.

## Weekly automatic polling

Weekly polling is enabled for **Mondays at 14:17 UTC** in `.github/workflows/upstream-wiki-refresh.yml`. Each run checks upstream main and proposes a review PR when the pinned content changes. Manual dispatch remains available. License changes, attribution removal and case retirement still require explicit review.

GitHub schedules run in UTC, can be delayed and may be disabled for inactive public repositories. For event-driven updates without polling, the upstream maintainer would need to send an authenticated `repository_dispatch` (or use a separately installed GitHub App) when their default branch changes. That requires cooperation or installation; this repository alone cannot subscribe its Actions workflow directly to every upstream push.

Automatic refresh should mean **proposed changes in a review PR**, with exact provenance and license checks. Keep accepted cases and past qualification evidence pinned until review. Do not auto-merge upstream text or run new payloads unattended.

## Maintainer reproduction

The GitHub workflow performs the equivalent of:

```bash
git clone --depth 1 https://github.com/nachi065/AI-Security-Wiki.git /tmp/ai-security-wiki
python3 tools/sync_ai_security_wiki.py --source-dir /tmp/ai-security-wiki --accept-revision
python3 tools/validate_catalog.py
python3 -m unittest discover -s tests -v
```

For reproduction at the existing lock, check out its exact commit in the upstream checkout and use `--check` instead of `--accept-revision`. Do not modify generated imported pages directly; maintain source mappings or importer changes in a reviewed PR. Changes to the license digest require an actual rights review, not an automatic hash update.
