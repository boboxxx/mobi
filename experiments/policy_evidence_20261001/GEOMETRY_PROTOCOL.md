# Fixed policy-conditioned geometry comparison

Use the twelve `*_00.npz` clouds from the existing 120-frame static capture,
without a prior or bootstrap. Same raw rays, projection uncertainty, quantization,
obstacle profiles and world/body registration as the braking follow-up.
Three stipulated initial speeds (0, 0.5, 1 m/s), five horizons
(0.2, 0.3, 0.4, 0.5, 0.6 s) give 180 paired checks.

Compare arbitrary-direction absolute acceleration 8 m/s² with the restricted
hold/go/brake policy in `tube.py`. These have different execution assumptions;
this is a conservatism/feasibility diagnostic, not a fair algorithm superiority
claim. No selection based on obstacle labels. Retain every failure.

Only policy geometry positives are packed as receiver-recomputed raw-ray proofs.
Measure cold generation and verification separately. Link delay is hypothetical
20 ms; additionally report 50 ms acquisition sensitivity. A zero-compute lower
bound diagnostic uses age 20 ms. All stopping gates remain conditional on
unvalidated physical contracts; no CARLA action is authorized. Raw captured
clouds do not become an ego-driving run by assigning hypothetical speeds.

Take a maximum only over the prespecified five-point horizon grid. Do not claim
it is the continuous optimum. Compression can fail independently of geometry.
Validate recorded packets against source rays and replay every saved positive.
