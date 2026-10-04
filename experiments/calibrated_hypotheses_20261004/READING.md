# Related-work reading that changes the candidate boundary

Plassier et al., **Probabilistic Conformal Prediction with Approximate
Conditional Validity**, ICLR2025. Read author full paper sections1–4, H1–H3,
Theorems3.1–3.3, Algorithm1 and experimental setup; targeted method/theory
reading, not a reproduction of its benchmark results.
[Primary PDF](https://proceedings.iclr.cc/paper_files/paper/2025/file/9da457059dd3386a2166c5b08f29b7de-Paper-Conference.pdf).
PCP already uses unions of sampled balls; CP2 adapts scale to an estimated
conditional distribution. Conditional accuracy bounds depend on distribution
estimation error and additional terms/assumptions. Therefore, multimodal sets,
adaptive normalized scores and approximate conditional coverage are existing
ideas. Our local training residual scale is a heuristic, not CP2 or a proved
conditional density estimator. The scientific question here is paid lifetime
benefit of exact current-observation geometric pruning and support fallback
under one registered current-state event. No novelty is established by naming
these components or by comparing only with an unadapted global circle.

Conrad et al., **Geometric Conformal Prediction with Spatial Ranks and
Multivariate Quantiles**, ICML2026. Verified venue and read abstract only from
[PMLR](https://proceedings.mlr.press/v306/conrad26a.html).
PDF fetch failed with unsupported content type; OpenReview requests returned
a verification page. Do not claim full-paper reading or implementation.
Its stated multivariate geometric set construction is additional prior art;
the abstract cannot establish detailed superiority or an uncovered novelty gap.

Search also surfaced EcoCert-V2X, Sensors2026; full page fetch failed. No method,
baseline or novelty conclusion is drawn from the search excerpt.
