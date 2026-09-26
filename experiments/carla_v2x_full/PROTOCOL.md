# Decision-sufficient V2X: finite experiment protocol

Frozen before running the main sweep on 2026-09-26. This is a finite, terminating experiment suite. It does not schedule recurring research or claim to reproduce named systems whose official code is not integrated.

## Question

Does set-aware scheduling provide a reproducible advantage over strong per-region/single-message selection once the receiver must obtain fresh evidence for two decision-critical regions, and is any advantage caused by set utility, by modeling the joint delivery process, or both?

The experiment may reject the proposed story. A CARLA platform run does not by itself establish novelty.

## Evidence and decision rule

There are two route-critical regions, A and B. Evidence is one of `free`, `occupied`, or `unknown`, with a production time and expiry. `free` requires an actual observation covering the region; absence of a message remains `unknown`. The conservative controller proceeds only while fresh evidence says both regions are free. Any occupied or unknown region causes it to wait.

Each region has two providers: A0/B0 share channel 0 and A1/B1 share channel 1. Provider identity, region, nominal delivery model, message size and observation age are available to the scheduler. The evidence content is not available to the receiver before delivery. Messages are 48 bytes; all transmissions, including redundant messages, count.

## Methods

1. `no_comm`: conservative local fallback.
2. `round_robin`: two-provider periodic broadcast, rotating provider pairs.
3. `coverage_greedy`: select one highest-marginal-delivery provider per unresolved/old region; this is the strong simple baseline and prevents a deliberately bad duplicate-only singleton method.
4. `singleton_voi`: greedy expected uncertainty reduction per byte, with redundancy suppression.
5. `set_independent`: enumerate feasible pairs and evaluate decision sufficiency using the product of marginal delivery probabilities.
6. `set_joint`: same set utility and search budget, using the configured joint delivery model.
7. `full_info`: sensor evidence without network loss or byte cost; an upper reference, not a deployable baseline.

The two set methods enumerate the same small candidate space. Their difference isolates joint arrival modeling. `coverage_greedy` and `singleton_voi` are allowed to stop refreshing already-fresh evidence and may select different regions; they are not forced to fill the budget with redundant messages.

## Network configurations

- `ideal`: two messages per 100 ms cycle, deterministic one-cycle delivery.
- `independent`: independent provider losses using declared marginals.
- `contention`: two simultaneous messages on the same channel cannot both arrive; cross-channel messages have independent losses.
- `burst`: messages on the same channel share a good/bad state, creating positive delivery correlation.
- `short_deadline`: channel 1 has a two-cycle delay but the deadline is one cycle.
- `one_slot`: one message per cycle; evidence can accumulate only while it remains fresh.

All configurations use a finite deadline and evidence lifetime. Arrival after deadline is counted but cannot affect the current decision. The simulator records scheduled, delivered, useful, expired and dropped bytes/messages.

## Scenario families

- `free`: both regions are free from the start.
- `hazard_a`: A is occupied then clears; B is free.
- `hazard_b`: B is occupied then clears; A is free.
- `both_hazard`: both regions are occupied then clear.
- `permanent_block`: at least one region never clears; communication cannot improve route progress within the horizon.

The offline mechanism sweep uses 1,000 paired seeds for every method × network × scenario cell. Random observations and channel states are shared by method through counter-based seed derivation where applicable. Main uncertainty intervals are episode bootstrap intervals, not repeated configuration rows.

The CARLA closed-loop subset uses actual semantic-LiDAR evidence from two elevated roadside regions and a physical ego vehicle. Dynamic instance IDs returned by the sensor are used to reject the known ego and count non-ego actor points inside each spatial ROI; no actor transform or type is read by the normal evidence pipeline. It covers `free` and `hazard_a`, `independent` and `contention`, all seven methods, and five paired seeds: 140 episodes. A fixed 5 s horizon and identical vehicle controller are used. The obstacle in `hazard_a` is removed at 2.5 s. Ground truth actor state is used only for scenario construction and evaluation; selection and the normal controller use received sensor evidence. `full_info` receives the same sensor output without network loss.

## Metrics and tests

Primary mechanism metrics are progress opportunity fraction after the route becomes clear, decision delay after clearance, unsafe-go fraction, useful bytes per successful go decision and deadline-valid evidence-pair probability. Closed-loop metrics are distance, clearance-to-go delay, collision events, waiting fraction, bytes and loop latency.

Report paired differences against `coverage_greedy`, `singleton_voi` and `set_independent`, with seed bootstrap 95% intervals. Also report the frequency of cells in which set methods tie. Do not convert zero observed collisions into zero collision probability.

## Decision rules

- The broad “set utility” claim is supported only if `set_independent` beats both strong non-set baselines in conditions without joint-arrival misspecification.
- The “joint delivery” claim is supported only if `set_joint` beats `set_independent` under contention/burst/short-deadline conditions and does not materially regress under ideal/independent delivery.
- If the gain appears only in deliberately constructed contention or only in the diagnostic free scenario, narrow the paper claim accordingly.
- If strong coverage selection closes the gap, abandon combination selection as the core contribution. If CARLA evidence fails to alter driving or the result depends on ground-truth leakage, reject the experiment.

## Limitations fixed in advance

This suite uses a controlled corridor rather than a natural traffic distribution, simple object/occupancy evidence rather than a learned cooperative perception network, and a software link model rather than a PC5 measurement. Named literature baselines are represented only by transparent mechanism-level analogues and must not be described as official reproductions. The finite suite is a hypothesis test and engineering foundation, not a complete MobiCom paper evaluation.
