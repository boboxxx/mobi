# Finite tighter-bound follow-up — 2026-10-03

The original144-call replay is preserved. It reveals very loose continuous-cell
bounds under the2000-node cap. This engineering follow-up uses the same saved
sources, thresholds, queries, byte budgets and two schedulers, with144 further
calls. It is not an independent statistical test or a changed point-score model.
The implementation was first checked on the same Audi calibration design frame
and randomized geometric regressions, not tuned by varying test thresholds.

Two analytic changes tighten the lower score bound while leaving the exact
posterior unchanged. First, bound relative Euler rotations componentwise via
fixed-axis Rodrigues matrix perturbations instead of one isotropic displacement.
Second, also use score=1-nonpassing/eligible: possible_nonpassing is bounded using
the outer box, while definitely_eligible comes from the inner box. Their bound
max(0,1-possible_nonpassing/definitely_eligible) preserves count dependence that
the separate definitely_passing/possibly_eligible ratio loses. Take the maximum
of the two valid lower bounds. Require at least8 definite eligible rays.

Full-ray independent audits must verify exclusions and witnesses. Budget exhaustion
remains unknown/retained. No claim that generic interval tightening is novel or
that this unvalidated upright operating domain establishes physical safety.
