# Temporal-observation diagnostic, fixed before its outputs

This follow-up is motivated by the negative single-snapshot diagnostic. It
preserves that diagnostic and its model family/thresholds without modification.
It tests the value of additional information, not retuned motion parameters.
It is synthetic, finite, discrete, per-action and conditional on the known
12-model family; no learned sensor model or CARLA result is claimed.

Reuse exactly the nine-state dynamics, prior and sensor likelihoods frozen in
action_window_reference_20261011. Obtain three actual partial observations at
source ticks 0,2,4. Enumerate all 4^3=64 histories. Reference epoch is tick 4;
retain all three acquisition times (no receipt-time reset). A history filter
per model applies likelihood at each acquisition epoch and propagates in
between. Latest-only comparison propagates the initial prior to tick 4 and
conditions only on the last observation. It is given the correct prior, not
artificially initialized with the original source distribution at tick 4.

Enumerate all histories, H in {1,2,4}, start ages 0..16 relative to source tick
4, and alpha in {.01,.05,.1}: 9792 query contexts. Apply the same robust
whole-window criterion to each information set. Neither true model nor state
enters the decision. Evaluate under each of the 12 possible true models.

Counts over histories are a diagnostic, not representative traffic statistics.
For each model, use its exact joint history probability for acceptance and
conflict mass. For each H,age,alpha and method, calculate conditional conflict
probability over selected histories (if any). This distinction matters:
latest-only is promised safety conditional on its latest observation, not
conditional on a hidden full history it never uses. A particular history can
have greater risk without violating that marginalized guarantee. Do not label
this as an unsafe latest-only policy solely from a history-conditioned slice.

Compare acceptance probability for each model at matched per-action budget.
Report both gained and lost decisions after receiving additional observations;
information can reveal danger as well as remove ambiguity. Separately measure
fees 0,1,2 ticks by excluding ages earlier than a paid fee, without changing
any risk. Added sensing/communication costs are not experimentally measured;
thus this is not an equal-cost system improvement claim.

Verify Bayes normalizations, sum of joint history probabilities=1 under every
model, independence of truth from policy decisions, exact killed-chain vs
absorbing-state recursion, and risk bounds after actual decision selection.
Compare local and sheng scientific JSON byte-for-byte. Freeze code and every
dependency hash before output. One finite job per host; no automation.

This follow-up cannot resolve unknown targets, sensor-model misspecification,
continuous physical tracking, actual V2X or whole-episode closed-loop risk.
Those require independently collected observations and frozen, calibrated
policies. No favorable-result stopping, parameter pruning or threshold tuning.
