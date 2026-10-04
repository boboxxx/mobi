#!/usr/bin/env bash
set -eu
cd /home/sheng/mobicom2027_visibility_20261001
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
TASK_PY=/home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python
E=experiments/matched_registration_20261004
P=results/matched_registration_20261004
"$TASK_PY" - <<'PY'
import hashlib,json
from pathlib import Path
f=json.loads(Path('experiments/matched_registration_20261004/freeze.json').read_bytes())
for section in ('sources','inputs'):
 for n,h in f[section].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h,n
b=json.loads(Path('results/body_expiry_20261004/native_build_sheng.json').read_bytes());assert hashlib.sha256(Path('experiments/body_expiry_20261004/proposer.so').read_bytes()).hexdigest()==b['local_binary_sha256']
print('FROZEN_SOURCES_INPUTS_NATIVE_VALIDATED',flush=True)
PY
"$TASK_PY" -m unittest discover -s "$E" -p 'test_*.py' -v > "$P/tests_sheng_before_timing.log" 2>&1
timeout --signal=INT --kill-after=30 1200 "$TASK_PY" "$E/produce.py" --results "$P" > "$P/produce_sheng.log" 2>&1
"$TASK_PY" "$E/audit.py" --results "$P" --out "$P/audit_sheng.json" > "$P/audit_sheng.log" 2>&1
"$TASK_PY" -m unittest discover -s "$E" -p 'test_*.py' -v > "$P/tests_sheng.log" 2>&1
printf 'FINITE_MATCHED_REGISTRATION_COMPLETE\n' > "$P/run_terminal.txt"
printf 'FINITE_MATCHED_RUNNER_SUCCESS\n'
