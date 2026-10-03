# Primary-source reading and claim boundaries — 2026-10-03

1. **Perceive With Confidence: Statistical Safety Assurances for Navigation with
Learning-Based Perception**, [arXiv:2403.08185v3](https://arxiv.org/html/2403.08185v3),
17 April 2025. Read abstract, introduction, formulation, conformal background,
calibration and limited-field-of-view sections, plus the filtering formulation.
Its environment-level maximum score and dataset-conditional calibration directly
precede our use of finite-family maximum scores. It explicitly separates visible
objects from occluded space handled by planning. The extension includes 3D
occupancy/distance representations. Thus adding conformal calibration, a filter,
3D geometry or a planning wrapper is not a defensible novelty claim here. Its
finite sampled-state construction and environment law must accompany coverage
claims; no theorem is evidence of arbitrary unseen traffic generalization.

2. **Predictive Semantic Safety: From Visual Physical Reasoning to Safety-Critical
Control**, [arXiv:2609.34356v1](https://arxiv.org/html/2609.34356v1), September 2026
preprint; acceptance not verified. Read assumptions and the trajectory calibration,
occupancy and backup construction through Section IV-D opening. It fixes the
object inventory and geometric bounds, calibrates across whole trajectory families,
and distinguishes marginal trajectory coverage from accepted-update conditional
coverage. Missing predictions do not become free space. This is particularly
close to our risk/expiry interface; semantic prediction, joint risk calibration
and backup control cannot alone serve as the proposed contribution. Our shape
capture still lacks its complete inventory and trajectory coverage premises.

3. **From Prediction Uncertainty to Conformalized Distance Fields for Safe Motion
Planning**, [arXiv:2607.00776v1](https://arxiv.org/html/2607.00776v1), preprint;
acceptance not verified. Read the theorem discussion and Sections 7.1–7.3, not
the entire paper. Spatial functional calibration and online long-run coverage
are distinct from a finite-episode no-failure event. Planning assurances require
feasibility/coverage conditions; soft penalties do not remove unavoidable
infeasibility. We therefore do not turn repeated one-frame 95% statements into
a vehicle-level safety guarantee.

4. CARLA official [sensor reference](https://carla.readthedocs.io/en/0.9.15/ref_sensors/)
and [Python API](https://carla.readthedocs.io/en/0.9.15/python_api/): semantic LiDAR
is an idealized synchronized ray-cast measurement. Bounding boxes enclose actors
but their interiors need not be opaque. This motivates the new score, and also
limits transfer to physical sensor noise, dropouts and calibration errors.

## Candidate contribution after these readings

The project should investigate **which received evidence rules out the earliest
still-possible task failure, and whether requesting that evidence extends usable
expiry after all communication/computation costs**. The new shape study repairs
one prerequisite and may itself fail; it does not establish firstness, a complete
state estimator, or a MobiCom-ready contribution. Literature constraints and
negative experiments are kept visible instead of recasting known tools as novel.
