# Finite observation-type scaling development probe

All previously published inputs, including the prospective hypotheses test set,
are now development data for this new candidate. The candidate was motivated by
their observed fallback bottleneck; it has no fresh holdout guarantee.

Two fixed families: balanced mean and balanced modes. On supported inputs use
the unchanged trained single/modes local residual scale σ(X), at least 50mm.
Score max(pose violation, nearest outward center error)/σ(X), and expand both
pose and circle by ceil(Q σ(X)). The runtime intersects their distance lower
bounds by cheap max. On unsupported nonempty inputs use the known catalog 3D
body radius b, floored at 50mm, as scale; score max(pose violation, body-ball
violation)/b. Runtime uses the joint body/pose method with ceil(Q b) expansion.
Empty observation refuses. No new model, guard, range, or class-specific tuning.

This changes score units and fallback geometry, not the statistical calibration
rule. Every family's one episode score is the maximum across all its emitted
source sets, regardless of type. No independent type-conditional guarantee is
claimed. If a supported score is covered, both pose and circle contain the
center; if a fallback score is covered, both its body/pose constraints do.
For an independent frozen-score batch the usual whole-episode maximum tolerance
bound would still apply. This development probe cannot use that future bound.

Source relative query radius750mm, motion5t+1.5t² and cap500ms stay unchanged.
No full computation/link utility is claimed by the development geometry probe.
Predictor replay is shared; rational scores/sets/ages are independently audited.
All outcomes including exclusions, worse queries and overstatements are retained.

Also compute descriptive grant-conditional center-exclusion bounds for the OLD
frozen policies, with one Bernoulli sample per complete test episode, class
separately, selected if any grant, failed if a grant references an excluded
source. There are 6classes ×8methods ×2rates ×2startups=192 comparisons. Do not
count queries as independent, pool stratified classes as iid, or attribute old
measured profiles to the new candidate. Exact binomial upper bounds with
Bonferroni δ=.05/192 require at least161 selected zero-failure episodes for a
5% guarantee. The old60/class cannot suffice. This is standard selective risk
testing, not a claimed new theorem.

Freeze code/dependencies before running this finite probe on sheng. Do not alter
the candidate based on its development outputs during this probe. Results may
justify or kill a new independently frozen experiment; no recurring loop.
