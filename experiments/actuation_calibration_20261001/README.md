# Independent-episode calibration of complete sampled maneuvers

This finite experiment addresses the supplied acceleration bound falsified by
actual CARLA controls. It compares a state-conditioned predictor with a matched
constant baseline, then independently calibrates and tests joint body-extent and
recorded stopping-band predictions. It is a statistical component study, not
physical movement authorization or an evidence-guided driving result.

Read [PROTOCOL.md](PROTOCOL.md) for the frozen design and
[STATISTICAL_SCOPE.md](STATISTICAL_SCOPE.md) for the probability statement,
calibration confidence, accepted-subset caveat and continuous-time limitations.

- `capture_3d.py`: 100 training + 299 calibration + 400 test episodes, independent
  input streams, recreated vehicles, frozen relay control, all snapshots and
  actual controls retained. Unfavorable episodes are not deleted or resampled.
- `model.py`: full eight-corner body targets, persistent observed speed-band
  time, fixed OLS/constant predictors, joint maximum-score calibration and exact
  one-sided binomial confidence limits.
- `analyze.py`: reconstructs the random plan, verifies raw hashes and snapshot/
  control continuity, fits on training only, calibrates on calibration only, and
  evaluates the untouched test data. A single fixed raw-ray region is reverified
  for a clearly labeled counterfactual admission comparison.
- `test_model.py`: geometric coordinate handling, unstable stopping suffixes,
  collision/infinite outcomes, joint correction and confidence formulas.
- `audit_geometry.py`: independently composes full Euler and local-box transforms
  to recheck every recorded 3D corner; reports yaw-only extent underestimation.
- `plot_results.py`: plots held-out duration predictions and conditional gates.

## Reproduce

From repository root with Python 3.8+, NumPy and SciPy (Matplotlib for figures):

```bash
python -m unittest discover -s experiments/actuation_calibration_20261001
python experiments/actuation_calibration_20261001/analyze.py --capture results/actuation_calibration_20261001/capture --packet results/policy_runtime_20261001/binary/packets/dense_0_free_03_v0.5_h0.4.pvx --out /tmp/actuation-calibration-analysis-new
python experiments/actuation_calibration_20261001/audit_geometry.py --capture results/actuation_calibration_20261001/capture --out /tmp/actuation-geometry-audit.json
python experiments/actuation_calibration_20261001/plot_results.py --results results/actuation_calibration_20261001
```

New analysis output directories must not exist. The figure command uses the
archived `analysis/` result. Raw episodes are losslessly gzip-compressed JSON,
one fresh physical simulation episode per file. They include warm/prefix states
as well as the evaluated command and backup, so hidden selection or state reuse
can be checked.

Production environment: sheng's Ubuntu 20.04 WSL, hostname DESKTOP-UGDDO8T;
workdir `/home/sheng/mobicom2027_visibility_20261001`; Python
`/home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python`. CARLA 0.9.15 runs on
the same machine's Windows installation. Capture writes
`results/actuation_calibration_3d_capture`; the committed package archives those
identical files under `results/actuation_calibration_20261001/capture`.

For fresh capture, use an exclusive CARLA Town10HD_Opt server and run
`capture_3d.py --host HOST --out NEW_DIR`. `start_carla.ps1` refuses any existing
CARLA process, records ownership, and enforces a 30-minute maximum lifetime.
Cleanup must stop only that owned process after actor/settings restoration.
No persistent job or continuing research automation is created.

The fixed 299-score maximum supplies a *per-method* tolerance statement under
the stated iid episode law; it does not make the small sensor/actuation error
boxes in the older deterministic certificate true. A global or mean coverage
claim must not be silently promoted to conditional coverage for accepted states,
all continuously visited driving states, or an entire unlimited mission.

The initial yaw-only measurement batch is retained in `preliminary_yaw_only.tgz` and excluded from the final statistical analysis. See [POSE_ADDENDUM.md](POSE_ADDENDUM.md); repeated requests across the two captures are not independent extra samples.

## Primary result and post-analysis realization

The constant envelope has 0/400 held-out joint exceedances; the prespecified state predictor has 7/400. Both pass 400 fixed-region counterfactual gates. Keep this primary result unchanged. `realize_ticks.py` only enlarges the calibrated time to complete 50 ms ticks; this post-analysis check on the same data has zero sampled exceedances, but both median durations become 200 ms. It is not a new independent test. `test_realization.py` checks monotone enlargement. `plot_summary.py` displays both versions without replacing the frozen plotting source.

```bash
python experiments/actuation_calibration_20261001/realize_ticks.py --results results/actuation_calibration_20261001
python experiments/actuation_calibration_20261001/plot_summary.py --results results/actuation_calibration_20261001
python experiments/actuation_calibration_20261001/validate_artifact.py --results results/actuation_calibration_20261001
(cd results/actuation_calibration_20261001 && sha256sum -c SHA256SUMS)
```

Final eight-test run, source/raw verification and realization were performed on sheng. Figure rendering was local because the existing remote Matplotlib installation lacks `six`; no remote plotting environment was changed. `dependencies.json` pins repository imports, current package sources and the fixed input proof. `validation.json` is the server-produced artifact audit. The checksum manifest excludes itself and the downstream `checksum_verification.json` attestation. Reproduction regenerates environment metadata, so use a copy of the package if preserving every archived byte.
