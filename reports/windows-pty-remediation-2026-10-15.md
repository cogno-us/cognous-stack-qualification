# Windows PTY input remediation

The execution-runtime CI run for the cross-component test migration completed with one failed job: [Windows test shard 4](https://github.com/cogno-us/cognous-execution-runtime/actions/runs/38777398438/job/116577061507). Its two failing tests were `process send-keys encodes Enter for pty sessions` and `process submit sends Enter for pty sessions`. The shard reported 223 passing test files and 1,540 passing tests. Other jobs in that run passed or were explicitly skipped by their existing conditions.

The tests requested immediate background execution and then sent input without waiting for Node to attach its stdin listener. Background execution can return while the Windows PowerShell child is still starting. [Runtime PR #88](https://github.com/cogno-us/cognous-execution-runtime/pull/88) adds a child-generated readiness marker and waits for it before sending input. The marker is constructed from character codes so terminal command echo cannot satisfy readiness. Each action now covers immediate and delayed listener startup. Unfinished test sessions are killed during cleanup.

The repair changes component-local tests and their focused workflow. It changes no production runtime code or dependencies. Exit status and expected-output assertions remain required; neither failing test is skipped.

The focused workflow runs the input tests, PTY output test, PTY fallback test, and key-encoding tests five times on Windows Server 2025 and Ubuntu 24.04. Its results are recorded separately from the original failure. The full runtime CI matrix also runs for the repair; focused regression success does not establish full-matrix success.

[Focused repair run 38786367321](https://github.com/cogno-us/cognous-execution-runtime/actions/runs/38786367321) passed at commit `4bf25deae013c3f334b8ba6109f5be7545cc6f93`: four test files and nine tests passed in each of five repetitions on each platform (45 passing Windows executions and 45 passing Linux executions). Formatting and lint passed on both hosted platforms and locally. Workflow YAML and shell syntax checks also passed locally.

[Full repair CI](https://github.com/cogno-us/cognous-execution-runtime/actions/runs/38786366915) passed at the same tested head: 32 jobs succeeded and one existing conditional job was skipped. All seven Windows jobs passed, including test shard 4. At merge time, the PR head had 43 successful checks and one existing skip, with no failed or pending checks.

[Runtime PR #88](https://github.com/cogno-us/cognous-execution-runtime/pull/88) was merged as `cb437f86ba26248d6f5b887f4e09d00737bf4453`. The separate [main-branch full CI run](https://github.com/cogno-us/cognous-execution-runtime/actions/runs/38797355190) and [main-branch PTY regression run](https://github.com/cogno-us/cognous-execution-runtime/actions/runs/38797355117) both passed at that merge commit. Their manifests are recorded alongside the passing PR run; they do not reuse the earlier source identity.

The repository owner reported deleting the obsolete failed GitHub run after the repair merged. Its committed failure snapshots and this report preserve the observations; the original external log link may no longer resolve. The historical failure remains a failure and is not rewritten as a pass.

The committed workflow manifests preserve exact workflow heads, job conclusions, observation times, and evidence limitations. These execution results do not accept any catalog scenario, select a component profile, or authorize release or production use.
