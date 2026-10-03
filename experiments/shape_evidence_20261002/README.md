# Shape evidence, family calibration and conditional expiry

Executed on sheng / Windows CARLA 0.9.15 on **2026-10-03**. The directory date
reflects the previous day's prototype; captures are genuinely new October 3 data.
No recurring automation was created. The two owned CARLA processes were stopped
after finite captures; actors/sensors were destroyed and prior world settings restored.

- [Frozen initial protocol](PROTOCOL.md): 234 scheduled episodes, 458 actual frames.
- [Fresh follow-up protocol](availability_followup/PROTOCOL.md): 39 episodes, 70 frames.
- [Derivation and exact scope](THEORY.md), [primary reading](READING.md).
- [Chinese report](../../research/shape_evidence_result_20261003.md).
- [Machine-readable summary](../../results/shape_evidence_20261002/summary.json).

`model.py` scores only observed ray coordinates, origin and an explicit box
hypothesis. IDs are audit labels. `evaluate.py` uses ground-truth boxes as test
targets, not a deployable detector. `availability.py` refuses the entire declared
family if an input is missing. `lifetime.py` computes tight age boundaries ONLY
after a complete calibrated state set and motion model have been established by
the caller; this capture does not establish that interface.

## Reproduce without a CARLA server

From repository root, with NumPy/SciPy (Matplotlib only for plot):

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m unittest discover -s experiments/shape_evidence_20261002 -p 'test_*.py' -v
python experiments/shape_evidence_20261002/evaluate.py --results results/shape_evidence_20261002 --label replay
python experiments/shape_evidence_20261002/audit.py --results results/shape_evidence_20261002 --out /tmp/shape-audit.json
python experiments/shape_evidence_20261002/evaluate.py --results results/shape_evidence_20261002/availability_followup --availability-followup --label replay
python experiments/shape_evidence_20261002/audit_followup.py --results results/shape_evidence_20261002/availability_followup --out /tmp/shape-followup-audit.json
python experiments/shape_evidence_20261002/check_lifetime.py --out /tmp/shape-lifetime.json
python experiments/shape_evidence_20261002/summarize.py --results results/shape_evidence_20261002
python experiments/shape_evidence_20261002/plot.py --results results/shape_evidence_20261002
```

Initial and follow-up audit files import neither the tested score nor its summary
implementation. They independently intersect six box faces, reconstruct sensor
Euler transforms, verify raw hashes/labels, regenerate random draws and recompute
quantiles. The follow-up audit is a separate fixed copy with its 39-episode law
and missing-episode score zero; the original audit remains unchanged.

## New captures, only when intentionally requested

The archived plan files are frozen, not new held-out draws on rerun. Install the
matching CARLA 0.9.15 Python client. The provided PowerShell launchers refuse to
start alongside an existing CARLA process, record their own PID and impose a
30-minute cap. Capture scripts refuse pre-existing output directories and require
an initially empty actor/sensor world. Use a new output path to preserve archives.
Stop only the recorded, executable-verified owned PID after capture. Existing
capture records contain failures; do not replace them to improve statistics.

The actual WSL runtime used was
`/home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python`, with repository
`/home/sheng/mobicom2027_visibility_20261001`. See environment_sheng.json for
library/runtime versions. Analysis/audit JSON match bytewise between sheng and
local; machine CPU timing and log output are naturally different.

## Interpretation

The initial full-only threshold transfer is an intentionally mismatched
communication-budget baseline, not a state-of-the-art calibrated baseline.
Joint-family calibration is established methodology. The no-penetration baseline
q=0 is a diagnostic of an invalid opaque-box premise. Neither baseline comparison
establishes algorithmic novelty. Unknown-object inventory, continuous pose-set
coverage, physical sensor/dynamics calibration, temporal risk accounting, real
links and useful closed-loop driving remain required before a stronger claim.

The initial pedestrian q=1 failure remains in the archive. A fresh experiment
tests explicit abstention; the original test set is not reused as validation.
Missing-input protection was additionally hardened against partially present
families and separately tested; replay confirms unchanged outputs on these
complete-or-missing captures. The previous physical eligibility gate still does
not authorize real actions. This package does not silently enable it.
