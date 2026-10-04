# Post-freeze reading update: ICML2026 full method text accessed

The frozen READING.md accurately records the initial browser PDF failure.
After freezing the candidate, the publisher-linked raw GitHub PDF was fetched
directly (a MIME-parser failure, not an access challenge bypass) and parsed
locally. SHA256: `fddd74dddac383f5f72c06bc807932bfb90ce6d99a7039afca6ac855da2abc81`;
2466311bytes,26pages. The copyrighted PDF is not redistributed in this repo.

Conrad, Moulines andPerez, **Geometric Conformal Prediction with Spatial
Ranks and Multivariate Quantiles**, ICML2026. Read sections1–4 and6,
including convex geometric quantile/spatial-rank definitions, PICNN and
kernel-weighted estimators, signed-distance/radial-rank calibration and
multi-output benchmark protocol/results. Targeted full-method reading,
not complete appendix verification or benchmark replication.
[Primary publisher-linked PDF](https://raw.githubusercontent.com/mlresearch/v306/main/assets/conrad26a/conrad26a.pdf).
GCQR conforms learned region boundaries; GRCP conforms estimated geometric
ranks. Local conditioning, shape adaptation, robust multivariate uncertainty
and cost/validity tradeoffs are established research topics. Their stated
split-CP result is marginal, not an unconditional per-input/authorized-action
guarantee. Our exemplar residual scale does not implement either method.
This reinforces the need to demonstrate paid geometric-pruning utility and
compare with adaptive set baselines, rather than claim new conformal geometry.
No candidate model, parameter, guard, score or development result is changed
in response to this reading update.
