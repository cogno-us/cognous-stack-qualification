# Release gate environment builder

`tools/rc_env.py` rebuilds, on a local Linux machine, the pinned producer environment that the delegated workflows build in CI. It exists because the suites installed into component trees (see [`suites/README.md`](../../suites/README.md)) skip or fail unless pinned producer checkouts, extra packages and a set of environment variables are present, and until now that recipe lived only in workflow YAML ([blockers B-03 and B-08 of the inventory](../test-inventory.md)).

Scope: bounded synthetic profile only, Linux only. The tool prepares inputs and verifies them; it runs no gate, selects no revision and decides nothing about which skips the gate allows. Candidate and release status are untouched.

## Where the pins come from

Nowhere but the workflow files. The tool reads `.github/workflows/<name>.yml` and takes from it: each `actions/checkout` (repository, exact commit, target directory), each `pip install` line (including `-r` lock files and `--require-hashes`), the `install_suite.py` overlay step, and the `env:` block of each test step. It carries no commit id, repository list or variable value of its own (a unit test enforces that), so when a workflow pin moves, `prepare` follows it and `check` reports a prepared directory that is now behind it.

A recipe is `WORKFLOW` or `WORKFLOW:JOB`. Default recipes (names only, in `DEFAULT_RECIPES`):

| Recipe | Gives the tests of |
|---|---|
| `cognous-replay-bundle--tests` | Replay bundle with its pinned and accepted producers (control plane, runtime, manifest) |
| `cognous-governance-evidence-pack--tests` | Evidence pack: five stages, four environments (the workflow swaps the installed Replay and ODES between stages) |
| `cognous-governed-exchange--tests` | Governed exchange with control plane, runtime, Replay, ODES, evidence pack |
| `open-decision-evidence-standard--tests` | ODES with the accepted Replay and producers |
| `cognous-execution-runtime--python-safety`, `--worker21-authority-effect`, `--durable-refusal` | Runtime overlay suites; each workflow pins a different control plane |
| the two pilot workflows, job `offline-controls` (`*-agent-pilot:offline-controls`) | Qualification tooling environment from the hashed serial lock, and `NATIVE_HUB_ROOT` for `tests/native` |

## Use

```
python tools/rc_env.py plan                                       # offline: the recipes as read from the workflows
python tools/rc_env.py prepare --work /path/to/work [--recipe R]  # clone, overlay, venvs (default: all default recipes)
python tools/rc_env.py env   --work /path/to/work --recipe R [--stage S] [--json]
python tools/rc_env.py check --work /path/to/work [--recipe R]    # exit 1 on any mismatch
```

`prepare` creates, per recipe, `WORK/<recipe>/ws` (stands in for the Actions workspace), `WORK/<recipe>/venvs/<key>` and `WORK/<recipe>/rc-env.json` (pins, tree ids, overlay hashes, `pip freeze` of each venv, resolved variables). Each repository is fetched alone, with `git init` and `git fetch --depth 1 origin <sha>` (`--full-history` drops the depth limit; inventory blocker B-10 lists tests that need history), then verified against the pin. Network use is the git host and the Python package index only. A directory that exists is refused unless `--force`.

`env` prints `export` lines for one test stage (default: the first; `--stage` takes a name that the first line lists) and a comment with the directory and command the workflow runs there:

```
eval "$(python tools/rc_env.py env --work W --recipe cognous-governed-exchange--tests --stage run_tests | grep -v '^#')"
cd <the directory named in the comment> && pytest -q tests
```

Every relative path in a variable becomes absolute. `PYTHONDONTWRITEBYTECODE=1` is added when the workflow does not set it, because several pinned repositories track bytecode and package metadata and a test run would otherwise modify the pinned tree; it is not a pin.

`check` compares what is on disk with the pins, and reports, per line, `ok` or `MISMATCH`: the workflow file hash and each pin as the workflow states it now against the prepared one; each checkout's head; tracked files that differ from the state recorded at the end of `prepare` (overlay and install side effects are recorded, anything later is reported); overlay file hashes; each venv's `pip freeze`; editable installs that point outside the checkouts; that every path variable exists; and that the workflow's own `test "$(git -C X rev-parse HEAD)" = "sha"` lines agree with its checkout pins.

`--source-rev RECIPE=SHA` replaces the owning-source commit of one recipe (the workflow's `source_revision` input): the delegated workflows are called by component CI with the component's own head, and the default here is the workflow's recorded baseline.

## Limits

- Third-party packages that a workflow installs without a pin or lock resolve from the package index on the day of `prepare`. Their versions are recorded and `check` reports a change; a lock is only as strong as the workflow's own.
- The interpreter is the version the workflow names (`python3.12` when present, otherwise the running interpreter, with a warning in the manifest). The newest entry of a matrix is prepared.
- Steps that are not environment (uploads, example generators, command-line smoke checks) are listed under `unmodelled` in the plan and never run. A step whose condition is not a simple matrix test is listed under `skipped_steps`. A variable that refers to a secret is dropped and listed.
- `_qualification` in a workspace is a link to this repository, so the overlay is the one in the checkout that runs the tool, not the workflow's `qualification_revision`.
- Not covered: suites that need a container runtime, a live gateway, Node or a Rust toolchain; the delegated hub workflows; the controller (`tools/v1_validation.py`).
- Skips that remain after the environment is complete are skips of the suites themselves (declared marks, data-driven or in-body); they stay a matter for the inventory.

## Measured effect

Measured on 19 October 2026, Python 3.12.3, Linux, with each owning source at its main head (Replay `f65547dd`, evidence pack `4288054e`, exchange `78331c65`, ODES `a79af163`, runtime `0987ad40`, set with `--source-rev`) and the overlay of this repository at `f71fa08`. "Before" is a fresh environment with only the plain install the workflow starts from (the `dev` extra; for the runtime, `pytest` and `pydantic`), no variables and no pinned producers, running the same commands as the workflow (`--continue-on-collection-errors` so that one unimportable module does not hide the rest). "After" is `prepare` followed by the variables of `env` for each stage. A test is counted once per suite (the best outcome over the stages of the recipe). Nothing was changed in the suites.

| Suite | Tests | Before: pass / skip / fail or error | After: pass / skip / fail or error | Tests that moved from skip, fail or error to pass |
|---|---:|---|---|---:|
| Runtime overlay (three recipes) | 807 | 673 / 127 / 7 | 770 / 37 / 0 | 97 |
| Replay overlay | 1,105 | 996 / 109 / 0 | 1,073 / 32 / 0 | 77 |
| Evidence pack overlay (five stages) | 447 before, 481 after | 312 / 91 / 44 | 449 / 32 / 0 | 102 |
| Exchange overlay | 333 | 260 / 3 / 70 | 333 / 0 / 0 | 73 |
| ODES | 3,175 before, 3,187 after | 3,063 / 109 / 3 | 3,186 / 1 / 0 | 110 |
| Total | | 439 skips, 124 failures or errors | 102 skips, 0 failures or errors | 459 |

(The counts differ before and after for the evidence pack and ODES because a module that cannot be imported without the pinned producers is not collected.) `tests/native` of this repository: without `NATIVE_HUB_ROOT` collection stops with a `KeyError` on main (1 collected, 1 error); with the variable from `env` for a pilot recipe, 6 tests are collected and pass.

What is left after the environment is complete (102 skips), by reason:

- Runtime, 37: 33 need a control plane that carries the local authority effect contract (the recipe of another workflow supplies it, for a different set of test files); 2 need a live gateway and a worker image; 2 are collection skips.
- Replay, 32: 18 ask for refusal-profile inputs that no workflow supplies; 12 are data-driven in-body skips of the suite; 1 is a strict expected failure; 1 is the Replay-to-pack pairing test (the pack is not installed in this recipe, B-05).
- Evidence pack, 32: 28 need an installed Replay that lists the programme-2 generation, which no stage of its workflow installs for the full suite; 2 are collection skips; 2 import a module that the pinned control plane or Replay of that stage does not have.
- ODES, 1: needs `rfc8785`, which no workflow installs.

Those are inventory matters (B-03, B-05, B-07 and B-08 of [the inventory](../test-inventory.md)); this tool does not add packages or variables that a workflow does not carry.
