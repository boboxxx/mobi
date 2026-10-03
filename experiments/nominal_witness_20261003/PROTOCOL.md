# Finite receiver-only feasible-state search

Declared after the proof-repair study and before executing this search. This is
offline diagnosis on reused observations, not new risk validation or an online
policy improvement. Preserve the frozen score, threshold, prior and motion model.

Use all36 proof-repair tasks: six classes, two queries and the three fixed pairs
(radius0,sigma0), (radius5mm,sigma1mm), (radius50mm,sigma10mm). Reconstruct one legal
raw observation from receiver information only: old endpoints for inlier balls,
and the transmitted exact endpoints for exceptions. Do not load current raw point
packets or actor-pose labels. Source extent/road/anchor metadata are the inherited
declared contract, not newly inferred information.

Search the complete six-dimensional pose prior for accepted poses. Initial
population256:128 scrambled Sobol poses and128 data proposals from16 most populated
0.5m XY bins of nominal endpoints above0.3m and below2*extent_z+0.3m, using eight
evenly spaced yaws. Bin means seed XY only; z is extent_z, pitch/roll zero. Missing
bins fall back to Sobol poses. No class-specific hand tuning or actor truth seeds.

Run scipy differential_evolution with this population,31 iterations, mutation
(0.5,1), recombination0.7, deferred/vectorized updates, no polish, tol=atol=0,
seed31003+task index. At most8192 evaluated poses per task (early convergence may
stop sooner). Exact integer score comparisons determine acceptance at both nested
ray budgets. Feasible objective is distance/30; infeasible objective is
2+max_positive_score_violation+0.01*distance/30. Keep every evaluation and every
successive best feasible-distance candidate. This heuristic has no completeness
guarantee; failure to find a witness does not prove infeasibility.

Each best accepted pose supplies a candidate upper bound for the message's union
of accepted states under legal raw realizations. Independently rescore every
successive best witness with all nominal rays using the Python world-plane
reference and high-precision contact-time calculation. Also compare32 fixed-index
evaluations per task to detect scorer errors. Verify nominal membership, all input
and output hashes, prior inclusion and the already audited4096-visit lower bound.

Keep upper bounds no larger than the previous unknown-boundary/cap bound. Report
all36 brackets and unresolved gaps. Search time is offline and cannot be charged
as free assistance to the earlier online results. A nominal-message witness is
not necessarily a witness for the hidden actual current cloud or physical mesh.
