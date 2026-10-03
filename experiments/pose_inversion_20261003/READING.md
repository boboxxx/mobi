# Primary-source checks — 2026-10-03

**Jaulin and Walter, “Set Inversion via Interval Analysis for Nonlinear
Bounded-error Estimation,” Automatica29(4),1053–1064,1993.**
[Author-hosted paper](https://webperso.ensta.fr/Jaulin/paper_automatica93.pdf).
Read formulation, interval inclusion functions, outer/inner set enclosure and
Section5 algorithm/conditions, plus limitations in the conclusion. SIVIA already
classifies parameter boxes, retains ambiguous regions and bounds characteristics
of the resulting sets. It discusses dependency/overestimation and the cost of
dimension/precision. Therefore our continuous-pose subdivision, uncertainty bounds
and finite search cap are uses of established ideas. We have not implemented a
full directed-rounding SIVIA library or inherited its convergence conditions for
our discontinuous integer-count score. FIFO is our simple comparison; it is not
the paper's stack implementation and does not exhaust strong search strategies.

**“Uncertainty Quantification for Visual Object Pose Estimation: S-Lemma
Ellipsoidal Bounds,” arXiv:2511.21666.**
[Primary full text](https://arxiv.org/html/2511.21666).
Read SectionIV (measurement/pose constraints and Proposition1), S-lemma relaxation
and hierarchy discussion, and empirical coverage discussion. It propagates
keypoint uncertainty to a continuous pose constraint set and bounds that set with
ellipsoids. Per-keypoint marginal guarantees do not automatically become an equal
joint pose guarantee; dependence and union bounds matter. Its results also
distinguish simulated versus real calibration and report coverage limitations.
The relevant lesson is that pose-set construction and calibration propagation
are established research topics, with explicit geometric and statistical premises.
We have not reproduced its method or verified a venue acceptance status.

The earlier [shape-study reading](../shape_evidence_20261002/READING.md) covers
Perceive With Confidence and predictive semantic safety. Together these sources
rule out claiming novelty merely from combining calibration, a pose set and
reachability. The unresolved communication contribution remains task-specific
evidence selection that buys usable validity after all costs, supported by a
validated observation/state/trajectory model and stronger appropriate baselines.
