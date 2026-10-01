> **Superseded interpretation (2026-10-01):** The channel-aware greedy audit eliminates the earlier joint-selector advantage. This is a historical experiment package; see the [revision](../../research/update_20261001.md) for baseline, RNG, conditional-marginal, and sensor-validity limitations.

# Finite decision-sufficient V2X experiment

This directory contains the finite mechanism, robustness, and CARLA closed-loop experiment used in the 2026-09-26 feasibility decision. The frozen design is in `PROTOCOL.md`. The scripts do not create a daemon, recurring automation, or continuous research loop.

## Main result

The broad hypothesis that set utility alone beats a strong coverage-aware selector was rejected under independent delivery. The narrower hypothesis was supported: when message arrivals are not factorizable because same-channel transmissions contend, explicitly modeling joint arrival improves decision progress. A 140-episode CARLA semantic-LiDAR closed loop reproduced this directional effect in a controlled corridor.

These methods are transparent mechanism-level baselines. They are not official reproductions of named systems from the literature.

## Files

- `core.py`: evidence, scheduler, channel, and finite mechanism simulator.
- `run_mechanism_sweep.py`: six network models, five scenarios, seven methods, 1,000 paired seeds per cell.
- `analyze.py`, `plot.py`: mechanism summaries, paired bootstrap intervals, and plots.
- `run_robustness.py`, `analyze_robustness.py`, `plot_robustness.py`: four semantic-noise settings, 500 paired seeds per cell, plus scheduler latency.
- `run_carla_closed_loop.py`: CARLA 0.9.15 semantic-LiDAR closed loop.
- `analyze_carla.py`, `plot_carla.py`: CARLA integrity checks, paired comparisons, and plots.
- `test_core.py`: seven mechanism tests.

## Local reproduction

Run from this directory so `core.py` is importable:

```bash
python3 -m unittest test_core.py
python3 run_mechanism_sweep.py --seeds 1000 --out ../../results/carla_v2x_full/mechanism_reproduction
python3 analyze.py ../../results/carla_v2x_full/mechanism_reproduction/per_episode.csv --out ../../results/carla_v2x_full/mechanism_reproduction/analysis
MPLBACKEND=Agg python3 plot.py ../../results/carla_v2x_full/mechanism_reproduction/analysis --out ../../results/carla_v2x_full/mechanism_reproduction/analysis/plots
python3 run_robustness.py --seeds 500 --out ../../results/carla_v2x_full/robustness_reproduction
python3 analyze_robustness.py ../../results/carla_v2x_full/robustness_reproduction
MPLBACKEND=Agg python3 plot_robustness.py ../../results/carla_v2x_full/robustness_reproduction
```

The archived final outputs use `mechanism_v2`; the earlier `mechanism` directory is retained for audit because it preceded the correction to one-cycle delivery semantics.

## CARLA reproduction

The final run used:

- CARLA server 0.9.15 on Windows at `100.109.48.32:2000`.
- Linux CARLA client 0.9.15 on `sheng`.
- `Town10HD_Opt`, synchronous 20 Hz simulation, 5 s per episode.
- Actual CARLA semantic-LiDAR observations from two roadside regions.
- `independent` and `contention` link models; `free` and `hazard_a` scenarios; seven methods; five paired seeds: 140 episodes.

Example client command on `sheng`, after starting the existing Windows CARLA server:

```bash
/home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python run_carla_closed_loop.py \
  --host 100.109.48.32 --port 2000 --seeds 5 --seconds 5 \
  --out /home/sheng/mobicom2027_v2x_full_20260926/results/main140
```

Analyze and plot with a Python environment containing NumPy and Matplotlib:

```bash
python3 analyze_carla.py RESULTS/main140 --out RESULTS/main140/analysis
MPLBACKEND=Agg python3 plot_carla.py RESULTS/main140/analysis --out RESULTS/main140/analysis/plots
```

The final script hashes recorded in the CARLA manifest are:

```text
run_carla_closed_loop.py  511c6da017381349b3fd6362ee88a69641c0abeddacc933fdb291337e051ea74
core.py                   c5e3fa967b212678b69a0d05da70936c48e15057d3eb21efb71b8b3847425dc5
```

## Integrity and interpretation

The validator requires all 140 episodes, completed status, zero stale sensor frames, free observations in the free scenario, and all 70 hazard traces to show occupied A before 2.5 s and free A after 2.6 s. These checks passed. Its separate `same_script_hash` flag only checks one manifest value and cannot establish per-episode source identity; archived source hashes match the manifest, but this is a narrower check. Zero recorded collisions in this small controlled experiment is an observation, not a collision-probability estimate.

The experiment uses a controlled straight corridor, two logical providers derived from each regional sensor, a software link model rather than measured PC5, and a simple rule-based controller. It does not establish natural-scene safety or a complete MobiCom evaluation.

## Results

- Mechanism: `../../results/carla_v2x_full/mechanism_v2/`
- Robustness: `../../results/carla_v2x_full/robustness/`
- CARLA: `../../results/carla_v2x_full/carla_main140/`
- Cleanup audit: `../../results/carla_v2x_full/cleanup.json`
- Scientific interpretation: `../../research/full_experiment_result_20260926.md`
