# Primary-source reading during the finite independent capture

This note does not alter the already published model/score freeze or measurement
freeze. No method or threshold is changed based on these papers or fresh data.
Downloaded copyrighted papers are kept in /tmp and are not redistributed.

* Zakeri, Moltafet, Codreanu, **Semantic-Aware Sampling and Transmission in
  Real-Time Tracking Systems: A POMDP Approach**, TCOM73(7),4898–4913,2025,
  DOI10.1109/TCOMM.2024.3511935. [Author institution PDF](https://liu.diva-portal.org/smash/get/diva2%3A1997077/FULLTEXT01.pdf).
  Retrieved16pages,1434755bytes,SHA256
  `da8bb47e78e29ff8e4f1054e6356d44b42a866a4a75842e15daf0c15142b215a`.
  Read model§III, belief/policy§IV including Proposition3, selected experiment
  discussion§V, conclusion and AppendixA. A costly sample reveals a finite
  Markov state; unsampled slots are partially observable. Belief depends on
  known source dynamics and buffered/feedback observations. Partial-observation
  semantic sampling is established; it is not calibrated continuous LiDAR sets.
  No replication or claim that all appendix proofs were checked.

* Salimnejad, Ephremides, Kountouris, Pappas, **Optimal Sampling and Actuation
  for Real-Time Monitoring of Markov Sources**, [author preprint v2](https://arxiv.org/html/2604.00748v2).
  Read§I–IV, especially model and CoAU/actuation formulation. The source sampler
  observes the current finite Markov state; perfect instantaneous feedback and
  receiver uncertainty affect randomized actuation. This already makes the
  distinction between estimation accuracy and effective action. Do not claim
  an accepted venue or a LiDAR coverage/time-validity theorem from this work.

* Zhu, Kiyani, Pappas, Hassani, **Conformal Risk-Averse Decision Making with
  Action Conditional Guarantee**, [author preprint HTML](https://arxiv.org/html/2606.05551v1),
  [metadata](https://arxiv.org/abs/2606.05551).
  Read§1–4, Theorems2.1/4.3 and Algorithm1. Finite discrete actions, prediction-
  set-dependent action groups and candidate-test-label pinball optimization are
  explicit. The stated finite-sample result uses exchangeability; continuous
  score assumptions additionally enter its upper-slack bound. Our frozen max125
  episode qualification is not AC-RAC and has no action-conditional guarantee.
  HTML displays a later internal date than metadata; no acceptance inference
  is made from search engines or third-party venue labels. Not fully replicated.

* **Vision-Based Safe Human-Robot Collaboration with Uncertainty Guarantees**,
  [author preprint](https://arxiv.org/html/2604.15221v1): read method background,
  task definition and§III-A–E. Normalized position-error spheres, physical speed
  expansion between forecast times and OOD reuse of prior predictions are
  closely related prior ideas. Missing humans/entry-exit handling are explicitly
  limited in that pipeline. This partial reading
  does not independently validate its safety-rate/certification claims.
* **Finite-Sample Conformal Coverage Recovery via Fusion under Degraded Local
  Guarantees in Occupancy Map Estimation**, [author metadata/abstract](https://arxiv.org/abs/2607.14906):
  abstract-only lead, not a read/verified fusion guarantee or implemented baseline.
* **Probabilistic Object Detection with Conformal Prediction**, [publisher
  page](https://proceedings.mlr.press/v329/ries26a.html): abstract-only lead on
  scaled/class-wise object-detection calibration. No full-method claim or venue
  comparison is inferred from this abstract.

The scoped inference is that partial observation, state-set calibration and
action-aware uncertainty are established research axes. A new mobile contribution
must withstand honest direct-deadline, strong state-estimation and initialized
same-information baselines, with complete costs and the appropriate risk event.
