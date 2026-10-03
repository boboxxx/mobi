# A defensible route from incomplete observations to expiry

## Two separate obligations

Let I be the actually received evidence, and W_alpha(I) a set of scene histories
with simultaneous coverage P(W_true in W_alpha(I)) >= 1-alpha under an explicit
episode law. The earliest possible task violation among these histories is

    T*(I,Q) = inf_{w in W_alpha(I)} inf {t >= 0 : Q(t) intersects O_w(t)}.

Before T*, no consistent retained world violates the task. This is a conditional
implication on the coverage event, not a guarantee that a learned posterior is
correct. Unknown objects, incomplete pose enumeration, invalid motion bounds,
unmodeled sensor errors and distribution changes break this implication.

Reliability of W and tightness of T are different obligations. Shape calibration
addresses one necessary coverage component. A lower safe bound L and an actual
retained-world collision witness U bound avoidable conservatism: L <= T* <= U.
No witness means no measured optimality gap. Counterexamples can guide requests
for extra evidence, but the request cannot reset the timestamps of old rays.

## What this experiment proves statistically

Let S_e=max_{v in {0,1}, k in {1,4,16}} score(I_e,v,k, true_box_e).
For 19 exchangeable calibration episodes and one new episode of the SAME class,
q=max of calibration scores implies P(S_new>q) <= 1/20. Missing calibration
episodes use the score upper bound 1. Unsupported rays cause abstention. This
controls rejecting the true supplied box anywhere in this six-case family.
It does not cover arbitrary new budgets, unknown shape families, a detector's
missed inventory, adaptive conditioning on accepted messages, or repeated-time
operation. Class labels/bbox truth used for scoring are evaluation annotations.
No claim of a completed continuous pose/state-set constructor follows.

For a fixed fitted threshold, n=19 calibration samples give only the weaker
distribution-free confidence statement that its tail risk is at most
1 - 0.05^(1/19) = approximately 14.59% with 95% confidence (ties conservative).
Marginal 5% coverage is not a 95%-confidence 5% risk guarantee. At least 59 iid
calibration samples using their maximum would be needed for the latter single
population statement. Independent 20-episode tests also have broad uncertainty.

## Exact finite abstract expiry implementation

lifetime.py implements the subsequent deterministic step for a supplied complete
finite union of uncertain disc states. A state has center c, enclosure radius r
(including initial-position uncertainty), initial speed at most v, and isotropic
acceleration bound a. For a stationary circular task region (q,R), the abstract
reachable disc remains disjoint while

    ||c-q||^2 > [r + R + v*t + (a/2)*t^2]^2.

The receiver takes the earliest boundary over EVERY retained state and returns
the last strictly safe integer microsecond, capped by a caller-supplied horizon.
Rational arithmetic makes rounding conservative. Except for horizon caps, the
minimizing state supplies a collision witness at the next microsecond: choose
initial velocity and acceleration towards q at their bounds. This is exact for
the abstract isotropic disc reachability model, with a <=1 microsecond bracket.
It can still be conservative relative to actual geometry/road dynamics; this is
not a claim of physical optimality. Original evidence age, worst-case clock
offset and requested action reserve are deducted at the receiver.

This module is unit/analytic validated; the new CARLA shape study does NOT feed
a verified complete state set into it. Explicit complete_support is a caller
premise, never inferred from the existence of some detections. Empty/unestablished
support and observations implausibly from the future grant no authority.

## Implication for the research claim

Generic conformal calibration, occupancy filtering and reachability are existing
tools, not this project's demonstrated novelty. The communication question is
whether a small amount of additional, timestamped evidence can remove the
earliest valid counterexample and buy more USABLE lifetime after selection,
transport and verification costs, with controlled episode risk. Previous paid
historical-repair results are conditional on an older abstract geometry model;
they cannot be combined with this shape experiment to claim a validated pipeline.
The missing complete-state interface and useful dynamic control remain explicit.
