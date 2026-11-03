#!/usr/bin/env bash
# R2 joined-chain participant run: ONE command from a clean checkout of the qualification repository.
#   bash r2_chain/participant_run.sh [out_dir]
#
# PRIVATE PREVIEW QUALIFICATION TUPLE (preview-only, NOT canonical; component-lock.json untouched).
# Synthetic only; single synthetic tenant; claim A only. No secrets, no credentials, no paid APIs, no production services.
#
# NETWORK: required ONLY for (1) installing the hash-locked packages from PyPI and (2) fetching the three pinned source trees by exact SHA from public
# GitHub (https://github.com/cogno-us/...). The tests themselves use no network. Nothing else is contacted.
#
# Needs: bash, git, python3 (3.11+; CI uses 3.13) with the venv module. Exit status is nonzero on any failure.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$here/.." && pwd)"

if [ "$#" -gt 1 ]; then
  echo "usage: bash r2_chain/participant_run.sh [out_dir]" >&2
  exit 2
fi
tmp="$(mktemp -d "${TMPDIR:-/tmp}/r2-participant.XXXXXX")"
cleanup() { rm -rf "$tmp"; }
trap cleanup EXIT

out_arg="${1:-${TMPDIR:-/tmp}/r2-joined-chain-evidence}"
mkdir -p "$out_arg"
out="$(cd "$out_arg" && pwd)"

echo "== R2 joined chain: PRIVATE PREVIEW QUALIFICATION TUPLE (preview-only, NOT canonical)"
echo "== synthetic only | single synthetic tenant | claim A only | network used only to install packages and fetch pinned sources"
echo "== qualification checkout: $(git -C "$repo_root" rev-parse HEAD 2>/dev/null || echo 'not a git checkout')"

echo "== [1/4] creating temporary virtualenv and installing hash-locked dependencies"
python3 -m venv "$tmp/venv"
"$tmp/venv/bin/python" -m pip install --quiet --disable-pip-version-check --require-hashes -r "$here/requirements.lock"

echo "== [2/4] fetching pinned sources by exact SHA (HEAD and tree verified)"
bash "$here/fetch_sources.sh" "$tmp/src" | tee "$tmp/sources-identity.tsv"

echo "== [3/4] running the joined chain (positive case, negative matrix, persistence negative, source identity)"
export SRC_DIR="$tmp/src"
export PYTHONDONTWRITEBYTECODE=1
cp "$tmp/sources-identity.tsv" "$out/sources-identity.tsv"
rc=0
"$tmp/venv/bin/python" -B "$here/run_chain.py" --src-dir "$tmp/src" --out "$out" || rc=$?

echo "== [4/4] summary"
"$tmp/venv/bin/python" -B -I - "$out" <<'PY'
import json, sys
from pathlib import Path
out = Path(sys.argv[1])
s = json.loads((out / "summary.json").read_text())
c = s["label_counts"]
print("  PASS                 : %d" % c["PASS"])
print("  REFUSED_AS_EXPECTED  : %d" % c["REFUSED_AS_EXPECTED"])
print("  NOT_APPLICABLE       : %d" % c["NOT_APPLICABLE"])
print("  NOT_RUN              : %d" % c["NOT_RUN"])
print("  FAIL                 : %d" % c["FAIL"])
print("  disposition          : %s" % s["disposition"])
for p in s["problems"]:
    print("  PROBLEM: %s" % p)
print("  machine-readable evidence in: %s" % out)
for n in ("summary.json", "rows.jsonl", "positive-case.json", "source-identity.json", "environment.json", "SHA256SUMS"):
    print("    %s%s" % (n, "" if (out / n).exists() else "  (MISSING)"))
PY

if [ "$rc" -ne 0 ]; then
  echo "== R2 joined chain: FAILED (run_chain.py exit $rc)" >&2
  exit "$rc"
fi
echo "== R2 joined chain: PASSED (claim A only; see r2_chain/README.md for what this does and does not prove)"
