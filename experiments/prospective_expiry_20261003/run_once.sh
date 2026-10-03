#!/usr/bin/env bash
set -eu
cd /home/sheng/mobicom2027_visibility_20261001
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
PY=/home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python
E=experiments/prospective_expiry_20261003
P=results/prospective_expiry_20261003
stop_owned() { powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'C:\Users\Administrator\mobi-prospective-stop.ps1' </dev/null > "$P/stop.log" 2>&1; cp /mnt/c/Users/Administrator/mobi-prospective-expiry-stopped.json "$P/server_stopped.json"; }
trap stop_owned EXIT
$PY - <<'PY'
import carla,time
for i in range(18):
 try:
  c=carla.Client('100.109.48.32',2000);c.set_timeout(4);w=c.get_world();assert c.get_server_version()=='0.9.15';print('server ready',flush=True);break
 except Exception:
  if i==17:raise
  time.sleep(2)
PY
cp /mnt/c/Users/Administrator/mobi-prospective-expiry-server.json "$P/server_started.json"
timeout --signal=INT 3300 "$PY" "$E/capture.py" --out "$P/capture" > "$P/capture.log" 2>&1
stop_owned
trap - EXIT
$PY $E/evaluate.py --results $P > $P/evaluate_sheng.log 2>&1
$PY $E/audit.py --results $P --out $P/audit_sheng.json > $P/audit_sheng.log 2>&1
$PY $E/summarize.py --results $P --out $P/summary_sheng.json > $P/summary_sheng.log 2>&1
$PY $E/action_functional.py --results $P > $P/action_functional_sheng.log 2>&1
$PY $E/action_functional_audit.py --results $P --out $P/action_functional_audit_sheng.json > $P/action_functional_audit_sheng.log 2>&1
$PY $E/action_functional_summary.py --results $P --out $P/action_functional_summary_sheng.json > $P/action_functional_summary_sheng.log 2>&1
$PY $E/support_audit.py --results $P --out $P/support_audit_sheng.json > $P/support_audit_sheng.log 2>&1
$PY -m unittest discover -s $E -p 'test_*.py' -v > $P/tests_sheng.txt 2>&1
printf 'complete\n' > "$P/run_terminal.txt"
