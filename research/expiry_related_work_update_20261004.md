# Evidence expiry related-work update,2026-10-04

This note was written during the finite independent CARLA capture. It does not
change any frozen method, threshold or service policy. Reading scope is explicit;
no external framework was reproduced or benchmarked by this update.

## Newly checked primary work

**CooperTrim — Mukhopadhyay, Roy-Chowdhury, Qiu, ICLR2026.**
Acceptance/title checked against the
[official proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/c99e08e921b90e901e5eaa7ddee51d6c-Abstract-Conference.html).
Read author manuscript sections3.1–3.3, selected experimental discussion, and
appendixA.8–A.9:
[author full text](https://arxiv.org/html/2602.13287v1).
It requests features using temporal representation differences, a learned quantile
gate and attention cutoff. Section3.2 explicitly distinguishes its conformal-
inspired gating from fixed calibration and intervals on the full regression
output. The theorem in3.3 concerns gradient bias in training. Its empirical
communication/accuracy evaluation is relevant; it does not supply the source-age
or conditional-action certificate evaluated here.

**MOT-CUP — Su etal, author revision2024.**
Read III-B–III-E, algorithms1/2, and experiment setupIV-A:
[author full text](https://arxiv.org/html/2303.14346v2).
It calibrates normalized coordinate errors, then incorporates corrected detection
uncertainty into Kalman filtering and association. Its scalar coverage lemma
states an IID premise. The evaluation is on V2X-Sim sequences, with tracking and
uncertainty metrics. This directly rules out claiming that propagating conformal
uncertainty into collaborative motion processing is new. Its prediction unit and
objective differ from an entire-episode source-age certificate followed by a
fixed-policy selected-query risk test. We have not evaluated MOT-CUP weights or
claimed superiority over its detector/tracker.

## Implications for this project (our assessment)

“Semantic”, “temporal uncertainty”, “conformal V2X”, “less retransmission” and
“uncertainty propagation” are not sufficient originality claims. Geometry sets,
normalized prediction scores, episode maxima, union accounting and exact selective
risk testing are established tools. The demonstrable development contribution is
identifying and correcting cross-contamination between the supported prediction
score and fallback geometry scale, while preserving observation constraints.

The central research question is whether partial observation can yield a useful
absolute expiration time with explicitly bounded authorization error after queueing,
transmission and receiver computation. That question requires actual source ages,
missing-observation refusal, risk-aware selection, and honest service costs.

A fair comparison must include the same initialized predictor/geometry sending
only direct deadlines or compact state. Renaming state as semantic evidence does
not create a contribution. CooperTrim is a relevant communication-scheduling
baseline for a future shared-feature/mobile study; MOT-CUP is a relevant temporal
state-estimation baseline when a detection/tracking pipeline is included. The
current known-class single-actor fixture is not equivalent to either workload.

The current independent experiment uses fixed query locations and measured FIFO
services; it cannot by itself establish an ego closed-loop or real wireless
advantage. Any final MobiCom story must remain conditional on that evidence.
Do not transplant another paper's empirical bandwidth percentage into this project.

## Reading and execution evidence

- Earlier normalized-neighbour, geometric/multimodal conformal, semantic POMDP and
  action-conditional literature is recorded in the previous published reading notes.
- Learn then Test selective binary testing is used explicitly, without novelty claim:
  [author section3.2](https://arxiv.org/html/2110.01052v5).
- The frozen method is `experiments/component_expiry_20261004/method.py`;
  independent-stage contract is `experiments/prospective_component_20261004/PROTOCOL.md`.
- No model, calibration rule, policy or test statistic changed after reading these
  newly retrieved papers. The already frozen finite experiment continues unchanged.
