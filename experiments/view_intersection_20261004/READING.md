# Additional primary-source reading, October4

These papers constrain the novelty claim. None of their learned models is an
implemented comparison in this same-state receiver-geometry experiment.

## CooperTrim — ICLR2026

[Official proceedings](https://proceedings.iclr.cc/paper_files/paper/2026/hash/c99e08e921b90e901e5eaa7ddee51d6c-Abstract-Conference.html),
[author full text v3](https://arxiv.org/html/2602.13287).
Read§3.2–3.3,§4 andAppendicesA.8/A.9. Temporal L1 changes between current and
previous fused features guide recipient requests; learned quantile and attention
thresholds control channel quantity. The text explicitly distinguishes its
conformal-inspired online gating from fixed-calibration regression intervals.
Inference loss experiments use simulated masks, while training assumes perfect
transmission. Uncertainty-driven selective sharing, temporal reuse and adaptive
request volume are therefore prior art. Their IoU/AP/channel-volume evaluation
does not supply this experiment's source-aged last-safe contact age. That is a
different metric, not evidence of novelty or superiority.

## MOT-CUP — RA-L2024

[Author full text v2](https://arxiv.org/html/2303.14346),
[author journal PDF](https://songyanghan.com/publication/ral2024/ral2024.pdf).
Read§III-C–E and§IV. Detection heads estimate variable-wise means and standard
deviations; conformal coordinate correction supplies uncertainty to Kalman
prediction and negative-log-likelihood association. The dataset evaluation uses
V2X-Sim. Detection uncertainty propagation into downstream collaborative
tracking is already established. Its coordinate-level formulation and learned
tracking differ from a max95 complete-episode event; neither their per-variable
coverage nor our current-state event automatically proves continuous-body safety.

## Dependent-sensor conformal late fusion — Neurocomputing2026

Siahkali and Gupta,
[publisher primary page](https://www.sciencedirect.com/science/article/pii/S0925231226005795),
DOI10.1016/j.neucom.2026.133182, volume678. The accessible abstract/introduction
describe learning dependencies among sensor p-values and recalibrating the
fusion scores, rather than assuming independent views. Full theorem formulas
were not available in this read; no detailed bound is quoted. Fusion with
dependent sensor uncertainties is prior art. Our intersection instead preserves
one already-calibrated simultaneous current-state event and adds no fusion fit.
This distinction alone does not establish a new statistical method.

## Proof-of-Perception —2026 author preprint

[Full author text](https://arxiv.org/html/2603.00324).
Read§3.2–3.5,§4.5–4.10. Set-valued node outputs drive accept/retry/expand/abort
decisions under computation budgets. Its stated limitations separate per-node
coverage from answer-level coverage, which is not theoretically guaranteed by
composition; the cost model is simplified. Certified uncertainty directing
additional computation is therefore prior art. Do not claim a fresh contribution
just by adding certificates and adaptive stopping to a V2X pipeline. The author
preprint is the source read here; a proceedings page lookup failed, so no venue
claim is needed for this comparison.

The current lens calculation and primal/dual supports are elementary convex
geometry. A MobiCom contribution would need a distinct communication/evidence
selection result and credible end-to-end benefit beyond these prior techniques.
