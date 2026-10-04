# Independent qualification of expiry from incomplete observations

This finite experiment uses a model fixed on earlier development data, then a
new CARLA calibration/test batch captured on sheng. It tests whether local
center hypotheses reduce expiry loss after whole-episode calibration and
whether the gain survives measured computation and communication costs.

The result report is
[`research/prospective_hypotheses_result_20261004.md`](../../research/prospective_hypotheses_result_20261004.md).
The conditional geometry argument, identifiability limit, sample complexity and
authorization-selection limitation are in
[`research/expiry_incomplete_observation_reasoning_20261004.md`](../../research/expiry_incomplete_observation_reasoning_20261004.md).
Primary-paper reading scope is recorded in `READING_UPDATE.md`.

## Preregistration and scope

* `caf2129d4ed494bf352ed9db39d6230bdd6b86ab`: capture, models, scores and plan
  before fresh capture.
* `ae38d1eceea0a0445d7ab7907b3dbe0a0819bfb0`: qualification and measured service
  implementation before fresh calibration, test inference and profiling.
* `cf6bd49926fe7460a79f0765a3569265f2891b5c`: minimum deadline registration
  sensitivity before its new setup/receiver profiles.

These freezes remain unchanged. Thresholds, predictors, scales and guards were
not repaired using fresh test failures. The four families are joint body/pose,
fixed ridge, guarded local mean and guarded local modes. Plain/max/clip geometry
variants share their family's coverage event.

There are six registered actor classes, two fixed RSU layouts, one moving actor,
six partial LiDAR sources per captured episode and two registered queries. The
plan contains 125 calibration and 60 test episodes per class. Failed capture
episodes are retained, receive no new evidence and are not replaced. This is a
static-RSU trace experiment with measured services and replayed FIFO links;
it does not implement live ego feedback, measured wireless links or an unknown
scene's complete actor inventory.

## Replay published results

Run from the repository root. Python, NumPy, SciPy and a C++17 compiler are required. The frozen
dependencies in the manifests must be present, including the earlier model and
development inputs. Large logical JSON files are stored as lossless gzip files;
restore the earlier shape analysis with its own archive script if necessary.

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
c++ -std=c++17 -O3 -shared -fPIC experiments/body_expiry_20261004/proposer.cpp -o experiments/body_expiry_20261004/proposer.so
python experiments/prospective_shape_20261004/prepare_archive.py --restore
python experiments/prospective_hypotheses_20261004/prepare_archive.py --restore
python experiments/prospective_hypotheses_20261004/audit.py --qualification-only --out /tmp/hypotheses-qualification-audit.json
python experiments/prospective_hypotheses_20261004/audit.py --out /tmp/hypotheses-paid-audit.json
python experiments/prospective_hypotheses_20261004/audit_minimal.py --out /tmp/hypotheses-minimum-audit.json
python experiments/prospective_hypotheses_20261004/verify_package.py
```

The audit uses independent raster, hull, calibration, integer geometry, wire,
FIFO and saved-future-grid checks. Frozen predictor replay is shared and is
explicitly not an independent reimplementation of the learned model. Original
sheng and local audit files allow exact byte comparisons. The complete artifact
manifest pins raw clouds, ground truth, capture failures, actual messages,
profiles, calibration receipts, logs, summaries and figures. Source and input
manifests pin the code and models without depending on rolling project prose.
The native library is built for the replay host from the frozen C++ source;
the sheng binary hash is an execution receipt, not a portable-binary requirement.

`run_capture.sh` and `run_evaluation.sh` document the finite sheng execution.
Replaying audits requires no CARLA server. Repeated timing need not reproduce
the saved costs, and measured maxima are not worst-case execution bounds.

## Interpretation

Coverage of the registered center and the declared body/motion bounds imply a
source-relative expiry through conservative integer geometry. Receipt time
does not renew evidence. Under the fixed-law iid whole-episode assumption, the
max125 calibration rule supports a 5% episode exclusion-risk tolerance with a
joint calibration confidence lower bound of about 96.06% over 24 class/family
events. This is neither authorization-conditional coverage nor a road-safety
guarantee.

Local hypotheses reduce the measured P95 expiry gap for several classes, but
the best family varies by class and the motorcycle remains conservative.
Observed center exclusions are retained even when fixed-query expiry and
saved-grid checks report no overstatement/conflict. The same-family direct
deadline baseline obtains almost identical paid authorization totals. The
batch does not establish a general solution or MobiCom novelty.
