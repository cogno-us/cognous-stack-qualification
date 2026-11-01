#!/usr/bin/env bash
# OCS-MVP-QGATE-05 / Worker C: append the complete raw evidence of the single authorized run to the append-only evidence branch (PROPOSED, non-authorizing).
#
# Usage: qgate05_evidence_commit.sh ARTIFACT_DIR
#   ARTIFACT_DIR  the downloaded run artifact (the whole results/mvp-acceptance tree, incl. its own SHA256SUMS)
# Required environment: GITHUB_REPOSITORY, GITHUB_RUN_ID, GITHUB_RUN_ATTEMPT, GITHUB_SHA, GITHUB_SERVER_URL, and EITHER GH_TOKEN (push over https with the job token)
#   OR QG5_REMOTE_URL (a git URL; used by the local dry run, e.g. file:///tmp/x.git).
# Optional: QG5_BRANCH (default nm138/evidence-run-1; the workflow never sets it), QG5_MAX_FILE_BYTES (default 95000000: GitHub rejects files >100 MB),
#           QG5_ACTOR_NAME / QG5_ACTOR_EMAIL, QG5_WORKFLOW_SHA, QG5_JOB_STATUS (the run job's result, recorded only).
#
# Rules (enforced here, visible to a reviewer):
#   * pushes ONLY to refs/heads/$QG5_BRANCH (never main, never a tag), NEVER with --force / + / --delete; a rejected push is a failure, not retried;
#   * append-only: if the branch exists the new commit is built on top of its tip (fast-forward); if the run directory runs/run-<id>-attempt-<n> already exists
#     in the tip the script refuses (it never overwrites or removes a committed file);
#   * the committed tree is: runs/run-<id>-attempt-<n>/{<the artifact tree>, RUN-IDENTITY.json, EVIDENCE-FILES.txt, SHA256SUMS}; SHA256SUMS covers EVERY committed file of that
#     run directory except itself; the artifact's own SHA256SUMS is kept as SHA256SUMS.run-job and verified (result recorded in ARTIFACT-SHA256SUMS-VERIFY.txt);
#   * a file larger than QG5_MAX_FILE_BYTES is NOT committed; it is listed (path, size, sha256) in OMITTED-LARGE-FILES.txt and stays in the Actions artifact.
set -u
ART=${1:?usage: $0 ARTIFACT_DIR}
BRANCH=${QG5_BRANCH:-nm138/evidence-run-1}
case "$BRANCH" in main|master|refs/*|"") echo "refusing branch '$BRANCH'" >&2; exit 2 ;; esac
case "$BRANCH" in nm138/evidence-run-*) ;; *) echo "branch must match nm138/evidence-run-*" >&2; exit 2 ;; esac
: "${GITHUB_RUN_ID:?}" "${GITHUB_RUN_ATTEMPT:?}" "${GITHUB_SHA:?}" "${GITHUB_REPOSITORY:?}"
MAXB=${QG5_MAX_FILE_BYTES:-95000000}
RUNDIR="runs/run-${GITHUB_RUN_ID}-attempt-${GITHUB_RUN_ATTEMPT}"
# The token is NEVER placed in a URL (a URL is echoed by git on errors and stored in .git/config): network commands carry it as an http.extraheader on the command line only.
GITN=(git)
if [ -n "${QG5_REMOTE_URL:-}" ]; then REMOTE=$QG5_REMOTE_URL
else : "${GH_TOKEN:?GH_TOKEN or QG5_REMOTE_URL}"; REMOTE="https://github.com/${GITHUB_REPOSITORY}.git"
  GITN=(git -c "http.extraheader=AUTHORIZATION: basic $(printf 'x-access-token:%s' "$GH_TOKEN" | base64 -w0)"); fi
redact() { sed -e 's#x-access-token:[^@ ]*#x-access-token:***#g' -e 's#\(AUTHORIZATION: *basic\) *[A-Za-z0-9+/=]*#\1 ***#Ig'; }
[ -d "$ART" ] || { echo "artifact dir $ART missing" >&2; exit 1; }
ART=$(cd "$ART" && pwd -P)

W=$(mktemp -d) || exit 1
trap 'rm -rf "$W"' EXIT
git init -q "$W/repo" || exit 1
cd "$W/repo" || exit 1
git config user.name  "${QG5_ACTOR_NAME:-github-actions[bot]}"
git config user.email "${QG5_ACTOR_EMAIL:-41898282+github-actions[bot]@users.noreply.github.com}"
git config advice.detachedHead false
git remote add origin "$REMOTE"
if "${GITN[@]}" ls-remote --exit-code --heads origin "refs/heads/$BRANCH" >"$W/lsremote.txt" 2>"$W/lsremote.err"; then
  "${GITN[@]}" fetch -q --depth 1 origin "refs/heads/$BRANCH" || { echo "fetch of existing $BRANCH failed" >&2; exit 1; }
  git checkout -q -b evidence FETCH_HEAD || exit 1
  MODE=append
else
  rc=$?
  [ "$rc" = 2 ] || { echo "ls-remote failed (rc=$rc): $(redact <"$W/lsremote.err")" >&2; exit 1; }
  git checkout -q --orphan evidence || exit 1
  MODE=create
fi
[ ! -e "$RUNDIR" ] || { echo "$RUNDIR already exists on $BRANCH: refusing to overwrite or duplicate" >&2; exit 1; }
mkdir -p "$RUNDIR" || exit 1

# 1. the artifact tree (files <= MAXB), omitted list for the rest
: >"$W/omitted.txt"
( cd "$ART" && find . -type f -print0 | sort -z ) | while IFS= read -r -d '' f; do
  f=${f#./}
  sz=$(stat -c %s "$ART/$f")
  if [ "$sz" -gt "$MAXB" ]; then
    printf '%s\t%s\t%s\n' "$f" "$sz" "$(sha256sum "$ART/$f" | cut -d' ' -f1)" >>"$W/omitted.txt"
  else
    mkdir -p "$RUNDIR/$(dirname "$f")" && cp -p "$ART/$f" "$RUNDIR/$f"
  fi
done
[ -s "$W/omitted.txt" ] && { echo "# path<TAB>bytes<TAB>sha256 of files NOT committed (> $MAXB bytes); they remain in the Actions artifact"; cat "$W/omitted.txt"; } >"$RUNDIR/OMITTED-LARGE-FILES.txt"

# 2. verify the artifact's own manifest against the downloaded bytes (record, never repair)
if [ -f "$ART/SHA256SUMS" ]; then
  mv "$RUNDIR/SHA256SUMS" "$RUNDIR/SHA256SUMS.run-job" 2>/dev/null
  ( cd "$ART" && sha256sum -c SHA256SUMS ) >"$RUNDIR/ARTIFACT-SHA256SUMS-VERIFY.txt" 2>&1
  echo "sha256sum -c exit=$?" >>"$RUNDIR/ARTIFACT-SHA256SUMS-VERIFY.txt"
else
  echo "the artifact carries no SHA256SUMS" >"$RUNDIR/ARTIFACT-SHA256SUMS-VERIFY.txt"
fi

# 3. run identity written by THIS job from the Actions context (does not replace the run job's own run-identity.json, which stays in the tree)
python3 - "$RUNDIR/RUN-IDENTITY.json" <<'PY'
import json, os, sys
keys = ["GITHUB_REPOSITORY", "GITHUB_RUN_ID", "GITHUB_RUN_NUMBER", "GITHUB_RUN_ATTEMPT", "GITHUB_SHA", "GITHUB_REF", "GITHUB_EVENT_NAME", "GITHUB_WORKFLOW", "GITHUB_WORKFLOW_REF",
        "GITHUB_JOB", "GITHUB_ACTOR", "RUNNER_NAME", "RUNNER_OS", "ImageOS", "ImageVersion", "QG5_WORKFLOW_SHA", "QG5_JOB_STATUS"]
doc = {k: os.environ.get(k) for k in keys}
doc["run_url"] = "%s/%s/actions/runs/%s" % (os.environ.get("GITHUB_SERVER_URL", "https://github.com"), os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_RUN_ID"))
doc["written_by"] = "evidence job (tools/qgate05_evidence_commit.sh); non-authorizing; the run job's own record is run-identity.json in this directory"
open(sys.argv[1], "w").write(json.dumps(doc, indent=2, sort_keys=True) + "\n")
PY

# 4. file list and the committed-tree manifest (every file of the run directory except SHA256SUMS itself)
( cd "$RUNDIR" && find . -type f ! -name SHA256SUMS ! -name EVIDENCE-FILES.txt | sort >EVIDENCE-FILES.txt )
( cd "$RUNDIR" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum >SHA256SUMS )
( cd "$RUNDIR" && sha256sum -c SHA256SUMS >/dev/null 2>&1 ) || { echo "committed manifest does not verify" >&2; exit 1; }
NFILES=$(wc -l <"$RUNDIR/SHA256SUMS")

git add -A -- "$RUNDIR" || exit 1
git commit -q -m "QGATE-05 evidence: run ${GITHUB_RUN_ID} attempt ${GITHUB_RUN_ATTEMPT} (${NFILES} files, non-authorizing)

Qualification commit: ${GITHUB_SHA}
Run: ${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}
Appended by the evidence job; raw evidence only; no verdict is edited, no file is overwritten." || { echo "commit failed" >&2; exit 1; }
COMMIT=$(git rev-parse HEAD)

# 5. push: explicit refspec to the evidence branch only, no force. A rejection is a failure.
"${GITN[@]}" push origin "HEAD:refs/heads/$BRANCH" 2>"$W/push.err"
prc=$?
redact <"$W/push.err" >&2
if [ "$prc" != 0 ]; then echo "push to $BRANCH rejected or failed (rc=$prc); not retried" >&2; exit 1; fi
echo "evidence committed: mode=$MODE branch=$BRANCH commit=$COMMIT dir=$RUNDIR files=$NFILES"
echo "SHA256SUMS sha256: $(sha256sum "$RUNDIR/SHA256SUMS" | cut -d' ' -f1)"
[ -n "${GITHUB_STEP_SUMMARY:-}" ] && { echo "### QGATE-05 evidence branch"; echo "- branch: \`$BRANCH\` commit \`$COMMIT\` dir \`$RUNDIR\` files $NFILES mode $MODE"; echo "- SHA256SUMS sha256: \`$(sha256sum "$RUNDIR/SHA256SUMS" | cut -d' ' -f1)\`"; } >>"$GITHUB_STEP_SUMMARY"
exit 0
