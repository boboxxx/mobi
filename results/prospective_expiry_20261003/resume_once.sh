#!/usr/bin/env bash
set -eu
cd /home/sheng/mobicom2027_visibility_20261001
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
PY=/home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python
E=experiments/prospective_expiry_20261003
P=results/prospective_expiry_20261003
$PY $E/evaluate.py --results $P > $P/evaluate_sheng.log 2>&1
$PY $E/audit.py --results $P --out $P/audit_sheng.json > $P/audit_sheng.log 2>&1
$PY $E/summarize.py --results $P --out $P/summary_sheng.json > $P/summary_sheng.log 2>&1
$PY $E/action_functional.py --results $P > $P/action_functional_sheng.log 2>&1
$PY $E/action_functional_audit.py --results $P --out $P/action_functional_audit_sheng.json > $P/action_functional_audit_sheng.log 2>&1
$PY $E/action_functional_summary.py --results $P --out $P/action_functional_summary_sheng.json > $P/action_functional_summary_sheng.log 2>&1
$PY $E/support_audit.py --results $P --out $P/support_audit_sheng.json > $P/support_audit_sheng.log 2>&1
$PY $E/tightness.py --results $P --out $P/tightness_sheng.json > $P/tightness_sheng.log 2>&1
$PY $E/contract_audit.py --results $P --out $P/contract_audit_sheng.json > $P/contract_audit_sheng.log 2>&1
$PY -m unittest discover -s $E -p 'test_*.py' -v > $P/tests_sheng.txt 2>&1
printf 'complete\n' > "$P/run_terminal.txt"
