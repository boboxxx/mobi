# Finite dynamic causal-frame evidence study

Read PROTOCOL.md, THEORY.md, TUBE_PROTOCOL.md, TUBE_THEORY.md FUNCTIONAL_PROTOCOL.md, ACTION_FUNCTIONAL_PROTOCOL.md and TIMING_NOTE.md.
The frozen930-episode plan contains95 calibration and60 test sequences for each
of six known classes. Six retained source scans (two simultaneous RSUs at steps
0,5,10) and21 physical actor snapshots per successful episode. The frontend uses
XYZ only; labels enter offline calibration and posthoc evaluation.

Every scan independently produces its own state set or refusal. Source-aged
expiry never waits for another view/future frame and never refreshes at reception.
The finite prediction-tube follow-up calibrates all future50ms snapshot residuals
up to500ms per source, using current XYZ centers only at runtime. Its linear3m/s
expansion is statistically calibrated, not an asserted physical speed limit.

## Reproduce saved evidence

Python3.8+, NumPy, SciPy. From repository root:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m unittest discover -s experiments/causal_state_20261003 -p 'test_*.py' -v
python experiments/causal_state_20261003/verify_package.py
python experiments/causal_state_20261003/audit.py --results results/causal_state_20261003 --out /tmp/causal-audit.json
python experiments/causal_state_20261003/summarize.py --results results/causal_state_20261003 --out /tmp/causal-summary.json
python experiments/causal_state_20261003/tube_audit.py --results results/causal_state_20261003 --out /tmp/causal-tube-audit.json
python experiments/causal_state_20261003/tube_summary.py --results results/causal_state_20261003 --out /tmp/causal-tube-summary.json
python experiments/causal_state_20261003/support_audit.py --results results/causal_state_20261003 --out /tmp/causal-support-audit.json
python experiments/causal_state_20261003/functional_audit.py --results results/causal_state_20261003 --out /tmp/causal-functional-audit.json
python experiments/causal_state_20261003/functional_summary.py --results results/causal_state_20261003 --out /tmp/causal-functional-summary.json
python experiments/causal_state_20261003/action_functional_audit.py --results results/causal_state_20261003 --out /tmp/causal-action-audit.json
python experiments/causal_state_20261003/action_functional_summary.py --results results/causal_state_20261003 --out /tmp/causal-action-summary.json
```

Compare these deterministic audits/summaries to the *_sheng.json outputs. The
primary raw auditor reconstructs raster components independently, all archived
sampled observations, packet payloads, quantiles, exact contact and all queues.
The tube auditor uses the validated primary payloads and independently rebuilds
scalar future residuals and linear contact. Timing varies by host/load; do not
expect remeasured evaluation JSON to match. Production evaluate.py/tube.py create
new message directories and refuse to overwrite existing ones; use a complete
separate result copy for remeasurement. --freeze is publication only.

## Interpretation

Six max95 calibration statistics provide a fixed-calibration tolerance statement
with joint confidence lower1-6*.95^95, under iid episodes and this finite known-
class sampling law. It is conditional on those assumptions, not an empirical
proof of iid deployment, conditional availability risk, unknown-scene coverage or
indefinite/continuous-time safety. All scheduled failed spawns remain in test
and query denominators. Query decisions occur at16 ticks, two fixed locations:
32 correlated outcomes per scheduled test,11520 per method/link preset.

Sender CPU, FIFO serialization and receiver CPU each share the simultaneous-view
jobs. All methods pay source-buffer selection, XYZ assembly, own source/receiver
measured maxima and modeled link/clock/action terms. Strong lossless-center and
full-sampled-XYZ baselines reconstruct precisely the SAME quantized center set,
radius and horizon. Fixed200 is a conservative diagnostic that is always shorter
than220ms reserve, not a competitive main baseline. CARLA simulation timestamps
and measured wall durations are combined in a modeled causal trace; no live
physical link, ego driver or continuous physical safety is claimed.

Only every fourth original return is archived; all stored points are audited.
Source sampling timing uses a buffer-layout fixture with zero-filled unused
slots, which are not new evidence. Pre-evaluation serializer/empty-array/sampling
fixes and old freeze sources remain in this directory. A finite owned-server
extension accommodated the whole schedule; cleanup/stop receipts are retained.
No recurring research loop. Reusing this plan is not a new independent holdout.

The task-functional and action-eligible successor reuse the current experiment
data after primary results were inspected, so they are exploratory development
comparisons. Their stored primary messages remain byte-identical. A separate
prospective_expiry_20261003 study freezes the candidate and new seeds before
new capture. Nine deterministic audit/summary pairs are checked for this package.
Unfiltered task calibration loses total grants; its successor improves modeled
paid utility but retains one actual observed occupied Sprinter grant. Do not
claim safety, untouched validation or MobiCom novelty from that successor.
