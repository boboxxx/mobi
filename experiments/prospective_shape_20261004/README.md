# Fresh finite qualification of a fixed shape-set predictor

Design and score were chosen using development data, then frozen before this
930-plan new capture. Read PROTOCOL.md and THEORY.md. New independent episode
draws use seeds2026103100/2026103200+class. Existing scene/maps/known classes stay
controlled; different seeds alone do not prove the iid assumption in deployment.

Near-upright padding is a predictor feature; the experiment directly calibrates
truth membership, even when that feature is physically false. Calibration is
whole-episode and joint across source/model outputs. No hidden pose rejection
or test-fitted correction. The calibration_frozen.json receipt is written before
the producer opens ANY test point cloud. Runtime uses XYZ/class/setup only.

Three new direct-membership/missing-output tests and the9 inherited geometric/
wire tests cover separate invariants. smoke_before_capture.py uses12 OLD
development frames and checks48 real encodings/decodings; that preflight is
clearly labeled and does not enter fresh calibration/test metrics.

The runner is finite: capture<=3300s; owned CARLA server<=60min. Scene settings
and owned actors/sensors are cleaned, then the server is ownership-checked and
stopped before paid offline evaluation. No recurring task or monitor exists.
If Windows/WSL interop prevents owned stopping, retain its stop log and stop
through direct Windows SSH with the same ownership script, then resume the
original evaluation once; do NOT recapture or change the plan/model/threshold.
Live-session observation expiry alone is not a failed capture.

Source profile uses the actual stride-four copy measured during capture, then
the three complete source jobs. Receivers pay complete actual decoders; RAW
uses the same exact hull optimization. Only measured observed maxima, not WCET.
Cold means shared-context transfer with an initialized service. Link/actuation
are modeled three-FIFO traces, not real-radio or ego-driving evaluation.

For archived complete results, run from the repository root with NumPy/SciPy:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m unittest discover -s experiments/prospective_shape_20261004 -p 'test_*.py' -v
python -m unittest discover -s experiments/pose_support_20261004 -p 'test_*.py' -v
python experiments/prospective_shape_20261004/audit.py --results results/prospective_shape_20261004 --out results/prospective_shape_20261004/audit_local.json
python experiments/prospective_shape_20261004/summarize.py --results results/prospective_shape_20261004 --out results/prospective_shape_20261004/summary_local.json
```

An initialized native library built from the pinned body_expiry_20261004
proposer.cpp is needed for producer/runtime tests; the independent auditor does
not load it. Sheng verifies that library against its archived build receipt.
Audits compare deterministic archived output bytes across hosts; costs are the
actual archived sheng measurements. Do not reinterpret retiming as identical.

The max95 coverage theorem has fixed-law whole-episode conditions. Test upper
bounds, center coverage, motion/corner samples and oracle gaps must be reported
separately, including failures. Unknown inventory, continuous physical/ray-mesh
optimum, novel communication selection and live ego utility are still outside
what this batch alone can establish. Full research completion remains unproven.
