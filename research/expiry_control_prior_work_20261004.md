# Additional control and deployment prior work

Read on 2026-10-04 during the finite prospective capture. No scores, thresholds,
models or policy definitions were changed. This note supplements, rather than
edits, the already frozen related-work document.

## Uncertainty can already determine a safe update interval

Yang, Pappas, Mangharam and Lindemann,
[Safe Perception-Based Control under Stochastic Sensor Uncertainty using Conformal Prediction](https://arxiv.org/html/2304.00194v2).
Reading scope: Sections 3--5, Proposition 1, equation (9), Lemma 2 and Theorem 1.
This author manuscript constructs perception-error bounds using calibration at
workspace grid points and Lipschitz extension. Equation (9) determines the next
control update from the error bound, a robustness parameter and a bound on dynamics.
The authors integrate this interval with a measurement-robust barrier controller
and evaluate a simulated LiDAR-equipped F1/10 vehicle. Their assumptions include
calibration access at grid states and sensor/perception regularity.

Implication for this project: a calibrated state set plus a motion bound plus a
valid time interval is established prior art. Our fixed-distribution episode
calibration does not replace their spatial assumptions with a pointwise guarantee.
Any claimed contribution must concern the partial-observation mechanism and its
communication consequences, demonstrated against fair controls. We have not
reimplemented or experimentally compared this controller.

## Compact cooperative messages and vehicle planning are already connected

Qu, Chen, Shimizu and Altintas,
[CooperDrive: Enhancing Driving Decisions Through Cooperative Perception](https://arxiv.org/html/2604.14454v1),
author preprint dated 2026-04-15; no publication venue is inferred here.
Reading scope: Sections III--IV, particularly III-B and IV-A/IV-D.
The authors exchange poses and object-level detection outputs, augment the planner's
object set and keep the underlying hierarchical planner. They report real-vehicle
experiments using two Toyota Sienna vehicles, LiDAR and prototype V2V radios.
Fusion weights account for remote latency, confidence and source trust. Their
planning evaluation includes TTC, stopping-related measures and constraint
violations; these reported empirical outcomes are not conditional-on-authorization
statistical certificates.

Implication for this project: object-level communication, lower traffic than dense
feature sharing and earlier reactions to occluded traffic are established directions.
Our registered-target fixed-RSU fixture cannot be described as stronger deployment
evidence. We read the paper but did not reproduce its hardware measurements or
compare its trained detector experimentally.

## The remaining claim to test

The current finite experiment tests whether separating supported-model and fallback
geometric errors improves source validity without sacrificing the fixed risk budget,
and whether this survives paid computation and communication with a separately
certified authorization policy. The same-model direct-deadline control is essential:
longer source validity or a small message is insufficient evidence of a useful
communication contribution. Actual result and scope are recorded separately after
the independent run; this note does not anticipate them.
