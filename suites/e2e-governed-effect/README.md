# e2e-governed-effect (V06)

End-to-end synthetic qualification: Registry selection -> Control Plane claim -> Runtime durable selection authority -> atomic effect-time guard -> effect or refusal -> evidence.
33 predeclared cases (D dependency/missing support, A valid, B withdrawal/revocation, R race, S stale/binding, P policy narrowing, L legacy bypass, G trust/corruption/evidence).

Run: `V06_COMPONENTS_DIR=<dir with registry, control_plane, runtime, control_plane_legacy at the pins in conftest.py> python -m pytest suites/e2e-governed-effect`.
The suite FAILS (never skips) if a checkout is absent or not at its pin. Reuses the Runtime's own test fixtures by import; adds no execution path or authority source.
Limits and evidence: [results/v06-e2e/README.md](../../results/v06-e2e/README.md). Builder-authored; not independently reviewed.
