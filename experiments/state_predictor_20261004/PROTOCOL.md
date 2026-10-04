# Frozen finite development gate, before fitting/new predictions

Fit all available rows from the completed October4 pose-support batch, with
truth labels joined by id from its October3 prospective parent. Runtime inputs
are only quantized observation hulls and layout; truth is used for fitting,
development radius setting, and audit. Latest shape batch is already observed
development data, never a new independently qualified holdout.

Exactly three single-circle baselines: largest-area hull bbox center; classwise
standardized linear ridge with lambda1; ridge with individual squared features
and lambda10. No model search, hyperparameter tuning or test repair. Features
use at most three hulls sorted by area/vertex count/location. Fixed feature map,
centering and quantization are in predictor.py. No future, simulator target id,
true center or runtime label enters inference. This is standard regression,
not an asserted novel algorithm or the unimplemented multimodal candidate.

Each class uses the max exact outward integer center error across the planned
95 calibration-labelled episodes of the already-observed shape batch. Retain
capture failures and refuse empty hulls. Test-labelled60 episodes/class are
used for exploratory source-age/coverage comparison only. Explicitly retain
exclusions and overstatement. Source age uses exact strict integer dynamics,
same3D body radius,750mm query radius,5m/s+1.5t²,500mscap and±6m queries.
Compare with unchanged parent's joint source ages, not with paid grant counts.

No fresh calibration theorem, actual runtime/encoding/radio benefit, physical
safety, closed loop or MobiCom novelty follows. One terminal run on sheng,
independent integer/coverage audit, publish full model/results; no recurring job.
