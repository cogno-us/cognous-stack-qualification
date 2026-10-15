# Windows PTY input remediation

The execution-runtime CI run for the cross-component test migration completed with one failed job: [Windows test shard 4](https://github.com/cogno-us/cognous-execution-runtime/actions/runs/38777398438/job/116577061507). Its two failing tests were `process send-keys encodes Enter for pty sessions` and `process submit sends Enter for pty sessions`. The shard reported 223 passing test files and 1,540 passing tests. Other jobs in that run passed or were explicitly skipped by their existing conditions.

The tests requested immediate background execution and then sent input without waiting for Node to attach its stdin listener. Background execution can return while the Windows PowerShell child is still starting. [Runtime PR #88](https://github.com/cogno-us/cognous-execution-runtime/pull/88) adds a child-generated readiness marker and waits for it before sending input. The marker is constructed from character codes so terminal command echo cannot satisfy readiness. Each action now covers immediate and delayed listener startup. Unfinished test sessions are killed during cleanup.

The repair changes component-local tests and their focused workflow. It changes no production runtime code or dependencies. Exit status and expected-output assertions remain required; neither failing test is skipped.

The focused workflow runs the input tests, PTY output test, PTY fallback test, and key-encoding tests five times on Windows Server 2025 and Ubuntu 24.04. Its results are recorded separately from the original failure. The full runtime CI matrix also runs for the repair; focused regression success does not establish full-matrix success.

[Focused repair run 38786367321](https://github.com/cogno-us/cognous-execution-runtime/actions/runs/38786367321) passed at commit `4bf25deae013c3f334b8ba6109f5be7545cc6f93`: four test files and nine tests passed in each of five repetitions on each platform (45 passing Windows executions and 45 passing Linux executions). Formatting and lint passed on both hosted platforms and locally. Workflow YAML and shell syntax checks also passed locally.

[Full repair CI](https://github.com/cogno-us/cognous-execution-runtime/actions/runs/38786366915) remains separate evidence; PR #88 is open pending its broader checks at this checkpoint. Follow its live status rather than inferring completion from the focused result.

The committed workflow manifests preserve exact workflow heads, job conclusions, observation times, and evidence limitations. These execution results do not accept any catalog scenario, select a component profile, or authorize release or production use.
