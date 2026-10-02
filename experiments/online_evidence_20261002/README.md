# Finite online-cost optimization and fresh control audit

See the [Chinese result](../../research/online_evidence_result_20261002.md) and
[search equivalence](THEORY.md). No successful evidence-guided driving or
established MobiCom novelty is claimed.

- `PROTOCOL.md`, `profile_source.py`: six post-analysis states, unchanged source
  under inherited/one-thread numerical libraries; four repetitions per state.
- `shell_frontier.py`, `bench_frontier.py`: all 37 archived cases, 222 paired
  calls with equal joint horizons. Stops at the first unknown distance shell.
- `REPAIR_PROTOCOL.md`, `efficient_renew.py`, `bench_repair.py`: 54 paired
  repeats at three horizons, byte identity, 36 full-reference proofs with
  current-ray provenance. Receiver verification stays complete.
- `LIVE_PROTOCOL.md`, `capture.py`, `analyze.py`: ten new runs, three controlled
  corridors and modeled byte-sensitive/fixed links; 384 raw inputs and 2,651
  physics ticks audited. 163 commands occur but forward motion is negligible.
- `ACTUATOR_PROTOCOL.md`, `actuator_probe.py`, `analyze_actuator.py`: 32 separate
  component episodes, 1,880 audited ticks, automatic/manual first-gear response.
  Manual policy has not been calibrated for the evidence controller.
- `plot.py`: reproducible PNG/PDF figures; `package.py`: source/model/result
  provenance and dedicated-process cleanup checked on sheng.

Use Python 3.8+, NumPy 1.24, SciPy 1.10; plotting additionally needs Matplotlib.
From repository root, with new output directories:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m unittest discover -s experiments/online_evidence_20261002
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python experiments/online_evidence_20261002/bench_frontier.py --capture results/live_repair_closed_loop_20261001/capture --reference results/live_repair_closed_loop_20261001/frontier/analysis.json --out /tmp/mobi-online-frontier
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python experiments/online_evidence_20261002/bench_repair.py --capture results/live_repair_closed_loop_20261001/capture --out /tmp/mobi-online-repair
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python experiments/online_evidence_20261002/analyze.py --capture results/online_evidence_20261002/live --out /tmp/mobi-online-live.json
python experiments/online_evidence_20261002/analyze_actuator.py --capture results/online_evidence_20261002/actuator --live results/online_evidence_20261002/live
python experiments/online_evidence_20261002/plot.py --results results/online_evidence_20261002 --out /tmp/mobi-online-figure
(cd results/online_evidence_20261002 && sha256sum -c SHA256SUMS)
```

`analyze_actuator.py` writes its derived `analysis.json` in the input directory;
copy that component directory first if preserving archive bytes is required.
Measured timings are not WCET. The 475 ms target is fixed after previous root
analysis; the exact frontier routine was benchmarked separately, not inserted
into capture for free. The 20 Mbps channel is modeled, not measured wireless.
All motion/sensing/shape contracts remain conditional. Dropout does not create
an infinite safe state; no moving fallback was demonstrated. Six new tests
passed. Both owned servers were stopped, no recurring automation created.
