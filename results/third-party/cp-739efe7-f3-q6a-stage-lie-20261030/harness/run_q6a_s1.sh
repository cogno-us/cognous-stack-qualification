#!/usr/bin/env bash
# usage: run_q6a_s1.sh <311|312> <label>
set -u
W=/tmp/claude-0/work/q6a; E=$W/evidence; CP=$W/src/cp-739efe7; INTERP=$1; L=$2
case "$INTERP" in 311) PY=/tmp/claude-0/work/venv311/bin/python;; 312) PY=/tmp/claude-0/work/d2/venv312/bin/python;; *) echo bad; exit 2;; esac
OUT=$E/raw/$L; mkdir -p "$OUT"
unset OCS_REGISTRY_PIN_DIR OCS_REQUIRE_REGISTRY_PIN PYTHONPATH Q6_FORMAT_MODULE_PATH
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$CP/src:$W/src/verifier/src
cd "$CP"
T=$E/harness/test_successor_q6a_stage_lie.py
{ echo "# label=$L interp=$INTERP cwd=$CP"; date -u +%FT%TZ; "$PY" --version; echo "PYTHONPATH=$PYTHONPATH"; echo "OCS_REGISTRY_PIN_DIR=<unset>"
  echo "cmd: $PY -m pytest -p no:cacheprovider -q -rA --junitxml=$OUT/junit.xml $T"; } > "$OUT/invocation.txt" 2>&1
"$PY" -m pytest -p no:cacheprovider -q -rA --junitxml="$OUT/junit.xml" "$T" > "$OUT/stdout.txt" 2> "$OUT/stderr.txt"
echo "exit=$?" >> "$OUT/stdout.txt"
"$PY" "$E/harness/assert_noskip.py" "$OUT/junit.xml" "$L" --min 4 > "$OUT/gate.txt" 2>&1
tail -3 "$OUT/stdout.txt"; tail -1 "$OUT/gate.txt"
