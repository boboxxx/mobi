# Finite proof repair and causal stopping on sheng

The current-message bounds in `../tube_evidence_20261003` revalidate only old
excluded leaves. This experiment additionally checks unresolved leaves and refines
the earliest-contact portion of the pose partition. All inherited observations,
thresholds, current endpoint-ball messages and physical limitations remain fixed.

Read [PROTOCOL.md](PROTOCOL.md), [ADAPTIVE_PROTOCOL.md](ADAPTIVE_PROTOCOL.md),
[THEORY.md](THEORY.md), and the
[Chinese result](../../research/proof_repair_result_20261003.md).

## What was executed

- Fixed: 36 tasks × budgets 0/256/4096 × 3 timing repeats = 324 calls;
  108 distinct deterministic proof outputs archived.
- Adaptive: the same 36 tasks × 3 new trials = 108 calls and independently
  archived timing-dependent proof outputs. Developed after fixed outcomes;
  this is not an independent holdout or a new risk test.
- Six regression tests on both hosts. Independent fixed/adaptive audits and
  cost-summary JSON match bytewise between local and sheng.

The strong fixed direct baseline and 256-visit repair both have 7/36 positive
modeled remainders. The repair-0 wrapper has 5/36: it is not the strong baseline.
At 4096 visits, geometric lower bounds improve in 21/36, but net remainder is zero
in all tasks. Adaptive repair has 7 tasks positive in all three trials versus 6
for same-trial direct checking; only one of 108 individual outcomes changes from
zero to positive. Two bicycle tasks gain time margin; the other positive tasks
skip repair. Median adaptive receiver cost increases substantially. No real-data
upper witness was found; broad expiry gaps remain.

## Reproduce from repository root

Requirements: Python 3.8+, NumPy, SciPy, C++17 compiler; Matplotlib for plotting.
Sheng execution uses the existing Python 3.8 environment. The replay needs the
previously committed `tube_evidence`, `pose_inversion`, `terrain_score` and their
transitive artifacts. No CARLA service, GPU or new download is required.

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
c++ -O3 -std=c++17 -ffp-contract=off -shared -fPIC experiments/proof_repair_20261003/kernel.cpp -o /tmp/mobi_repair_kernel.so
c++ -O3 -std=c++17 -ffp-contract=off -shared -fPIC experiments/proof_repair_20261003/adaptive.cpp -o /tmp/mobi_adaptive_repair.so
export MOBI_REPAIR_LIBRARY=/tmp/mobi_repair_kernel.so
export MOBI_ADAPTIVE_LIBRARY=/tmp/mobi_adaptive_repair.so
python -m unittest discover -s experiments/proof_repair_20261003 -p 'test_*.py' -v

# Choose fresh output directories; do not replace the published measurements.
python experiments/proof_repair_20261003/run.py --out /tmp/mobi-proof-repair-replay
python experiments/proof_repair_20261003/run_adaptive.py --out /tmp/mobi-proof-repair-adaptive

# Audit the published sheng outputs on either host.
python experiments/proof_repair_20261003/audit.py --results results/proof_repair_20261003/replay --out /tmp/mobi-fixed-audit.json
python experiments/proof_repair_20261003/audit_adaptive.py --results results/proof_repair_20261003/adaptive --out /tmp/mobi-adaptive-audit.json
python experiments/proof_repair_20261003/summarize.py --results results/proof_repair_20261003 --out /tmp/mobi-repair-summary.json
MPLCONFIGDIR=/tmp/mobi-repair-mpl python experiments/proof_repair_20261003/plot.py --summary /tmp/mobi-repair-summary.json --out /tmp/mobi-repair-figures
python experiments/proof_repair_20261003/verify_package.py
```

The final command verifies frozen sources/results by default. `--freeze` is a
publication-maintenance option, not necessary for reproduction. Fixed trees are
deterministic; timing numbers and adaptive stopping prefixes are machine/load
dependent. Repeating the algorithm on another host need not reproduce the same
adaptive trees. The two-host byte comparison audits the *same saved sheng trees*.

## Artifacts and accounting

`results/proof_repair_20261003/replay` contains fixed trees, timing triples and
producer hashes; `adaptive` contains every individual trial. Independent audit
logs, test logs, environment, summaries, figure, source manifest and result hashes
are retained alongside them. No failed or zero-result tasks are removed.

Source creation uses prior worst-of-five measurements. Fixed rows charge worst
of three current encoding-plus-receiver times; adaptive rows charge each actual
trial. Both include modeled 20Mbps serialization, 20ms propagation, 20ms clock
and 200ms action reserve. The old proof, reference transport/coding and restore
cost are paid; 0.694–14.503s fits each saved 20.5s gap. Query/radius choices are
separate tasks, not a simultaneous deployment workload or an oracle selector.

Audit tree export, serialization, NPZ output and native context destruction are
after the measured online authority interval. The research wrapper returns after
that logging; full integrated API return latency has not been measured. Deployment
would need a separate early-result path or asynchronous logging, and remeasurement. Sensor/callback latency, real links, WCET, physical noise,
scene inventory and trajectory coverage remain unvalidated. Model-positive time
does not authorize driving. See the theory for the conditional guarantee and
the unresolved distinction between information loss and computational loss.
