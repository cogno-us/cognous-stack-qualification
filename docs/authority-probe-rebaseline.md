# Authority probe re-baseline (F-15, r4 pin bump)

Date: 2026-10-17. Owner instruction: qualify functionality, not documentation wording. Applies from refreeze entry RF-17 and profile `process/security-runtime-f5b-20261016-r4.json` (authority `cogno-us/cognous-institutional-governance` moved from `fb3d9793` to `cbc39e79`).

## Why the probes changed

At `cbc39e79` the F-15 probe (`test_probe_er031_tier_declares_a_delay_limit`) passes, and 19 of 23 authority probes passed. The other four failed for reasons that are not F-15: they asserted document wording or an exact count rather than the guarantee they were written for. They were revised, not deleted, in `suites/v1-probes/test_authority_probes.py`. The delay-limit probe and every probe about normative content are unchanged.

## What each probe asserts now

| Probe | Before | After |
|---|---|---|
| `new_authority_checks_do_not_alter_the_archived_results` | `rac.execute()["passed"] == 44` | archived results tree digest unchanged; executed checks equal the declared fixture set; every oracle satisfied; every check recorded in the pin's own `results.json` still runs with its recorded outcome. New checks may be added. |
| `archived_results_retain_their_synthetic_and_unreviewed_scope` | README must contain "synthetic" and an independent-review phrase | each archive has `results.json` and `manifest.json`; `results.json` has `execution_status` EXECUTED_SYNTHETIC and `review_status` NOT_INDEPENDENTLY_REVIEWED; no README claims proven efficacy or field success. The READMEs became pointers to the central test hub, so their wording is documentation. |
| `profile_commits_only_add_to_the_baseline...` | no line removed anywhere since baseline `76cdff90` | no path deleted or renamed; normative files lose no line; documentation and citation metadata may be rewritten; other modified files may only be extended (a removed line must reappear with text appended); the baseline tier table keeps its original cells. |
| `constitutional_text_archives_and_pre_existing_checks_are_untouched...` | no change under a path list that included `docs/` | no baseline file under the normative path list is modified, deleted or renamed (additions allowed); draft constitution and archived result data byte-identical to baseline; baseline `tests/test_bootstrap.py` test names all still present. `docs/` and READMEs are no longer protected. |

## The re-baselined guarantee

The baseline commit stays `76cdff90`, the commit the profile README names. The protected path list is split in the test file into `NORMATIVE_IMMUTABLE` (constitution, constitutional-design, history, archived result data, battery, sources, protocol, applications, pre-existing harness scripts, the authorization/effect contract), `DOCUMENTATION_METADATA` (citation, licence, notice, READMEs, docs/) and one reviewed refactor, `tools/validate_bootstrap.py`, which `tests/test_bootstrap.py` guards.

Differences found between `76cdff90` and `cbc39e79`: documentation and citation metadata (CITATION.cff URL and licence, LICENSE rewritten as Apache-2.0, NOTICE, READMEs, docs/), run commentary moved from archived-result READMEs to the hub, the F-15 delay-limit column and section in `process/PROPORTIONAL_GOVERNANCE.md`, a new schedule-O appointment instrument and its validator check, and 33 added files. No baseline file under the normative list changed, no path was deleted or renamed, and archived result data are byte-identical.

## Limits

This changes what the probes assert, not what the authority repository does. A passing probe at `cbc39e79` is local evidence. ER-03-1 is verified only by a controller run at the r4 pins.
