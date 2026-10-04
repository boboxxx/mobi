# Reproduce the finite component-expiry experiment

Run commands from the repository root. The experiment is a registered single-target
CARLA fixture, not an ego-controller or a radio test. The independent run consists
of 1,560 calibration, 600 policy-certification and 360 held-out test episodes.
The statistical unit is a complete episode. Failed episodes are retained.

## Restore published evidence and check it

Use Python with NumPy and SciPy and a C++17 compiler. The reference sheng execution
uses Python 3.8, NumPy 1.24.4 and SciPy 1.10.1. Replaying the independent audit does
not require a running CARLA server. Native geometry must be built on each host:

```sh
python experiments/prospective_shape_20261004/prepare_archive.py --restore
python experiments/prospective_hypotheses_20261004/prepare_archive.py --restore
python experiments/prospective_component_20261004/restore_results.py
c++ -std=c++17 -O3 -shared -fPIC experiments/body_expiry_20261004/proposer.cpp -o experiments/body_expiry_20261004/proposer.so
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python experiments/prospective_component_20261004/audit.py --out /tmp/mobi-component-replay-audit.json
```

Compare the reconstructed audit with `results/prospective_component_20261004/audit_sheng.json`.
The independent audit checks raw XYZ geometry, calibration scores, packet bytes,
actual recorded processing fees, FIFO traces, source timestamps and the selected
query certificate. The source predictor is shared frozen code; the audit is not an
independent implementation of the trained model.

Large logical JSON files are losslessly archived. Both archive manifests record
the original byte length and SHA-256, and restoration verifies these bytes before
renaming a new file. The plain restored files are ignored by Git. Raw clouds,
actual messages, failed-episode records and timing measurements remain published.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python experiments/prospective_component_20261004/verify_package.py --out /tmp/mobi-component-package-check.json
```

This checks the immutable source closure, logical archives, artifact manifest,
stage ordering, owned-server cleanup and agreement of both host audits. Existing
published outputs must not be overwritten. To reconstruct plots, copy the result
tree to a separate checkout and use `plot.py`; the prescribed summary requires an
explicit fresh `--out` path when `summary_sheng.json` already exists.

## Understand the claim before using a certificate

`PROTOCOL.md` fixes the scene grid, support guard, score components, query schedule,
service policies and confidence budgets. `research/component_expiry_proof_20261004.md`
states the geometric implication and its statistical assumptions. Calibration
controls an episode-level marginal exclusion event. Policy certification separately
tests failure conditional on authorization for a uniformly preselected scheduled
query under the declared joint scene/service law. It does not certify every location
or every supported/fallback subgroup individually.

Evidence expires relative to its source timestamp. Network receipt or retransmission
does not renew it. Cold service means paying registered context initialization;
models and the background frontend are already initialized. Three measured processing
repetitions do not establish a worst-case execution time or IID service timing.
Known actor inventory, body bounds and motion bounds are essential assumptions.
No unknown-actor completeness or real-traffic safety certificate is provided.

## Original finite collection

The Windows launcher and WSL scripts in this directory describe the original sheng
run. They refuse conflicting CARLA ownership and verify the frozen source files.
The launcher starts CARLA 0.9.15 at the specified Windows installation. Capture and
evaluation are finite sequential stages, with no replacements or recurring jobs.
`run_capture.sh` stops only the process whose PID, executable and start time match
its ownership receipt. Do not rerun collection into the published result directory.
New collection would be a new experiment with a new publication and independent
data; it cannot reproduce the exact recorded CPU timings from this experiment.
