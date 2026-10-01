# Renewal candidate validation on sheng

This is a finite negative-result package. The candidate three-step scheduler does not outperform the generic stationary reference in the tested configurations. Simple group refresh matches the core two-region result. The real CARLA sensor gate fails at the preselected primary resolution in one of two views. See the [full interpretation](../../research/renewal_sheng_result_20261001.md); do not describe it as a successful new driving algorithm.

## Environment and reproducibility

Production ran in `/home/sheng/mobicom2027_renewal_20261001` on the existing sheng WSL host `DESKTOP-UGDDO8T`. Python 3.8.10 and NumPy 1.24.4 were already installed. CARLA client/server were 0.9.15. The Windows server used the existing Shipping executable with offscreen low-quality rendering. No dependency installation or persistent scheduled job was added.

From the repository root, using Python with NumPy (and Matplotlib for plots):

```bash
python3 -m unittest discover -s experiments/renewal_sheng_20261001 -p 'test_*.py'
python3 experiments/renewal_sheng_20261001/run_suite.py --seeds 500 --decisions 60 --out /tmp/renewal_main_reproduction
python3 experiments/renewal_sheng_20261001/run_stationary.py --seeds 500 --out /tmp/renewal_stationary_reproduction
MPLBACKEND=Agg python3 experiments/renewal_sheng_20261001/analyze.py results/renewal_sheng_20261001
```

Output directories must not exist. The plot command rebuilds comparisons/figures from the archived CSVs. To analyze new outputs, place them under a common root as `main38500` and `stationary5500`. Timing is machine dependent. `stationary5500/models.csv` uses the original name `cold_s`, but repeated model parameters can hit a cache; not every row is a cold construction time. Episode timing also includes cached decisions and must not be treated as end-to-end system timing.

Run `python3 experiments/renewal_sheng_20261001/validate.py` to check archived hashes, episode counts, sensor frames and cleanup records. The first transfer archive included macOS AppleDouble `._*.py` metadata; those entries remain in the original manifest for provenance but are not Python modules and are excluded explicitly from executable-source checks. Actual executed source hashes match. Metadata forks are not uploaded to Git.

## Code and scope

- `scheduler.py`: EDF, normalized age, periodic/group refresh, deterministic/stochastic finite-horizon references.
- `stationary_reference.py`: generic discounted value iteration, gamma 0.99; small state spaces only.
- `certificate.py`: 1D reachability lifetime under externally supplied correct coverage and motion bounds. No new safety theorem.
- `run_suite.py`: 38,500 synthetic episodes and 10,000 bounded kinematic stress samples.
- `run_stationary.py`: 5,500 post-diagnostic reference episodes, with original run preserved.
- `carla_coverage_gate.py`: actual point-cloud prerequisite audit. 80 measured world frames, 320 rows across cell sizes/thinning factors. No driving controller.
- `test_renewal.py`, `test_stationary.py`: ten tests, including exhaustive checks and rolling-horizon postponement regression.
- `analyze.py`: paired bootstrap comparisons and exportable scientific plots.

The main suite uses correct-free observations and supplied lifetimes; all methods see identical inputs, and future outcomes are hidden. False-validity metrics use separate uncapped true ages. Modeled communication cost is 72 bytes per attempted message, explicitly a model rather than a measured protocol. No claim of official AoUI/C-MASS/TAMP reproduction is made.

## CARLA prerequisite audit

With the matching server running and no existing vehicles:

```bash
python3 experiments/renewal_sheng_20261001/carla_coverage_gate.py --host 100.109.48.32 --frames 20 --out /tmp/renewal_carla_gate
```

All created actors are destroyed and the original world settings restored in `finally`. The warm-up may skip an initial missing subscription frame; measured frames must match the requested world frame exactly. Raw XYZ samples are stored as compressed NumPy arrays. Semantic LiDAR is an idealized simulator sensor. Ground endpoint coverage is a necessary diagnostic for this representation, not proof of continuous free volume.

`start_carla.ps1` uses a direct process API (`UseShellExecute=false`) because Shell launching waited for interaction on the existing downloaded executable. It leaves file trust markings and permanent security settings unchanged. If launching through SSH, keep the launching session alive while using CARLA; this run found that a short-lived session did not keep the server usable. Only close the process you created, identified by the recorded PID and executable. No task scheduler is required.

The primary grid remains 0.5 m. A coarse 1 m sensitivity result must not be substituted after seeing the outcome. A failed gate blocks promotion of these certificates to driving claims; it does not prove alternative perception representations are impossible.
