# mvp-d2-route-b (Worker D2)

Local builder evidence for route B (AtomicLocalControlPlaneExecutor with operation identity) at the MVP tuple. It is NOT wired to
CI (no workflow, no lock, not registered) and is not a Qualification verdict.

- `test_REACHABLE_*` tests PASS when a hole exists. They document reachability, not safety; a green check is not a control and
  they must be excluded from any aggregate pass count.
- `test_approval_revocation_is_terminal_like_grant_revocation` is the terminal-revocation expectation (parity with grants). It failed at Runtime ec728da6 (revocation was reversible); the reversible-behaviour characterisation test was retired when the tuple moved to Runtime c5e97e87 (F3 PR #144). The expectation was not weakened.
- Run: `PYTHONPATH=<pydantic>=2.12 D2_CONTROL_PLANE_DIR=<cp checkout> D2_CONTROL_PLANE_PIN=<sha> D2_RUNTIME_DIR=<runtime checkout> python -m pytest suites/mvp-d2-route-b`
  Accepted pins: Runtime c5e97e87dd239c821b1b4a406a55dcd03c5bc61f; Control Plane 0a41faa972699f7ec3063967a14cd9bdd3e67d27 or
  7a4bcd40b3b49e61ff3c294dcca53b52f460b22c. Any other HEAD, a dirty checkout or pydantic < 2.12 fails every test.
- Needs `suites/operation-identity/` (imports `_oi_flow.py` and the R2 helper unmodified).
- The ODES touchpoint trace script is not in the repo (removed); its result is in the D2 report only.
