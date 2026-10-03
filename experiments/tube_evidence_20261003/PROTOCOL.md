# Bounded-return evidence under coordinate perturbations

Finite follow-up, frozen before outcomes. Keep the previous terrain-clipped score,
calibration thresholds, pose prior, disc dynamics, unknown boundary and64000-node
budget. Use all six classes and both fixed queries. No new risk calibration or
real sensor/noise robustness claim from synthetic data.

For each class, old test00 is the predictor/reference; current test10 is the new
observation. Current noise variants: unchanged capture, additive sensor-xyz
Gaussian sigma1mm, sigma10mm; deterministic per-class SHA-derived seeds. Noise is
an algorithm stress input, not a calibrated CARLA/physical sensor model. Preserve
current frame/time, and report whether the current full-score true pose is kept.

Three fixed endpoint radii:0mm,5mm,50mm. Before seeing current inputs, build one
continuous proof tree per radius from the old scan. Inflate outer pose boxes and
lower the ground clipping plane; erode inner boxes and raise its plane by the
endpoint radius plus explicit numerical/time-parameter guards. A nominal ray
then bounds all current endpoints in that ball. Unresolved cells remain possible.

Sender reads ALL actual current points. Returns outside the advertised world
endpoint ball are sent exactly with indices; all others are represented by the
ball. Receiver verifies reference/configuration/current-time identities and packet
integrity. Missing observations are not small changes. Incompatible counts or
sensor transforms refuse. Ball membership is an encoder assertion checked against
actual current data by the independent experiment audit, not remote authentication.

Revalidation subtracts old ball contributions for exceptions and adds exact current
contributions. Compare with full rechecking of the SAME mixed ball/exact message
on the SAME inherited partition. All counts and outputs must match. Also compare
all resulting score lower bounds against the actual complete current returns.
This preserves raw-score soundness without pretending in-ball coordinates equal
their old values. Charge encoding, packet decoding, receiver checks, bootstrapping
and the existing20Mbps/20ms propagation/20ms clock/200ms reserve model.

Run the fixed matrix:3 radii x3 noise conditions x6 classes x2 queries =108 warm
cases, three timing repeats. Radius0 is the exact lossless-update control. Retain
all zeros, revoked exclusions, oversized messages and worse-runtime outcomes.
No automatic parameter sweep, scheduled loop or new CARLA server is started.
