#!/usr/bin/env bash
# AMEND-D2-3 supplementary: tests/test_v02_claim_policy_binding.py hard-codes Registry pin 943ab18; usage: run_supp_v02.sh <311|312> <label>
set -u
W=/tmp/claude-0/work; D=$W/d2; CP=$D/src/cp-739efe7; L=$2
case "$1" in 311) PY=$W/venv311/bin/python;; 312) PY=$D/venv312/bin/python;; esac
OUT=$D/evidence/raw/$L; mkdir -p "$OUT"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$CP/src OCS_REGISTRY_PIN_DIR=$D/src/reg-943ab18 OCS_REQUIRE_REGISTRY_PIN=1
{ echo "# label=$L interp=$1 registry=$(git -C $OCS_REGISTRY_PIN_DIR rev-parse HEAD)"; date -u +%FT%TZ; "$PY" --version; } > "$OUT/invocation.txt" 2>&1
cd "$CP"; "$PY" -m pytest -p no:cacheprovider -q -rA --junitxml="$OUT/junit.xml" tests/test_v02_claim_policy_binding.py > "$OUT/stdout.txt" 2> "$OUT/stderr.txt"
echo "exit=$?" >> "$OUT/stdout.txt"; tail -3 "$OUT/stdout.txt"
