# AMEND-R1 (runner defect, logged per protocol section 5)
Defect: run_gaps.sh passed the -k expression unquoted, so pytest received "or" as a path and collected nothing ("no tests ran", exit 4). No test executed; no candidate behavior observed.
Diff: AMEND-R1.diff. Pre-amendment runner: run_gaps.pre-AMEND-R1.sh. Protocol, harness and all criteria unchanged. The failed first invocation output is retained at raw/739efe7-first-attempt/.

# AMEND-R2 (environment defect)
Defect: the Registry pin directory was first materialized with `git archive` (no .git); the harness preflight reads `git rev-parse HEAD` there and aborted every test at SETUP (48 errors, 0 tests executed; output retained at raw/739efe7-second-attempt-pin-preflight/). Fix: pin directory is now a detached git checkout at a40fe755e2384a99c37016fa9ad59396f1835900 (HEAD verified). Protocol, harness, criteria unchanged.
