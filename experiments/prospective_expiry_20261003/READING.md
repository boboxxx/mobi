# Closest prior work and the scope of the candidate

The development study's `causal_state_20261003/READING.md` records RA-L2023
trajectory calibration, Where2comm, CoBEVFlow, RECAP/MPnP reading and ICRA2022,
ICLR2024 and2026 direct safety-score calibration. Those methods remain prior art.

## Relevance does not yet define risk-qualified expiry

Lusvarghi et al., *The Search for Relevance: A Context-Aware Paradigm Shift in
Semantic and Task-Oriented V2X Communications*,
[author full manuscript](https://uwicore.umh.es/semanticV2X/Publications/The_Search_for_Relevance.pdf),
[arXiv metadata](https://arxiv.org/abs/2508.07394). The author copy is a manuscript
with a placeholder header; no publication venue is asserted here. Read§III,
§V-A/B and§VI: contextual relevance is already central to content selection.
Its numerical model uses distance-based detection probability, nonuniform
relevance weights, uncertain relevance estimates and a maximum item count;
assumes no transmission error/collision and expires received items after one
communication cycle (N slots). It supports relevance-aware V2X as prior art.
It does not provide the present candidate's data-dependent, action-budgeted
last-safe age against independently captured future-contact errors. That
difference is a candidate gap, not proof of novelty or empirical superiority.

## Driving-aware communication is already established

Liu et al., *Towards Collaborative Autonomous Driving: Simulation Platform and
End-to-End System*, [author full text](https://arxiv.org/html/2404.09496),
[official V2Xverse implementation](https://github.com/CollaborativePerception/V2Xverse).
Read§III-A/C,§IV communication,§VI-B/C and AppendixC latency: CoDriving uses
driving-request maps to select spatial perceptual features, and evaluates
perception/planning and actual feedback-driven CARLA driving, including latency
and pose noise. The repository identifies its paper as TPAMI2025; the fulltext
link is the author preprint/version. Claiming task-aware feature selection,
latency handling or CARLA closed-loop support alone is insufficient novelty.
Our finite fixed-query physical-actor capture and modeled arrival queues are
not this end-to-end driving benchmark; we have not run its models/checkpoints.

## Further exact temporal benchmark

Zhou et al., *V2XPnP: Vehicle-to-Everything Spatio-Temporal Fusion for Multi-Agent
Perception and Prediction*, ICCV2025,
[official repository](https://github.com/Zewei-Zhou/V2XPnP),
[full author text](https://arxiv.org/html/2412.01812). It studies one-/multi-step
communication and early/late/intermediate spatiotemporal fusion, jointly
evaluating perception and prediction. It is distinct from MobiCom2025 MPnP
(LLM multimodal interfaces); do not conflate the two. It is an important
representation/temporal prediction comparator, not an implemented comparator
in this current known-class center-based expiry study.

The present algorithm calibrates unsafe expiry overstatement only after a
fixed action eligibility filter; source-aged deadlines, paid arrivals, refusal,
minimal constant max95 correction and finite-grid oracle gaps are explicit.
The tolerance statistic, direct task calibration, episode maximum and frozen
selection-pipeline principles are established tools. MobiCom novelty would
require an independently distinct evidence/content/arrival/expiry selection
algorithm and credible end-to-end systems benefits; current results cannot
claim them merely by combining known ideas.
