# Primary-paper reading and novelty boundary (2026-10-04)

Read the following full author manuscripts, separating prior art from our
development results. No paper's reported accuracy or runtime is our measurement.

**Groß, Osep and Leibe, AlignNet-3D (3DV2019).**
[Author PDF](https://arxiv.org/pdf/1910.04668), introduction, method/network/loss
and experiments. Partial-view centroid bias and learned amodal center/yaw
estimation are established problems. Segmentation/association are given to its
registration system. Our retained yaw family is a different output, but neither
partial visibility nor shape-based correction establishes novelty.

**Yang and Pavone, Object Pose Estimation with Statistical Guarantees
(CVPR2023 highlight, author metadata).**
[Full author manuscript](https://arxiv.org/html/2303.12246), sections3–6 and
supplementA3.4–A3.5. Joint keypoint scores induce pose uncertainty sets; geometric
propagation preserves coverage. Nonconvex-set error bounds use SDP relaxations.
Large sets and annotation symmetry can remain conservative despite tight solver
bounds. Their exchangeability discussion excludes treating correlated video
frames as independent samples. Pose-set certification is strong prior art.
The official CVF PDF returned403; the accessible full author manuscript was read.

**Timans et al., Adaptive Bounding Box Uncertainties via Two-Step Conformal
Prediction (ECCV2024, author metadata).**
[Full author manuscript](https://arxiv.org/html/2403.07263v2), sections2.3,
4–6. Class prediction sets and class-conditioned box uncertainty explicitly
handle classification ambiguity. Undetected objects are outside its stated
coverage. Our known-class catalogue is an assumption; fitting point-group
coverage does not establish scene completeness. We use one whole-episode joint
event, without multiplying marginal coverages or assuming independent outputs.

**Fayyazi et al., Proof-of-Perception.**
[Full author manuscript](https://arxiv.org/html/2603.00324), sections3.3–3.5,
4.10. Set-valued tool results and budgeted acceptance/retry/abort are prior art.
Its stated marginal node guarantees do not alone establish answer-level
composition. The official CVPR2026 result was search-indexed, but its page
returned403; full-text reading relied on the author manuscript. Historical
reading records are retained rather than silently upgrading venue verification.

These papers weaken a story based only on uncertainty sets, certificates or
known-shape inversion. The candidate still needs a distinct mobile/wireless
algorithm: show which transmitted constraints remove action-relevant ambiguity,
quantify what uncertainty remains, and beat strong same-information alternatives
after source, bytes, queue and receiver costs. Our current sphere-to-pose gain is
a representation effect. The same exact hull supports every policy; it is not
evidence of a new selector or compressor.

[Official MobiCom2027 CFP](https://www.sigmobile.org/mobicom/2027/cfp.html)
was checked on2026-10-04. It asks for significant mobile/wireless contributions.
Summer submission was2026-09-02; winter dates remainedTBD. Do not invent a
winter deadline or equate this incomplete feasibility package with submission
readiness.
