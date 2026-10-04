#!/usr/bin/env bash
set -eu
cd /home/sheng/mobicom2027_visibility_20261001
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
TASK_PY=/home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python
E=experiments/prospective_component_20261004
P=results/prospective_component_20261004
"$TASK_PY" "$E/qualify.py" --split calibration > "$P/calibration.log" 2>&1
"$TASK_PY" "$E/qualify.py" --split certification > "$P/certification_qualification.log" 2>&1
"$TASK_PY" "$E/produce.py" --split certification > "$P/certification_paid.log" 2>&1
"$TASK_PY" "$E/certify.py" > "$P/certification.log" 2>&1
"$TASK_PY" "$E/qualify.py" --split test > "$P/test_qualification.log" 2>&1
"$TASK_PY" "$E/produce.py" --split test > "$P/test_paid.log" 2>&1
"$TASK_PY" "$E/audit.py" --out "$P/audit_sheng.json" > "$P/audit_sheng.log" 2>&1
"$TASK_PY" -m unittest discover -s "$E" -p 'test_*.py' > "$P/tests_after_evaluation_sheng.log" 2>&1
printf 'FINITE_PROSPECTIVE_COMPONENT_EVALUATION_COMPLETE\n' > "$P/terminal.txt"
