#!/usr/bin/env bash
# usage: run_d1.sh <label> <cp-root> <outdir> [pytest -k expr]
set -u
W=/tmp/claude-0/work; L=$1; CP=$2; OUT=$3; SEL=${4:-}
mkdir -p $OUT/helper
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$CP/src D1_CP_ROOT=$CP D1_LABEL=$L OCS_REGISTRY_PIN_DIR=$W/run/reg-v8 OCS_REQUIRE_REGISTRY_PIN=1 \
  F3_EVIDENCE_DIR=$OUT/helper D1_EVIDENCE_DIR=$OUT
cd $OUT
ARGS=(); if [ -n "$SEL" ]; then ARGS=(-k "$SEL"); fi
date -u +%FT%TZ > $OUT/start.txt
$W/venv311/bin/python -m pytest -p no:cacheprovider -q -rA "${ARGS[@]}" $W/d1/evidence/harness/test_d1.py > $OUT/stdout.txt 2> $OUT/stderr.txt
echo "exit=$?" >> $OUT/stdout.txt
date -u +%FT%TZ > $OUT/end.txt
tail -15 $OUT/stdout.txt
