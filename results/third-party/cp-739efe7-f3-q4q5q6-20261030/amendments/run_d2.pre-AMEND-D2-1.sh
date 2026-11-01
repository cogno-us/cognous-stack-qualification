#!/usr/bin/env bash
# D-2 runner. usage: run_d2.sh <interp: 311|312> <label> <cp-root> <suite> <variant: pristine|M06|M04> [pytest -k expression]
# suites: readj (frozen readjudication harness) | orig (frozen original harness post-AMEND4) | builder (7 ungated D-06 builder files, junit) | d2 (this worker's test_d2_q4q5.py)
set -u
W=/tmp/claude-0/work; D=$W/d2; INTERP=$1; L=$2; CP=$3; SUITE=$4; VARIANT=$5; SEL=${6:-}
case "$INTERP" in 311) PY=$W/venv311/bin/python;; 312) PY=$D/venv312/bin/python;; *) echo bad interp; exit 2;; esac
OUT=$D/evidence/raw/$L; mkdir -p "$OUT/helper"
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$CP/src READJ_CP_ROOT=$CP D2_CP_ROOT=$CP OCS_REGISTRY_PIN_DIR=$W/run/reg-v8 OCS_REQUIRE_REGISTRY_PIN=1 \
  F3_EVIDENCE_DIR=$OUT/helper READJ_EVIDENCE_DIR=$OUT D2_EVIDENCE_DIR=$OUT F3_OLD_SRC=$D/src/cp-b7eb11a/src D2_VARIANT=$VARIANT
ARGS=(); if [ -n "$SEL" ]; then ARGS=(-k "$SEL"); fi
{ echo "# label=$L interp=$INTERP suite=$SUITE variant=$VARIANT cp=$CP sel='$SEL'"; date -u +%FT%TZ; "$PY" --version; } > "$OUT/invocation.txt" 2>&1
H=$D/evidence/harness
case "$SUITE" in
  readj) cd "$OUT"; "$PY" -m pytest -p no:cacheprovider -q -rA --junitxml="$OUT/junit.xml" "${ARGS[@]}" "$H/test_readj_gaps.py" > "$OUT/stdout.txt" 2> "$OUT/stderr.txt";;
  orig)  cd "$OUT"; "$PY" -m pytest -p no:cacheprovider -q -rA --junitxml="$OUT/junit.xml" "${ARGS[@]}" "$H/test_f3a_independent.post-AMEND4.py" > "$OUT/stdout.txt" 2> "$OUT/stderr.txt";;
  d2)    cd "$OUT"; "$PY" -m pytest -p no:cacheprovider -q -rA --junitxml="$OUT/junit.xml" "${ARGS[@]}" "$H/test_d2_q4q5.py" > "$OUT/stdout.txt" 2> "$OUT/stderr.txt";;
  builder) cd "$CP"; "$PY" -m pytest -p no:cacheprovider -q -rA --junitxml="$OUT/junit.xml" tests/test_effective_configuration_binding.py tests/test_effective_configuration_binding_dedicated.py \
      tests/test_effective_configuration_binding_legacy.py tests/test_effective_configuration_binding_unit.py tests/test_authorization_pin_export.py tests/test_claim_journal_stage.py \
      tests/test_v02_claim_policy_binding.py > "$OUT/stdout.txt" 2> "$OUT/stderr.txt";;
  *) echo bad suite; exit 2;;
esac
echo "exit=$?" >> "$OUT/stdout.txt"
tail -4 "$OUT/stdout.txt"
