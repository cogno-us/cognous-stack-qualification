# Licensing and third-party notices

The repository is a collection with explicitly scoped licenses. The root Apache-2.0 license does not replace third-party terms.

| Material | Terms and provenance |
|---|---|
| Original tooling, workflow and original documentation | Apache-2.0 under the root LICENSE |
| 40 Cognous scenario adaptations in `scenarios/catalog.json` and `scenarios/README.md` | Apache-2.0; derived from user-supplied engineering documents under the user's explicit publication instruction; see `sources/documents.json` for source-document terms and limits |
| Bounded-comparison process adaptation in `process/testing/` | Apache-2.0; user-authorized adaptation of source C in `sources/documents.json`; original DOCX, correspondence, synthetic bundle and external methodology source are not redistributed or relicensed |
| Content and adaptations in `scenarios/ai-security-wiki/` | CC BY-SA 4.0, with nested LICENSE; source author and per-page credits retained |
| Wiki-derived title lists and provenance metadata in `sources/ai-security-wiki.lock.json` | CC BY-SA 4.0 for material derived from the Wiki; the record identifies its source and license |

## AI Security Wiki

Source: [nachi065/AI-Security-Wiki](https://github.com/nachi065/AI-Security-Wiki). Original author: **Nachiket Sathaye**. Contributor credited by the upstream README: **Ankush Jain**. Per-page author/coauthor fields are retained in imported pages, catalog entries and the lock. No endorsement of Cognous is implied.

License: [Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/); the complete license is retained at `scenarios/ai-security-wiki/LICENSE`. Exact source commit, original paths and original/redistributed hashes are in the lock. Each case links to its source at that commit.

Changes: extracted case metadata into JSON and an index; added attribution, applicability and NOT RUN status; resolved relative Markdown links to pinned source URLs. Original test text, thresholds, mappings, safety notes and prior modification notices remain in the pages. Wiki-derived adaptations remain under CC BY-SA 4.0 and must retain attribution, change notices and the license. A future executable test adapted from Wiki expression requires the same license review; directory placement alone cannot change its obligations.

The live README and LICENSE at the pinned revision use CC BY-SA 4.0. Earlier versions used CC BY 4.0; that historical fact is not a basis to relicense the imported current revision. Changed license terms or removed author credits block automated refresh.

References to OWASP, MITRE, NIST, laws or other third-party works are upstream references, not an assertion that those works are covered by the Wiki license or current/accurate. Do not import linked payloads, tools or external documents without checking their own terms. This import does not provide legal or compliance clearance.

## Relocated Cognous integration suites

The files under `suites/` retain their original source commits, paths, byte commitments and license notices in `migrations/cross-component-2026-10-15.json`. The hub, Replay, Evidence Pack, ODES, Governed Exchange and evidence registry source repositories use Apache-2.0 for the imported material. The executor’s corresponding Python safety tests use its Apache-2.0 grant; `tools/openappa/` uses the retained source MIT default where no narrower grant was identified. Its original MIT LICENSE, Apache license and NOTICE are preserved together. No retained upstream Moltbot application code is imported.

The initial move is byte-preserving. Workflow adaptations add explicit source/suite checkouts and source-identity artifacts, while retaining source pins and assertions; original workflow bytes remain in each suite. This does not relicense dependencies fetched at test time. OpenAPPA, OpenShell and any other external checkout retain their own terms; the migration does not copy those repositories into this one. Private source content is excluded.
