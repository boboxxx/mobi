# Exploratory task-functional expiry calibration

This follow-up is proposed after inspecting the primary current-center max95
radii and its three test exclusions, but before inspecting tube outputs or
computing task-contact scores. Existing calibration/test data are reused; these
are development comparisons, not a new untouched holdout or deployment test.
The frontend, complete saved messages, sender timing, two queries, queues,
clock/action budget and all scheduled denominators remain fixed.

Use current quantized XYZ candidate centers and fixed8mm radius plus known body
and .75m task disc. Base expiry H_s,q is exact linear3m/s contact capped500ms.
No true current/future coordinates or semantic IDs enter the receiver. For offline
calibration only, G_s,q is one microsecond before the first observed future50ms
snapshot in steps s..s+10 whose true center body disc touches the query; if no
contact is observed, G=500000us. Source/future times use floor(timestamp*1e6).
An already occupied source has G=-1. No continuous safety interpolation follows.
Episode score is max over all available source/view/query pairs of max(0,H-G).
Refused/missing sources create no authority and score0. Calibrate delta_c=max
95 calibration episode scores per class. Receiver lifetime is max(-1,H-delta_c).
Negative lifetime is an empty authority window. Calibrate a TASK FUNCTIONAL,
not coverage of every possible center or trajectory. Slope3m/s is a predictor
design choice; the correction is learned against actual grid contact times.

For this frozen family and iid episode law, the standard max95 tolerance bound
controls episode-any grid-contact deadline overstatement at5% per class with
joint calibration confidence1-6*.95^95. Assumptions and finite-grid scope remain
essential. This is not conditional-on-grants risk, arbitrary scene inventory,
physical continuous-time or interactive ego-control assurance. Reuse/posthoc
selection precludes interpreting the existing test as an untouched confirmation.

All three representations reuse byte-for-byte primary stored source messages.
Receiver explicitly validates the primary contract/calibration/class and a
separate task-policy registry identity before deriving expiry from decoded
centers. Setup policy/primary registries are shared offline, as for earlier
methods; setup delivery and cold-start cost are not benchmarked. Payload radius
still means the primary state-set radius; it is not relabeled as8mm coverage.
All methods have the identical new task policy and source observations. Retain
original measured source/selection costs; remeasure actual message decoding,
frontend (fullXYZ), functional horizon and correction in three receiver calls.
Separate causal source/link/receiver queues, original wire bytes and propagation
are all charged. A perfect-future-grid contact oracle on the SAME arrivals is
only a posthoc diagnostic; it is not an implementable baseline.

Report score delta, episode-any violations, unsafe granted windows, per-class
and all scheduled grants, strong representation comparisons, oracle utility gap
and lifetime slack. Exact geometric solver brackets refer only to the fixed base
predictor. No global minimum conservatism, physical safety or MobiCom novelty
claim. Publish all outputs, failures, hashes and an independent implementation.
No repeated tuning or recurring research loop.
