#!/usr/bin/env bash
set -eu
cd /home/sheng/mobicom2027_visibility_20261001
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
TASK_PY=/home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python
E=experiments/prospective_shape_20261004
P=results/prospective_shape_20261004
stop_owned() {
 powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'C:\Users\Administrator\mobi-prospective-shape-stop.ps1' </dev/null > "$P/stop.log" 2>&1
 cp /mnt/c/Users/Administrator/mobi-prospective-shape-stopped.json "$P/server_stopped.json"
}
trap stop_owned EXIT
"$TASK_PY" - <<'PY'
import hashlib,json
from pathlib import Path
f=json.loads(Path('experiments/prospective_shape_20261004/freeze.json').read_bytes())
for section in ('sources','inputs'):
 for n,h in f[section].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h,n
native=json.loads(Path('results/body_expiry_20261004/native_build_sheng.json').read_bytes());assert hashlib.sha256(Path('experiments/body_expiry_20261004/proposer.so').read_bytes()).hexdigest()==native['local_binary_sha256']
print('FREEZE_AND_NATIVE_VALIDATED',flush=True)
PY
"$TASK_PY" - <<'PY'
import carla,time
for i in range(18):
 try:
  c=carla.Client('100.109.48.32',2000);c.set_timeout(4);w=c.get_world();assert c.get_server_version()=='0.9.15';print('server ready',flush=True);break
 except Exception:
  if i==17:raise
  time.sleep(2)
PY
cp /mnt/c/Users/Administrator/mobi-prospective-shape-server.json "$P/server_started.json"
timeout --signal=INT --kill-after=40 3300 "$TASK_PY" "$E/capture.py" --out "$P/capture" > "$P/capture.log" 2>&1
printf 'CAPTURE_TERMINAL_SUCCESS\n' > "$P/capture_terminal.txt"
stop_owned
trap - EXIT
"$TASK_PY" "$E/evaluate.py" --results "$P" > "$P/evaluate_sheng.log" 2>&1
"$TASK_PY" "$E/audit.py" --results "$P" --out "$P/audit_sheng.json" > "$P/audit_sheng.log" 2>&1
"$TASK_PY" "$E/summarize.py" --results "$P" --out "$P/summary_sheng.json" > "$P/summary_sheng.log" 2>&1
"$TASK_PY" -m unittest discover -s "$E" -p 'test_*.py' -v > "$P/tests_sheng.log" 2>&1
"$TASK_PY" -m unittest discover -s experiments/pose_support_20261004 -p 'test_*.py' -v > "$P/tests_inherited_sheng.log" 2>&1
printf 'FINITE_PROSPECTIVE_SHAPE_COMPLETE\n' > "$P/run_terminal.txt"
