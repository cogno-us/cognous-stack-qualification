# Custody verification (append-only addendum; the original record in this directory is unchanged)

The record in this directory (merged in cogno-us/cognous-stack-qualification#238, merge commit `0d90e355238ca28549eed443efd4242c11de7f8a`) was filed as produced. Its README predates the merge and still describes the record as "PROPOSED / open and unmerged"; that sentence described the state at filing and is superseded by this addendum for custody status only.

## Verification performed
From an independently materialized fresh clone of `https://github.com/cogno-us/cognous-stack-qualification` at `0d90e355238ca28549eed443efd4242c11de7f8a` (sparse checkout of this directory), `sha256sum -c SHA256SUMS` reported OK for `F3-qualification-evidence-ed31764.tar.gz`, `PROTOCOL-F3-v1.md`, `manifest.json` and `verdict.md`. Independent hash printout:

| File | sha256 |
|---|---|
| `PROTOCOL-F3-v1.md` | `e799b1083743526648a0c1c23d2c1455c0533ac843d88f3fe977dfd6a3850135` |
| `F3-qualification-evidence-ed31764.tar.gz` (12,816,115 bytes, 5,792 archive entries) | `1d07a70439625de3b3e85e0ea3c088a43f14bc237649487d22d85da51a174fc5` |
| `verdict.md` | `57546d2b3fd390d905a731ee7904660fa06f42128aaeae68593a0677a8342cb1` |

These equal the identities named in the Architect's directive of 2026-10-29. Byte custody in Git of the original record is therefore established at that commit.

## What this does not establish
Not a hub run, not Tier 1, not independent certification, not release or production authorization. Independence of the producing session remains not established. F3-A remains FAIL (DEV-PE-1) as originally recorded; F3-B remains the original scoped PASS. No successor qualification evidence exists in this repository.
