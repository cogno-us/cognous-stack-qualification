#!/bin/bash
m=$1; b=$(basename $m .py); out=/home/claude/cs-run/run2
cd /home/claude/wt-wiki
export PYTHONDONTWRITEBYTECODE=1 SCN_COMPONENTS_DIR=/home/claude/cs-components V1_VALIDATION_ID=current-stack-20261031 V1_PROFILE=process/security-runtime-current-stack-20261031.json PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 OBS_OUT=$out/$b.obs.json PYTHONPATH=/home/claude/cs-pkg
timeout 2400 python3 -m pytest -q -p no:cacheprovider -p obs_plugin -o junit_family=xunit1 -rA "$m" --junitxml=$out/$b.junit.xml > $out/$b.log 2>&1
echo "$b rc=$?" >> $out/_done.txt
