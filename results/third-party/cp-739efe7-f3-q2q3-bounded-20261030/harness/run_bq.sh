#!/usr/bin/env bash
# usage: run_bq.sh <label> <cp-root> <reg-pin-dir> <python> <outdir> [pytest -k expr]
# <outdir> is the evidence root for this run; run_bq.sh is run from any cwd; harness dir = dir of this script.
set -u
L=$1; CP=$2; REG=$3; PY=$4; OUT=$5; SEL=${6:-}
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$OUT/helper" "$OUT/basetemp-parent"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$CP/src" \
  OCS_REGISTRY_PIN_DIR="$REG" OCS_REQUIRE_REGISTRY_PIN=1 \
  BQ_PROTOCOL=OCS-F3-Q2Q3-BOUNDED-v1 BQ_CP_ROOT="$CP" BQ_LABEL="$L" BQ_EVIDENCE_DIR="$OUT" \
  D1_CP_ROOT="$CP" D1_LABEL="$L" D1_EVIDENCE_DIR="$OUT" F3_EVIDENCE_DIR="$OUT/helper"   # D1_*/F3_* are read by the reused d1_lib/orig_harness
ARGS=(); if [ -n "$SEL" ]; then ARGS=(-k "$SEL"); fi
cd "$OUT"
date -u +%FT%TZ > "$OUT/start.txt"
"$PY" -m pytest -p no:cacheprovider -q -rA --junitxml="$OUT/junit.xml" --basetemp="$OUT/basetemp-parent/bt" \
  "${ARGS[@]}" "$HERE"/test_bq*.py > "$OUT/stdout.txt" 2> "$OUT/stderr.txt"
echo "exit=$?" >> "$OUT/stdout.txt"
date -u +%FT%TZ > "$OUT/end.txt"
tail -15 "$OUT/stdout.txt"
