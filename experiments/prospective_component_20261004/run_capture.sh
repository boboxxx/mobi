#!/usr/bin/env bash
set -eu
cd /home/sheng/mobicom2027_visibility_20261001
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
TASK_PY=/home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python
E=experiments/prospective_component_20261004
P=results/prospective_component_20261004
stop_owned() {
 powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'C:\Users\Administrator\mobi-prospective-component-stop.ps1' </dev/null > "$P/stop.log" 2>&1
 cp /mnt/c/Users/Administrator/mobi-prospective-component-stopped.json "$P/server_stopped.json"
}
trap stop_owned EXIT
"$TASK_PY" - <<'PY'
import hashlib,json
from pathlib import Path
f=json.loads(Path('experiments/prospective_component_20261004/freeze.json').read_bytes())
for section in ('sources','inputs'):
 for n,h in f[section].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h,n
assert not Path('results/prospective_component_20261004/capture').exists()
print('FRESH_COMPONENT_FREEZE_VALIDATED',flush=True)
PY
"$TASK_PY" -m unittest discover -s "$E" -p 'test_*.py' > "$P/tests_before_capture_sheng.log" 2>&1
"$TASK_PY" - <<'PY'
import carla,time
for i in range(18):
 try:
  c=carla.Client('100.109.48.32',2000);c.set_timeout(4);w=c.get_world();assert c.get_server_version()=='0.9.15';print('server ready',flush=True);break
 except Exception:
  if i==17:raise
  time.sleep(2)
PY
cp /mnt/c/Users/Administrator/mobi-prospective-component-server.json "$P/server_started.json"
timeout --signal=INT --kill-after=40 9000 "$TASK_PY" "$E/capture.py" --out "$P/capture" > "$P/capture.log" 2>&1
printf 'FRESH_COMPONENT_CAPTURE_COMPLETE\n' > "$P/capture_terminal.txt"
stop_owned
trap - EXIT
printf 'FINITE_COMPONENT_CAPTURE_WRAPPER_COMPLETE\n'
