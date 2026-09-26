# Feasibility pilot v1 — protocol before running

Date: 2026-09-26. Host requested by user: sheng; current reachable address verified from existing project records: 100.94.183.27.

Question: do complementary messages provide enough *achievable* decision benefit over strong singleton selection to justify developing the proposed V2X algorithm?

No result below will be called closed-loop driving, real-world safety, an official baseline reproduction, or evidence of publication readiness.

## Experiment A: exact finite Bayesian mechanism test

Randomly generate 4 latent binary conflict-zone states, finite actions with conflict-zone requirements, independent noisy binary observations, and a risk-constrained decision rule. Compare no observation, single-step expected decision-value selection (fills budget with an entropy-based tie break), two-step selection, exact nonadaptive subset selection and risk/entropy selection. All schedulers see priors, likelihoods and action definitions, but not the true states or unrevealed message outcomes. Enumerate all states and observation outcomes; no Monte Carlo ground-truth shortcut. Evaluate both one-requirement actions (negative control) and multiple-requirement actions (mechanism stress test). Link delivery is independent unless otherwise stated; message failure is an explicit observation outcome. This model is generated, not a natural traffic distribution.

## Experiment B: existing OPV2V detector-cache open-loop probe

Use `/home/sheng/voi/data/opv2v/*.npz` (465 frames), created by frozen single-agent V2X-ViT inference; these contain all ego/sender predictions and GT, not just the GT-matched object table. Read the accompanying extraction manifest, source script and frame CSV. Dataset is CARLA-generated OPV2V validation, not real-world vehicle data. No network retraining.

Map each frame to its original YAML using the same sorted scene/CAV/timestamp indexing as OpenCOOD. Use its recorded plan_trajectory, transformed to ego LiDAR coordinates. A route-prefix probe uses stop and increasing progress along the recorded route. A separate branching stress probe adds lateral-offset candidates, with **no claim that these candidates obey lane boundaries or vehicle dynamics**. Static swept-box intersection is only a decision probe, not collision probability.

The sender chooses among at most 8 nearest detected objects, selected without GT. Messages contain actual serialized quantized box corners and confidence. The receiver request contains its quantized route and local action-blockage scores; this information is paid for. Thus the sender can evaluate its own messages plus the explicitly shared receiver state, without seeing GT or hidden receiver inputs. This is a one-sender pilot; distributed multi-sender uncertainty remains untested.

Hold the candidate actions, frozen outputs, encoding and fusion rule fixed. Compare singleton expected-value greedy, pair lookahead, exact small-subset search, risk-coverage ranking and a confidence-ranked object broadcast requiring no task request. Include no communication and reliable all-candidate reference. Preserve zero-benefit frames. Exact search is under the declared known-message model, not a GT oracle. Ground truth is used only after selection for static intersection diagnostics.

Report action disagreement and decision regret relative to all-candidate perception, plus independent GT static intersection and progress diagnostics. Report reference failures and regret improvements that do not improve GT outcomes. Use existing scene split (3 development, 6 evaluation scenes), and paired scene-level bootstrap. Do not interpret frames as independent traffic episodes.

Budget configurations include constrained and loose regimes, reliable and lossy delivery, short and generous deadlines. Count request bytes, data bytes, request erasure and complete-message delivery; include measured selector compute latency in deadline admission. The software link model is not PC5 measurement. CRC/serialization verifies accounting but is not a PHY simulation.

## Go/no-go

Proceed to a full driving experiment only if the strong singleton method leaves useful headroom, an implementable policy captures some of it, and gains survive communication/control costs. A result confined to generated multi-requirement cases or artificial lateral alternatives supports only a mechanism, not the road-driving research claim. Negative outcomes and overhead losses are retained.

## Data eligibility amendment after first full-run parser failure

The first full run encountered an empty `plan_trajectory` in the source YAML and stopped before aggregate results were written. Frames with missing/empty routes or less than 1m of recorded route are now explicitly ineligible for the route probe; all are logged with frame and reason in `exclusions.csv`. No synthetic replacement route is invented, and no exclusion depends on method performance. Source and eligible frame counts must both be reported.

## Self-obstacle audit correction

The first complete data run produced anomalously high static blockage. Inspection showed that sender predictions and merged GT include ego itself near (0.5m,0m), while ego's own detector does not. Those first results (`results/opv2v`) are invalid for driving conclusions and are retained for audit. The corrected run (`results/opv2v_self_filtered`) applies the same pose-only rule independently to each prediction list and GT: suppress boxes whose center is within 1.5m of known ego origin and whose footprint covers that origin. No GT matching is used by selection. This heuristic and removal counts are reported; near-overlap edge cases remain a limitation. A regression test checks that a neighboring vehicle remains.
