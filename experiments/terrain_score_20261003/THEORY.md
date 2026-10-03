# What terrain clipping does, and what a trustworthy expiry requires

Let B(x) be a padded oriented box at pose x. Replace the old measurement shape by
K(x)=B(x) intersection {z>=0.15m}. This is a scoring construction, not an assumption
that every box interior is opaque. A measured return supplies only its observed
ray segment. A ray is eligible if it encounters K before its return; it is a
penetration if it leaves K strictly before that return. Keep score0 (non-exclusion)
for fewer than8 eligible rays, unavailable observations, or a sensor inside K.
Never discard a ground-hit ray: it may observe an entire above-ground segment.

The intersection along a ray is obtained from six box slabs plus a seventh world
halfspace. Each contributes an interval in ray parameter t. Their intersection
with t>=0 is exact in real arithmetic. The numerical implementation uses the
same engineering tolerances as the previous score, not verified directed rounding.

For a fixed pose cell C, inherited enclosures give Bminus subset B(x) subset Bplus.
Intersection with the SAME fixed halfspace preserves both inclusions. Therefore
Kminus subset K(x) subset Kplus. Inner-ray hits yield Nminus; outer-ray hits Nplus;
inner hits which exit the outer before the measured return yield Pminus. Let Hplus
count outer-eligible rays not known to exit before the return. If Nminus>=8,

    score(x) >= max(Pminus/Nplus, 1-Hplus/Nminus, 0), for every x in C.

Otherwise use lower bound0. Whole-cell exclusion requires a strict lower bound
above the newly calibrated q. KD angular prefiltering uses the uncut outer box,
so it can add extra candidates but cannot intentionally omit clipped-box rays.
Unresolved cells and outside-domain states remain possible. This is a conservative
continuous-set algorithm; the independent audit rechecks exclusions with all rays,
without the KD prefilter or tested intersection implementation.

For a prospectively fixed score, define one episode score as the maximum over
all prespecified views and budgets. The maximum19 calibration scores is the
usual rank19 threshold for nominal marginal5% exclusion under exchangeability.
A missing full episode has exclusion score0 only because the corresponding
procedure retains full support/refuses action. Hypothesis-specific sparse support
also retains that hypothesis. This is not95%-confidence conditional5% error, and
not an infinite-sequence or selected-update guarantee. The present repair was
motivated by inspected test failures; it requires a fresh prospective evaluation.

Given a correctly covered state set C and a valid future dynamics family, a task
expiry lower bound is L <= inf_{x in C, admissible future} T_failure(x). A retained
state plus an admissible failure trajectory supplies an upper bound U. Then U-L
bounds numerical conservatism within THAT observation/dynamics abstraction. It
cannot measure error introduced by an inaccurate body model, unmodeled actors,
terrain assumptions, or the score's broad acceptance region. This experiment's
body-disc witnesses are not automatically feasible CARLA mesh trajectories.

The actionable remainder is max(0,L-source_age-processing/transport/clock/action
reserves), with each cost counted exactly once. A positive offline geometric L
is not a timely grant when inversion itself exceeds the horizon. Current program
results deliberately preserve unresolved brackets rather than pick a midpoint.
No physical action gate is enabled by this retrospective study.
