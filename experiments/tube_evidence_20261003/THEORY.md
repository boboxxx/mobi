# Current evidence as a set, with a measured price for losing precision

## Meaning of validity under incomplete observations

Let `X(E)` contain every scene state compatible with current evidence E and the
stated sensor, inventory, geometry and motion assumptions. Let `T(x,u)` be the first
violation time for a specified action u. The strongest robust horizon supported
by that information is `H*(E,u) = inf_{x in X(E)} T(x,u)`. A computed lower bound
`L <= H*` permits only times strictly before L. An explicit compatible violation
witness can supply an upper bound U. Reporting `[L,U]` distinguishes insufficient
information from an insufficiently refined computation. A zero L alone proves
neither an imminent collision nor impossibility of a better proof.

If X has simultaneous coverage at least `1-alpha`, and the motion/action contract
holds, a deterministic robust guarantee inside X transfers to a probabilistic
one with that coverage. Conditional-on-action or repeated-time coverage does not
follow automatically from a marginal single-episode calibration. If inventory,
sensor or motion assumptions can fail, their failure events must be included;
no coverage number for them is established here. The current retrospective score
calibration does not establish deployment risk under synthetic or real noise.

The implementation only constructs an outer set of accepted known-shape poses
under the frozen terrain score. It is not a complete scene posterior, an object
inventory estimator, or a universal solution to partial observability. Unknown
space outside the pose prior remains possible. It must not be relabeled free.

## What adaptive communication can preserve without spending extra risk

For a fixed raw-score acceptance set A(Y), let every legal message m generated
from current raw observation Y produce an outer set S(m) with `A(Y) subset S(m)`.
This inclusion must hold pointwise for every Y and every allowed message choice,
not only on average for each radius. If `P[x_true in A(Y)] >= 1-alpha`, then for
ANY data-dependent legal message selector m(Y),

`P[x_true in S(m(Y))] >= P[x_true in A(Y)] >= 1-alpha`.

Furthermore, on that same event, any action selected after receiving the message
is safe strictly before its robust lower horizon, provided the soundness claim is
uniform over all admitted actions and the physical action/motion contracts hold.
Thus data-dependent compression/query selection does not itself require a union
bound when it preserves ONE globally covering state set pointwise. This is a
standard set-containment consequence, not a new conformal theorem.

This does NOT allow choosing a score threshold after inspecting test outcomes,
converting marginal label confidence to physical scene coverage, or making
repeated-time guarantees from single-episode coverage. The current experiment
only tests two fixed static-disc queries, does not certify an unrestricted action
family, and does not implement a costed adaptive-radius controller. This lemma
specifies a sound design requirement; it does not fill those empirical gaps.

## Why a universally positive horizon is impossible

Suppose two admissible worlds generate exactly the same evidence, but in one world
an unobserved object already intersects the queried action region. Every algorithm
receives the same E in both worlds. A positive robust horizon would therefore be
wrong in the second world. In that case H*=0; returning zero is unavoidable
information loss rather than excessive algorithmic conservatism. A calibrated
probabilistic claim can relax worst-case support only under a justified scene law,
not by dropping the inconvenient world after observing the query.

The practical requirement is thus two-sided: retain all admissible uncertainty for
soundness, and quantify the additional algorithmic gap L versus H*. Neither a
longer TTL nor a low empirical collision count alone establishes both properties.
The present study solves a narrower representation/revalidation subproblem; its
broad upper brackets leave the latter optimality question open.

## The receiver's missing coordinates have a concrete representation

A fresh sender reads every current return. Return i is represented either exactly,
or by a Euclidean ball of radius epsilon around the old measured endpoint p_i.
The packet includes a current frame/time, immutable reference digest and compatible
sensor transform, class, calibration and sampling identities. Index alignment is
only valid when count/sampling/transform agree. In-ball membership is asserted by
the sensor encoder; the experiment independently audits it from actual observations.
A checksum detects corruption, not a malicious or miscalibrated sender.

This uncertainty is about withheld CURRENT coordinates. It is distinct from
measurement error relative to the physical surface, which needs its own model.
Missing frames, dropped/unmatched returns and an unknown sensor pose are not covered
by silently assigning epsilon to an old endpoint; the present protocol refuses
incompatible frames. Actual unseen objects remain an inventory problem.

## Endpoint-ball enclosure

For a fixed origin o and parameter t, the nominal ray is `r(t)=o+t(p-o)`.
For any represented endpoint p' with `||p'-p|| <= epsilon`,
`||r'(t)-r(t)|| <= t*epsilon`. The existing score tests intersections only before
`t <= 1+1e-10`; use `delta=epsilon*(1+2e-10)+1e-9` for positive epsilon.
For a continuous pose cell C, the old geometry gives inner/outer oriented boxes
`B- subset B(theta) subset B+` for every theta in C. Erode each inner half-extent
by delta, dilate each outer half-extent by delta; raise/lower the terrain clip
plane `z=.15` by delta respectively. A nominal ray entering the eroded inner set
must enter every compatible true set. A true intersection must have a nominal
intersection with the dilated outer set. Outer exit before the endpoint certifies
penetration; an outer intersection extending to the endpoint remains a possible
non-penetration. These give counts at each of two nested ray budgets:

- n: upper bound on the number of relevant rays;
- m: lower bound on relevant rays;
- k: lower bound on penetrations;
- h: upper bound on non-penetrations.

For m>=8, `max(k/n, 1-h/m, 0)` lower-bounds the fixed raw penetration score.
Otherwise the lower bound is zero. Reject a whole cell only when this lower
bound exceeds the frozen threshold at a calibrated budget. The second term
uses `actual penetrations = actual relevant - actual non-penetrations`.

If erosion empties the inner box, the origin lies in the expanded outer box,
or the original enclosure is unresolved, every uncertain ray contributes the
worst tuple `(1,0,0,1)`. Returning all-zero counts here is unsafe when later mixed
with exact exceptions: it would drop unknown denominators and may create a false
exclusion. The positive-epsilon implementation and regression test enforce this.
For epsilon=0, use the prior exact implementation; unresolved cold cells are never
excluded and are never queried by the warm excluded-leaf path.

These are real-arithmetic arguments. Numerical guards and random differential
tests do not constitute formal outward-rounded floating-point verification.

## Revalidation and expiry

For every old excluded leaf, cache ball counts over all old endpoints. Replace
exceptions by exact current endpoints using:

`current bounded counts = old ball counts - exception old ball counts + exception exact current counts`.

All four counts are additive. This equals a full recheck of the same mixed
ball/exact message. Any old exclusion that no longer passes is revoked; unresolved
old leaves stay possible. Recompute the minimum reachable contact time over the
entire retained union and the unknown boundary. Do not renew the old conclusion
by merely resetting its timestamp. This experiment uses the existing conservative
body disc and fixed speed/acceleration envelope, not a validated physical controller.

On the SAME partition, exact current coordinates can only strengthen the bounded
counts. The independent audit computes both horizons and their difference,
`L_raw_same_partition - L_message >= 0`. This isolates additional warm-message loss within the inherited revalidation
procedure: ONLY formerly excluded leaves are eligible for new exclusion. Old
unresolved leaves remain possible even if a fresh raw evaluation could exclude
them. Therefore this number does not include the uncertainty already paid when
building the cold tree, a full all-leaf raw refinement, the remaining pose-partition
gap, or the body-disc approximation gap.
Across separately constructed partitions, that monotonicity need not be visible.

A usable remainder must charge source construction, encoding, transport, decoding,
verification, initialization backlog, clock uncertainty and action reserve. Larger
endpoint balls save bits and updates but weaken geometric evidence. Therefore the
largest geometric horizon or smallest packet is not the objective. The fixed
matrix evaluates all choices; it does not deploy an oracle that chooses a winning
radius after observing its final outcome.
