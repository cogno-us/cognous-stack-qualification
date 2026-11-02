# S3 FREEZE-STEPS (Worker Q3-tuple-prep, 2026-10-31) - PREPARATION ONLY, NOTHING EXECUTED
Governing: Engineering Constitution @ 1c2e920f4e58e07a52e8e2408a506cf7dbc1292b; Issue #254, Gate S3. Replaces PRERUN.md section 0/2/3 where they differ.

## State (all verified 2026-10-31 by `git ls-remote origin refs/heads/main` == SHA; trees via git rev-parse)
Branches (cogno-us/cognous-stack-qualification): RUN branch `security-wiki/s3-current-tuple-20261031` = prep config + ea8bddcd (cur patch, sha256 cb0fc4d2...e8d0d) + probe patch;
`prep/NOT-FOR-MERGE-s3-wiki41-20261031` = prep config + probe patch WITHOUT the cur patch (runner refuses there by design). Both are config-only; Exchange PENDING; runner refuses.
| Component | SHA | tree |
|---|---|---|
| control_plane | b19c47ddd020409d24e52e70b11359c46265edbb | 039219b5aba7a157fff79781c716067fad7ed985 |
| runtime | f7a55e2a8494801e49193f9f46935f0a971c248d | 97da8323368bb5a573fd157b11a9c1dda1178a10 |
| replay | d395e37c443fedf1bf6b9a4651338b7b7de4a553 | 0bdee3eacd650ecb0e99781635a972e68cbe2853 |
| evidence_pack | 96f5f2e126a9c27a75716658d4d2e85baf94b40b | 2fc26d4c86e65b22bdffedf1090a15e7167440d3 |
| odes | 77fd7a1cb1dd7a2dbc9ac3c02538a617056688ae | d8b33261de975fc504ff8f0ac30a8f47e8ebd43f |
| manifest | fa170815ef96a54c233d0dd9da821b60debabf8b | 3b0e3772e944aa668c8f4b879588c7cc3e2c32be |
| registry (tuple) | 6b96a9a658923954433dc1a4c13626fa5145b9c7 | 38d50602ae725e208f010baba05bbf7b908e76ac |
| registry (builder, probe only) | a40fe755e2384a99c37016fa9ad59396f1835900 | eab8ebcc24243c1abc9b6db834b7ef498f1bcb91 |
| exchange | PENDING (r2, profile security-runtime-current-20261031-r2 per other worker; merge SHA unknown) | PENDING |

## Step 0 - preconditions (stop if any is false)
a. Exchange r2 PR merged; `git ls-remote https://github.com/cogno-us/cognous-governed-exchange refs/heads/main` -> SHA X; tree T=`git rev-parse X^{tree}`. The Exchange profile name P is read from the MERGED Exchange source and must define exactly this tuple (Replay d395e37c, ODES 77fd7a1c, Pack 96f5f2e1, CP b19c47dd, Runtime f7a55e2a, Manifest fa170815). Do not use a branch/tag/name guess.
b. Architect go for the run. Disk: `df -m /` >= 300 MB free at start, abort < 200 MB (measured need ~150 MB; at 2026-10-31 free varied 0.5-1.1 GB because of other workers).
c. Work on the RUN branch in /home/claude/wt-s3 only (single writer): `git checkout security-wiki/s3-current-tuple-20261031`; `git status --porcelain --untracked-files=all` empty.

## Step 1 - fill the Exchange fields (7 places; all currently the string PLACEHOLDER:...)
Dir D=process/v1-validation/current-stack-S3-TEMPLATE, profile F=process/security-runtime-current-stack-S3-TEMPLATE.json
1. $D/runner-tuple.json: `exchange` = X; `exchange_compatibility_profile` = P
2. $F: `exchange_compatibility_profile` = P; `components.exchange.revision` = X
3. $D/freeze-manifest.json: `profile.exchange_compatibility_profile` = P; `components_subject.gax_imx_transport.sha` = X; `verified_trees.trees.exchange` = T
4. $D/tuple.json: `components.exchange[1]` = X; `verified_trees.trees.exchange` = T
## Step 2 - fill the freeze-time fields (also PLACEHOLDER; runner refuses on those in the profile/freeze-manifest)
$D/freeze-manifest.json: `frozen_utc` (YYYY-MM-DD), `identities.hub.head` (40-hex hub head at freeze), `identities.qualification.closeout` (qualification main SHA at configuration time).
$D/tuple.json (hashed, not scanned, but must be resolved): `option_A_status` (E3), `components.hub[1]`, `components.qualification[1]`, `known_consistency_risks` (re-state; CUR re-tie risk must be OBSERVED not assumed).
## Step 3 - rename TEMPLATE -> dated ids (the runner refuses 'TEMPLATE' in the runner tuple and the profile id must match; tested verbatim in a scratch sim)
```
DATE=20261101   # = frozen date, no dashes
N=current-stack-S3-$DATE
git mv process/v1-validation/current-stack-S3-TEMPLATE process/v1-validation/$N
git mv process/security-runtime-current-stack-S3-TEMPLATE.json process/security-runtime-$N.json
sed -i "s/current-stack-S3-TEMPLATE/$N/g" process/v1-validation/$N/*.json process/security-runtime-$N.json tools/run_wiki_s3.py   # also fixes profile_id, validation_id, DEFAULT_NODEIDS
```
Then delete the `_template_status` keys from the profile and freeze-manifest, and reword the label/note strings that say TEMPLATE (tuple.json label; freeze-manifest label and note; profile `note` if needed). `grep -rn "PLACEHOLDER\|TEMPLATE" process/security-runtime-$N.json process/v1-validation/$N tools/run_wiki_s3.py` must show only the runner's own check lines (run_wiki_s3.py:83 and :~137 text). tools/run_wiki_s3.py changes ONLY the DEFAULT_NODEIDS path (re-verify: `git diff` of that file is exactly that one line; this is the only allowed runner edit - cur-patch verification A-J relies on the runner being otherwise unchanged).
Commit (new commit, no amend) with the two Co-Authored-By/Claude-Session trailers. `git status --porcelain --untracked-files=all` empty; `git diff ea8bddcd~1 ea8bddcd | sha256sum` still cb0fc4d2943db0bfc3055c0c25b573c8c84349828fe631beae2b2deb268e8d0d; wiki41-nodeids.txt sha256 bd43f8891e4db51ca6a5d279328a58a0ac73e7b6e27da209c56d2313a836fc3c, 41 sorted-unique lines.
## Step 4 - fresh PRISTINE component checkouts (existing /home/claude/cs-components are NOT pristine: ignored __pycache__, extra fetched objects)
Use a NEW dir W=/home/claude/cs-components-s3run (runner-owned). For each name/repo/SHA (exchange = X):
```
export PYTHONDONTWRITEBYTECODE=1
mkdir -p $W/<name> && git -C $W/<name> init -q && git -C $W/<name> fetch -q --depth 1 https://github.com/cogno-us/<repo> <SHA> && git -C $W/<name> checkout -q --detach FETCH_HEAD
```
(control_plane=cognous-control-plane, runtime=cognous-execution-runtime, replay=cognous-replay-bundle, evidence_pack=cognous-governance-evidence-pack, odes=open-decision-evidence-standard, exchange=cognous-governed-exchange, manifest=cognous-action-manifest, registry=cognous-ocs-registry @ 6b96a9a6). Never run pytest/python inside them without PYTHONDONTWRITEBYTECODE=1 (pycache = not pristine). Verify each: `git rev-parse HEAD` == SHA, `git rev-parse HEAD^{tree}` == table, and `python3 -c "import sys;sys.path.insert(0,'tools');from pristine_checkout import require_pristine as r;..."` or simply the runner's --dry-check.
Second Registry checkout for the PROBE ONLY (a40fe755 is an ACCEPTED_PIN; 6b96a9a6 is not): `git clone --shared -n $W/registry $W/registry_a40 && git -C $W/registry_a40 checkout -q --detach a40fe755e2384a99c37016fa9ad59396f1835900` (needs the a40fe755 object in $W/registry: if absent, `git -C $W/registry fetch -q origin a40fe755e2384a99c37016fa9ad59396f1835900` first). 22 MB working tree, objects shared. NOTE `clone --shared` needs the source repo to keep existing; do not delete $W/registry before the probe.
PyNaCl (probe): pynacl 1.6.2 cp38-abi3 manylinux_2_34 wheel (1.4 MB), sha256 c8a231e3...59f6 must MATCH requirements-ed25519.lock.txt in the Registry; `pip install --no-deps --no-index --target $W/site <wheel>`; pass `--site $W/site`. cffi/pycparser already present in system Python 3.13.
## Step 5 - dry check (must print dry_check OK, collected 41, executed 0; writes nothing)
```
cd /home/claude/wt-s3
python3 tools/run_wiki_s3.py --tuple process/v1-validation/$N/runner-tuple.json --components $W --dry-check
```
(`--hub <pristine hub checkout at identities.hub.head>` optional.) Any REFUSED -> stop, do not run.
## Step 6 - the run (single execution; no -x, no reruns, no -n; 1 pytest process)
```
python3 tools/run_wiki_s3.py --tuple process/v1-validation/$N/runner-tuple.json --components $W --out results/security-wiki-s3-$DATE   # out dir must not exist
```
Do not rerun the 244 passing cases. Registry probe (separate, labelled, after the Wiki run, not Wiki coverage):
```
python3 tools/registry_integration_probe.py --tuple process/v1-validation/$N/runner-tuple.json --components $W --registry-builder-dir $W/registry_a40 --site $W/site --out results/security-wiki-s3-$DATE-registry-probe [--dry-check first]
```
Vocabulary: PASS_IMPORT / REFUSED_AS_EXPECTED / FAIL / BLOCKED(reason) / NOT_APPLICABLE / NON_DETECTION_RECORDED / RETENTION_ONLY; DRY_CHECK_OK = preparation only. claims_made = []; qualification NONE.
## Step 7 - evidence (new evidence branch, no force-push)
results/security-wiki-s3-$DATE/: raw/{junit.xml,log.txt,obs.json,run.json,collect-only.txt,nodeids-41.txt,tuple.json}, SHA256SUMS, per-test-41.csv with the 7 required fields (test ID; expected behaviour; actual behaviour; first failure/refusal boundary; applicable component revision; PASS/FAIL/BLOCKED; raw evidence reference) plus extra columns (junit status, observer calls). 41 rows; vacuous exception-only success is NOT a PASS. REPORT.md states PROVISIONAL DEVELOPMENT PIN / UNQUALIFIED status of the CUR pins inherited, caller-asserted provenance labels, and the Registry bytes caveat (a40fe755 exercised, 6b96a9a6 recorded).
## Step 8 - cleanup
Remove $W (or keep only if the architect wants the checkouts as evidence), scratch dirs; `git status` clean; `git ls-remote origin <branch>` == `git rev-parse HEAD` for every pushed branch.

## Known facts to carry into REPORT.md
- Registry 6b96a9a6 vs a40fe755: 62 paths differ (59 added/3 modified), all under docs/ or README.md; 12 .py files under docs/ are analysis scripts not imported by any package/test/CP builder.
- cur patch re-verified against MERGED ODES 77fd7a1c/Replay d395e37c: conditions A-J PASS; `cur` collects the same 326 ids as p2 with no ImportError (results/security-wiki-s3-20261031/merged-components-verification/). Exchange used there was the OLD local 7f7569b0 (collection does not exercise it); the real collect-only against Exchange X is performed by the runner's --dry-check.
- Probe: Runtime export of a governed decision BLOCKED (PinnedControlPlaneExecutor rebuilds workflow, cannot build GovernedPolicyWorkflow) - recorded, not repaired.
