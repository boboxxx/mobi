# Query-specific lifetime from incomplete observations

Let I_t contain only observations delivered and checked by the receiver by time t,
and A be the explicit shape, motion, sensor-error, clock and task assumptions.
Let W(I_t,A) be all physical histories compatible with them. The relevant lifetime
is H* = inf over w in W of its first future task violation time relative to the
query reference. An implementable verifier returns a lower bound L <= H*.
A compatible concrete violating history at time U proves H* <= U. Thus [L,U]
measures conservatism; a detector confidence or a fitted average collision time
alone provides neither statement. Bounds here are conditional on A, not calibrated
probabilities and not unconditional real-world safety.

## Backward historical demand

For one class let F0 be the receiver-owned center-free set at historical reference
t0, E0 the additional set excluded by the previously received t0 rays, and E1 the
set excluded by current rays at t1. Projections retain each ray's actual timestamp
and conservatively account for its age, quantization and sensor/pose errors.

Let D bound center displacement from t0 to t1. With acceleration norm bounded by
a and speed caps v0,v1 at the two references, the implementation rounds outward:

    D >= integral_0^dt min(v0+a*s, v1+a*(dt-s)) ds.

These are already available endpoint caps, not an estimate of future speed.
Future reach uses the one-sided bound; the second cap is unavailable in the future.
Let T(L) be all whole grid tiles needed to establish the requested current task
horizon L, including body size, pose margin, clock uncertainty and future travel.
First remove tiles wholly in the erosion F0 (-) ball(D), then tiles wholly in E1.
Call the remaining tile union M. Every historical center capable of occupying M
at t1 belongs to P = M (+) ball(D). Enumerate an outer whole-tile cover of P.
Refuse the proof if unknown exterior centers could reach M from outside the domain.
Remove tiles wholly in F0 or E0. The rest, N, is the additional historical demand.

If additional authentic t0 observations exclude every tile of N, then every tile
of T(L) is center-free at t1. Proof: a center in M would have a t0 predecessor in P.
All P tiles are excluded by F0, E0 or the checked supplement, a contradiction.
The other T(L) tiles were already excluded by inherited freedom or current rays.
The existing future envelope then establishes L under A.

The generation path uses an EDT over grid vertices; the reference checker uses a
KD tree over vertices and independently projects whole-cell negative evidence.
For equal aligned square grid cells, minimum cell-to-cell distance is achieved
at grid vertices (including a shared edge/vertex for intersecting cells). All
thresholds keep their outward/inward rounding convention. A brute box-distance
unit test checks the predecessor primitive independently.

## Causality and authority

A request names an owned positive parent and an actually received failed target.
The sender sees only its eight completed cached source records. A fragment is
bound to its real historical frame and cannot act as a new root. The receiver
verifies the partial proof, then replays only received or paid-backfilled frames
on a shadow state. It preserves global anti-replay maxima. Requests and replies
are bounded, matched, single-flight and checked before authority installation.

Facts and actions have different clocks. An expired fact can support a new proof,
but a 475ms fact completed at age364ms cannot authorize a new action needing200ms:
364+200 >=475. It can still restore the chain so that a later frame becomes usable.
This is why lifetime quality and paid useful coverage are reported separately.

## What is and is not contributed

The candidate contribution is task-proof-guided, retrospective selection of
previously untransmitted negative evidence, with explicit proof-chain repair and
paid causal scheduling. Set-membership filtering, reachable sets, sparse requests,
greedy cover, temporal replay and confidence/risk-based selection are established
ideas; this package does not claim their invention or establish firstness.
The finite traces support the proposed mechanism, not general optimality of the
request policy. Dynamic sensor contracts, useful moving control and real links
remain essential before a MobiCom systems claim.
