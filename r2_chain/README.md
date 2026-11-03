# R2 joined chain: Control Plane -> OCS Registry F4 -> retained record -> Replay F4

**PRIVATE PREVIEW QUALIFICATION TUPLE** (preview-only; not canonical; `component-lock.json` is untouched).

> **SINGLE SYNTHETIC TENANT.** The private preview is limited to one synthetic tenant with no shared multi-tenant evidence resolver; no tenant-isolation or cross-tenant authorization assurance is claimed.
>
> Synthetic data and synthetic Ed25519 keys only. Claim A only. No production claim of any kind.

Register: [#259](https://github.com/cogno-us/cognous-open-control-stack/issues/259). R1 Final Closeout: <https://github.com/cogno-us/cognous-open-control-stack/issues/259#issuecomment-6609667524>.

## Run it

From a clean checkout of this repository:

```
bash r2_chain/participant_run.sh [out_dir]
```

The default `out_dir` is `${TMPDIR:-/tmp}/r2-joined-chain-evidence`. The script creates a temporary virtualenv, installs `r2_chain/requirements.lock` with `pip --require-hashes`, runs `r2_chain/fetch_sources.sh` (exact SHAs, HEAD and tree verified), sets `SRC_DIR` and `PYTHONDONTWRITEBYTECODE=1`, runs `r2_chain/run_chain.py --src-dir ... --out ...`, prints counts of PASS, REFUSED_AS_EXPECTED, NOT_APPLICABLE, NOT_RUN and FAIL, and exits nonzero on any failure.

Requirements: bash, git, python3 (3.11 or newer; CI uses 3.13) with `venv`.
**Network access is required** to install the pinned packages from PyPI and to fetch the pinned sources from public GitHub. Nothing else is contacted; the tests themselves use no network. No secrets, credentials, paid APIs or production services.

## The tuple

| Source | Revision (exact SHA; tree also verified) | Role |
|---|---|---|
| Control Plane (`cognous-control-plane`) | `46372de34ef1ce882cff1aa9664c38a98afb2a3b` | final R1 state; governed decision and retained bounded record |
| OCS Registry (`cognous-ocs-registry`) | `7de0ec9f8471c7a2ff630eb4035fa24d60b5e2eb` | F4 signed selection evidence and the injected verifier |
| Replay (`cognous-replay-bundle`) | `6651abef2dfc0960b09907ed268db45e809ee814` | F4 re-admission of the retained record |
| Qualification (this repository) | the checkout under test (recorded at run time) | tuple assembly, wiring, assertions, evidence |

Trees and interfaces are in `sources.json`. Revisions are fetched by SHA, never by branch or tag.

## What the joined chain proves

For the synthetic refund-age workflow, within this tuple:

- A. the Control Plane consumed the intended F4 selection evidence;
- B. the retained bounded record contains the exact selection evidence required for Replay;
- C. Replay passed the original carried selection text / record text through the injected Registry verifier;
- D. Replay bound the verifier verdict to the exact retained record;
- E. the expected positive path is admitted;
- F. the defined negative cases (A-S, plus one persistence/reload negative G2) are refused and produce no admission marker. Almost all refusals carry an exact typed code that the tests assert; a few sub-cases in rows L, Q and S are refused by Replay's untyped guard (code `None`) and are asserted by message text.

## What it does NOT prove

- Replay independently authenticating the entire Control Plane decision (claim B is not asserted).
- Registry-origin institutional authority.
- Production readiness, operational trust, or production key custody (keys are synthetic).
- Multi-tenant isolation (see the constraint above).
- Q7, canonical adoption, G3, H3 or G4.
- Anything about AGT, Evidence Registry / BitRep, Exchange, Verifier, Ergonomics or Execution Runtime: they are outside the primary path and are not qualified here.

Replay claim-scope markers stay as the current contract declares them, e.g. `registry_authenticated` is `False`, `registry_origin_unverified` is set, `control_plane_decision_authenticated` is `False`. No external effect is executed.

## Result labels

`PASS`, `FAIL`, `REFUSED_AS_EXPECTED` (expected refusal observed with the expected typed code), `NOT_RUN`, `NOT_APPLICABLE` (a case that does not apply, or one of the four documented-limit rows below, which assert observed ADMITTED behavior and are never counted as refusals). A refusal is never reported as `PASS`. Any `FAIL` or `NOT_RUN` row, a missing required row, or a source-identity problem makes the run exit nonzero.

## Evidence

Written to `out_dir`: `summary.json`, `rows.jsonl`, `positive-case.json`, `source-identity.json`, `environment.json`, `tuple.json`, `sources-identity.tsv`, `junit.xml`, `pytest.log`, `SHA256SUMS`. Index: [`evidence/README.md`](evidence/README.md). Dependencies: `requirements.lock` (hash-locked). CI: `.github/workflows/r2-joined-chain.yml`.

## Documented limits (not refusals)

These behaviors of the pinned contracts are asserted, recorded as `NOT_APPLICABLE` rows (`J-limit`, `L-limit`, `O-limit`, `S-limit`), and NOT claimed as refusals. A behavior change would make them FAIL.

- J-limit: swapping in identical or effective-value-equivalent genuine evidence is admitted; the marker lists `substitution_by_other_genuine_selection` as not verified.
- L-limit: source-revision binding is declaration-only and unattested. A well-formed but wrong declared revision is admitted and marked `operator_declared_unattested`; only malformed revisions are refused (row L).
- O-limit: Replay does not cross-check the verdict's `selection_digest` and `bound_record_digest` members. The sha256 echoes of the exact texts are checked.
- S-limit: an identical duplicate signature entry and trailing whitespace on the selection text are admitted.

Note: two `engine` modules from the Registry's vendored `baseline/execution-runtime` load through the Registry's own consumer. The Execution Runtime component is not used or qualified here.
