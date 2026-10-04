# Finite physical realization reproduction

The full36-episode plan, capture code and independent analyzer were published
before fresh capture. Reproduction from stored data does not require CARLA:

```sh
python -m unittest discover -s experiments/ego_actuator_realization_20261004 -p 'test_*.py'
python experiments/ego_actuator_realization_20261004/verify_package.py
python experiments/ego_actuator_realization_20261004/analyze.py --capture results/ego_actuator_realization_20261004/capture --out /tmp/ego-physical-independent-analysis.json
```

Use a fresh output filename; the analyzer refuses overwriting. Compare the bytes
with `analysis_sheng.json`. All inherited logical inputs listed in freeze.json
must first be restored using their published parent restoration helpers.
Full capture JSONs are losslessly gzip archived per episode with SHA-256 and
uncompressed byte lengths in capture/outcomes.json; no capture is discarded.

To obtain new data, use an isolated output directory, matching official CARLA
0.9.15/Town10HD_Opt and the exact prepublished plan. start_carla.ps1 refuses an
existing server; stop_carla.ps1 only stops its exact PID/path/start identity.
New timings/physics outcomes are new experiments, not byte-identical published
results. Stop/packaging/report code was added after capture and is pinned by the
publication source manifest, separate from the immutable pre-capture freeze.

These are sampled physical component diagnostics. The final60-tick go prefix
does not validate arbitrary-time braking or a new scene/control risk certificate.
All goal_complete fields remain false; no recurring automation exists.
