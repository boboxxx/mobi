# Finite complete-yaw support and paid expiry study

Read PROTOCOL.md, THEORY.md and the Chinese result in
research/pose_support_result_20261004.md. Primary sources stayed unchanged after
freeze. RAW_OPTIMIZATION_PROTOCOL.md is a separately frozen exact-reduction
follow-up; diagnose.py and tilt_prior_lower_bound.py are post-result diagnostics.

The sheng runner completed all5304 reused source frames,2076 paid test frames,
5760 primary traces and1440 optimized-RAW traces. All actual new hull wires are
under results/pose_support_20261004/messages. Byte-identical RAW wires remain
at the pinned parent results/prospective_expiry_20261003 paths; do not duplicate
them or transfer the old transport header's risk claim to this new model.

An initialized exact native hull/ball proposer is inherited from
experiments/body_expiry_20261004/proposer.cpp and its kernel wrapper. On Linux:

```sh
g++ -O3 -std=c++17 -shared -fPIC experiments/body_expiry_20261004/proposer.cpp -o experiments/body_expiry_20261004/proposer.so
```

The sheng run validated that binary against the archived parent native-build
receipt before execution. Auditors do not load the production native library.
With Python, NumPy, SciPy available, run from the repository root:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m unittest discover -s experiments/pose_support_20261004 -p 'test_*.py' -v
python experiments/pose_support_20261004/audit.py --results results/pose_support_20261004 --out results/pose_support_20261004/audit_local.json
python experiments/pose_support_20261004/summarize.py --results results/pose_support_20261004 --out results/pose_support_20261004/summary_local.json
python experiments/pose_support_20261004/audit_raw_optimized.py --results results/pose_support_20261004 --out results/pose_support_20261004/raw_optimized_audit_local.json
python experiments/pose_support_20261004/diagnose.py --results results/pose_support_20261004 --out results/pose_support_20261004/diagnostic_local.json
python experiments/pose_support_20261004/tilt_prior_lower_bound.py --results results/pose_support_20261004 --out results/pose_support_20261004/tilt_prior_lower_bound_local.json
python experiments/pose_support_20261004/verify_package.py
```

Deterministic archived outputs compare bytewise across hosts; measured timings
are sheng observations. Retiming on another host changes costs and is not an
identical experiment. Source producers refuse to overwrite accepted analysis.
For a genuinely new run, prepare a distinct output directory with matching
freeze/input provenance rather than bypassing existing-output checks.

Nine tests cover partial-view bias, unknown yaw/cell boundaries/tilt, exact hull
projection, integer calibration threshold, rational closest points, missing vs
empty sets, exact binary radius, actual RAW/hull decoding and context/checksum
failure. Whole-corpus audit additionally checks the optimized RAW equivalence.

Primary distance/expiry precision is a declared outer-model result.72 source
frames violate the sufficient tilt prior, with exact any-yaw lower witnesses.
Reused-data zero center exclusions and sampled-grid zero conflicts are not new
risk qualification. Known classes/inventory, motion/shape contracts and service
initialization remain explicit. No simulator, radio/ego experiment or recurring
research job ran in this study. The full research goal remains incomplete.
