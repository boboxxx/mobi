# Additional primary-source check before motion-envelope work

Read on2026-10-04; this note does not change any experiment, threshold or result.

## Functional distance-field conformal prediction

Shin, Ra and Yang, [From Prediction Uncertainty to Conformalized Distance Fields
for Safe Motion Planning](https://arxiv.org/html/2607.00776v1), author preprint
v1,2026-07-01. Read Sections4–7 and the explicit scope remarks. The method
conformalizes a residual distance field using functional principal components
and a Gaussian-mixture coefficient envelope. Its field bound supports trajectory
queries without tying coverage to a particular control sampler. Section4 assumes
obstacle occupancy independent of ego controls and full occupancy observability;
partial observability is left for future work with a conservative occupied-space
alternative. The safety remark distinguishes desired per-step probability from
proved long-run empirical closed-loop safety. Theorem2 requires ongoing MPC
feasibility, asymptotic field coverage and equality of actual and planned next
positions. Therefore neither this theorem nor an adaptive conformal citation
supplies our missing source-age, partial-observation or physical tracking
certificate. A queryable uncertainty field is already prior art; we must not
present that representation alone as novel. No publication venue inferred.

## Conformal ACC with temporal perception

Li, Girard and Kolmanovsky, [Safe Adaptive Cruise Control Under Perception
Uncertainty: A Deep Ensemble and Conformal Tube Model Predictive Control
Approach](https://arxiv.org/html/2412.03792v1), author preprint v1,2024-12-05.
Read Sections2–3. Stereo image history estimates distance headway and relative
velocity; ensemble uncertainty is conformalized before longitudinal tube MPC.
Theorem1 is standard split-conformal coverage under IID/exchangeability, not
coverage conditional on a network-delayed authorization. The longitudinal model
assumes lead speed constant between adjacent samples. Temporal perception plus
conformal tube control is consequently not a new combination by itself.

## Networking comparator with restricted reading scope

[STCC: A Spatio-Temporal Calibration Method for Delay-Tolerant Cooperative
Vehicular Network](https://doi.org/10.1109/INFOCOM59046.2026.11571531), INFOCOM2026.
Publisher search record identifies history-aware delay alignment and interaction
uncertainty calibration. Only the indexed abstract/metadata were accessible;
full methodology and quantitative results have **not** been read or reproduced.
It is a relevant comparator to obtain before a broad novelty claim.

## Implications for this repository (our inference)

We should attribute set-to-distance, conformal tubes, temporal velocity inference
and queryable fields to existing research. The unresolved empirical question is
whether partially observed, source-stamped evidence can remain useful after actual
communication and execution fees at a matched risk level. Current motion and ego
tracking bounds are conditions; neither parked-target diagnostics nor marginal
center calibration can replace them. A future temporal-envelope implementation
must keep every historical source epoch, handle incompatible history by refusal,
and certify its own observation/controller law. Actual distributed transport and
a matched compact scalar comparator remain necessary for a MobiCom systems claim.
No new algorithm, experiment or risk certificate is claimed by this note.
