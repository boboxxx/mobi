# Primary reading informing the causal revision

Read the relevant problem/method/evaluation/limitation passages in the linked
primary full texts. Search metadata alone is not treated as paper understanding.
No method below has been reimplemented as an empirical baseline in this study.

- Lindemann, Cleaveland, Shim and Pappas, RA-L2023,
  [Safe Planning in Dynamic Environments using Conformal Prediction](https://arxiv.org/html/2210.10254):
  sections3–4 calibrate future trajectory regions and connect them to planning;
  Theorem1 applies a temporal union bound, and the planning claims have assumptions
  on agent interaction and feasibility. Future uncertainty calibration and robust
  planning are prior art. Our frozen prediction-tube follow-up uses finite future
  snapshot residuals, not a new planning theorem.
- Hu et al., NeurIPS2022,
  [Where2comm](https://arxiv.org/html/2209.12836): section4.3 selects spatial feature
  content and communication partners using confidence/request maps and a bandwidth
  budget. This rules out presenting spatial confidence selection or compact
  perception messages alone as our novelty. Its learned detection task differs
  from our known-class calibrated center sets; no accuracy superiority is claimed.
- Wei et al., **NeurIPS2023**, not ICCV2023,
  [Asynchrony-Robust Collaborative Perception via Bird's Eye View Flow](https://arxiv.org/html/2309.16940):
  sections3–4 formulate irregular asynchronous messages and estimate BEV flow to
  warp their features to a common time. Delay compensation and history-based
  temporal alignment are established. Our source-aged deadline is a finite
  validity measurement; no advantage over their learned compensation is tested.
- Shin et al., MobiCom2024,
  [RECAP:3D Traffic Reconstruction](https://fawadahm.github.io/assets/pdf/Recap_Mobicom_2024.pdf):
  introduction and sections4.5/5 separate reconstruction accuracy/coverage from
  component latency. It explicitly targets offline reconstruction. It would be
  misleading to present its latency as failure on our online query objective.
- Huang et al., MobiCom2025,
  [Modality Plug-and-Play:Runtime Modality Adaptation in LLM-Driven Autonomous Mobile Systems](https://sites.pitt.edu/~weigao/publications/mobicom25_mpnp.pdf):
  introduction and sections2–3 focus on efficient encoder-to-LLM adaptation, with
  device evaluation. Modality choice is assumed from external criteria; it is
  not a calibrated V2X evidence-expiry baseline. We do not add an LLM merely to
  borrow venue relevance.

The current question is whether a statistically covered finite future-state
family remains useful after actual observed source/receiver cost and causal link
queues. A successful finite trace would validate that pipeline, not establish a
new communication theorem or readiness for MobiCom2027. Strong same-state lossless
center and full-sampled-XYZ encodings must accompany any compact-wire claim.

## Additional closest safety/risk literature, read on2026-10-03

- Luo et al., *Sample-Efficient Safety Assurances using Conformal Prediction*,
  ICRA2022, [author full paper](https://stanfordasl.github.io/wp-content/papercite-data/pdf/Luo.Zhao.ICRA22.pdf).
  Read §II–III and Algorithm1/Proposition1: safety surrogates explicitly include
  time-to-collision; their warning guarantee concerns dangerous instances and
  marginal exchangeability. Calibrating a task safety score is already prior art.
  Our unconditional episode-any deadline overstatement is a different risk
  denominator, and must not be presented as their dangerous-instance FNR.
- Angelopoulos et al., *Conformal Risk Control*, ICLR2024,
  [primary full text](https://arxiv.org/html/2208.02814).
  Read §1.1, §2.1–2.3, Eq4 and Theorems1–2: bounded monotone losses can be
  calibrated in expectation. Their risk tightness theorem has additional iid/
  continuity assumptions and bounds risk, not milliseconds of expiry regret.
  Our max95 fixed-fit tolerance statistic is not their CRC algorithm and its
 95.4% calibration confidence must not be confused with marginal expected risk.
- Chang and Ahmed, *Barrier Function Conformal Safety Clearance Certification
  with CVaR for Driving Trajectory Selection*, arXiv2026 preprint (no verified
  peer-reviewed venue), [primary full text](https://arxiv.org/html/2608.26533).
  Read §II assumptions, §IV-B/C, Theorem1/Corollary1 and §V protocols/results.
  It calibrates prediction-minus-realized selected safety margin using a frozen
  complete selection/eligibility pipeline and session maxima. It explicitly
  distinguishes joint false certification from conditional certified risk.
  This substantially overlaps the methodological idea of task-functional and
  eligibility-aware calibration. Its object is driving clearance, not paid
  V2X source-aged message expiry. That difference alone establishes no novelty;
  new evidence selection and prospective systems experiments remain necessary.

The unfiltered functional policy and its single220ms-eligibility successor are
exploratory reused-data studies; these readings do not turn them into new
statistical methods or an untouched held-out validation.
