Hosted runs of .github/workflows/rw01-f4-poc-e2e.yml (pull_request events), PR #263:
- head 9982550651433fa4c04660897cd77e9804dd8ecd: https://github.com/cogno-us/cognous-stack-qualification/actions/runs/41487747002  conclusion: success
- head 69ab92543a0fe9517b15ca43c2b0d26ac8b1f0eb: https://github.com/cogno-us/cognous-stack-qualification/actions/runs/41488982317  conclusion: success
  (69ab9254 differs from 9982550 only by evidence/ci files; the raw output of the first run is in the PR comments, see COMMENTS.sha256)
The run on the documentation-only head after that is recorded in a PR comment.
Hosted: battery 115 collected / 114 passed / 1 failed (F-1, intentional); registry_pr 533/533; replay_pr 730/730; cp_pr 83/83; cp_repinned_6f600ab1 385/385; cp_repinned_v8 305/305.
INTEGRATED CLAIM NOT ESTABLISHED: the check is green by design; F-1 is an intentional documented FAIL (a real GovernedAgeWorkflow record is refused by every Replay profile, 'resolution journal missing', pre-existing at base).

SUPERSESSION NOTE (F-1 recovery; the lines above are the historical record of those hosted runs and are kept unchanged):
The intentional F-1 FAIL and the banner "INTEGRATED CLAIM NOT ESTABLISHED / green by design" describe those earlier runs only. After the F-1 recovery the battery pins Replay ca94d6a8 and
Control Plane cf7f5268, the F-1 FAIL row is replaced by the passing integration rows F1-A..F1-G, and the workflow fails on ANY failed test or non-PASS required row.
The banner OPERATIONAL TRUST NOT ESTABLISHED / PRODUCTION ADOPTION NOT AUTHORIZED stands. No hosted run of the new head is recorded here.

SUPERSESSION NOTE 2 (closeout re-pin, 2026-11-02): PRs #86/#102/#84 are now merged (squash). The battery pins Registry 7de0ec9f8471c7a2ff630eb4035fa24d60b5e2eb, Control Plane 8b97d32ff9a5aee640e61704637ff60dc57a84d9 and Replay 6651abef2dfc0960b09907ed268db45e809ee814; their trees are IDENTICAL to the former PR heads (52ff5f7d / cf7f5268 / ca94d6a8), so the pins named above are superseded by identity of merged commit only. The lines above are unchanged history. No hosted run of the re-pinned head is recorded here.
