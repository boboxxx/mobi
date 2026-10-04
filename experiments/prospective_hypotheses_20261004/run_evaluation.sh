#!/usr/bin/env bash
set -eu
cd /home/sheng/mobicom2027_visibility_20261001
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
TASK_PY=/home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python
E=experiments/prospective_hypotheses_20261004
P=results/prospective_hypotheses_20261004
test -f "$P/capture_terminal.txt"
test -f "$P/server_stopped.json"
"$TASK_PY" -m unittest discover -s "$E" -p 'test_*.py' > "$P/tests_before_evaluation_sheng.log" 2>&1
"$TASK_PY" "$E/qualify.py" > "$P/qualification_sheng.log" 2>&1
"$TASK_PY" "$E/audit.py" --qualification-only --out "$P/audit_qualification_sheng.json" > "$P/audit_qualification_sheng.log" 2>&1
"$TASK_PY" "$E/produce.py" > "$P/paid_sheng.log" 2>&1
"$TASK_PY" "$E/audit.py" --out "$P/audit_sheng.json" > "$P/audit_sheng.log" 2>&1
"$TASK_PY" "$E/summarize.py" > "$P/summarize_sheng.log" 2>&1
"$TASK_PY" -m unittest discover -s "$E" -p 'test_*.py' > "$P/tests_after_evaluation_sheng.log" 2>&1
printf 'FINITE_EVALUATION_AND_AUDIT_COMPLETE\n' > "$P/evaluation_terminal.txt"
