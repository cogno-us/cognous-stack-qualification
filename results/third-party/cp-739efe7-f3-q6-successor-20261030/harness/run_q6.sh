#!/usr/bin/env bash
# Q6 successor runner. usage: run_q6.sh <311|312> <label> <case>
# cases: A (journal stage, verifier on path) | A0 (negative control, verifier NOT on path) | B0 (original format-module test, unmodified, negative control)
#        B (successor copy with env FORMAT_PATH) | C (original v02 file against Registry checkout at 943ab18)
set -u
W=/tmp/claude-0/work/q6; E=$W/evidence; CP=$W/src/cp-739efe7; INTERP=$1; L=$2; CASE=$3
case "$INTERP" in 311) PY=/tmp/claude-0/work/venv311/bin/python;; 312) PY=/tmp/claude-0/work/d2/venv312/bin/python;; *) echo bad interp; exit 2;; esac
OUT=$E/raw/$L; mkdir -p "$OUT"
# hermetic base env: no Registry pin vars unless the case sets them
unset OCS_REGISTRY_PIN_DIR OCS_REQUIRE_REGISTRY_PIN PYTHONPATH Q6_FORMAT_MODULE_PATH
export PYTHONDONTWRITEBYTECODE=1
PP=$CP/src
cd "$CP"
case "$CASE" in
  A)  export PYTHONPATH=$PP:$W/src/verifier/src; T=(tests/test_claim_journal_stage.py);;
  A0) export PYTHONPATH=$PP; T=(tests/test_claim_journal_stage.py);;
  B0) export PYTHONPATH=$PP; T=(tests/test_authorization_pin_export.py::test_payload_passes_the_runtime_format_module_when_available);;
  B)  export PYTHONPATH=$PP; export Q6_FORMAT_MODULE_PATH=$W/src/fmt/authorization_pin_format.py; T=($E/harness/test_successor_pin_export_format_module.py);;
  C)  export PYTHONPATH=$PP; export OCS_REGISTRY_PIN_DIR=$W/src/reg-943ab18 OCS_REQUIRE_REGISTRY_PIN=1; T=(tests/test_v02_claim_policy_binding.py);;
  *) echo bad case; exit 2;;
esac
{ echo "# label=$L interp=$INTERP case=$CASE cwd=$CP"; date -u +%FT%TZ; "$PY" --version
  echo "PYTHONPATH=$PYTHONPATH"; echo "OCS_REGISTRY_PIN_DIR=${OCS_REGISTRY_PIN_DIR:-<unset>}"; echo "Q6_FORMAT_MODULE_PATH=${Q6_FORMAT_MODULE_PATH:-<unset>}"
  echo "cmd: $PY -m pytest -p no:cacheprovider -q -rA --junitxml=$OUT/junit.xml ${T[*]}"; } > "$OUT/invocation.txt" 2>&1
"$PY" -m pytest -p no:cacheprovider -q -rA --junitxml="$OUT/junit.xml" "${T[@]}" > "$OUT/stdout.txt" 2> "$OUT/stderr.txt"
echo "exit=$?" >> "$OUT/stdout.txt"
tail -3 "$OUT/stdout.txt"
