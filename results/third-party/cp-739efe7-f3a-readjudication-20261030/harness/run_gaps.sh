#!/usr/bin/env bash
# usage: run_gaps.sh <label: 739efe7|8616d5f|M06> <cp-root> <selector -k expr or ''>
set -u
W=/tmp/claude-0/work; L=$1; CP=$2; SEL=${3:-}
OUT=$W/evidence/cp-739efe7-f3a-readjudication-20261030/raw/$L; mkdir -p $OUT/helper
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$CP/src READJ_CP_ROOT=$CP OCS_REGISTRY_PIN_DIR=$W/run/reg-v8 OCS_REQUIRE_REGISTRY_PIN=1 \
  F3_EVIDENCE_DIR=$OUT/helper READJ_EVIDENCE_DIR=$OUT F3_OLD_SRC=$W/src/cp-b7eb11a/src
cd $OUT
ARGS=(); if [ -n "$SEL" ]; then ARGS=(-k "$SEL"); fi
$W/venv311/bin/python -m pytest -p no:cacheprovider -q "${ARGS[@]}" $W/harness/test_readj_gaps.py > $OUT/stdout.txt 2> $OUT/stderr.txt
echo "exit=$?" >> $OUT/stdout.txt
tail -5 $OUT/stdout.txt
