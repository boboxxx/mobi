# Observation validity and action admissibility are different statements

This note formalizes a conditional interface implemented in `lease.py`. It does
not establish physical sensor/actuator bounds, maximal permissiveness, or a new
control theorem beyond existing robust safety-filter principles.

## 1. What incomplete observations can establish

Let D contain authenticated first-return rays and their individual observation
times. Let A specify valid sensor/pose/clock bounds, a complete set of relevant
obstacle classes, their opaque inner cores, outer radii and motion bounds. Let
W(D,A) be all physical worlds consistent with D and A. Assume A is valid and
W(D,A) is nonempty; inconsistent assumptions cannot supply a physical guarantee.
For a region R, define

H*(D,R,A) = sup { h >= 0 : for every w in W(D,A), for every t in
[t_ref,t_ref+h], the relevant obstacle occupancy O_w(t) does not intersect R }.

This is a *conditional robust* validity definition. A ray does not prove that an
unobserved cell is empty. Without restrictions on object size, opacity, speed,
and observation errors, indistinguishable worlds can contain an imminent hidden
collision, so a useful positive worst-case lifetime need not exist. Fitting a
confidence score alone does not remove this indistinguishability.

The existing raw-ray verifier computes a sufficient condition, not H* exactly.
For obstacle class c, it covers every grid cell that may contain a dangerous
center within the requested horizon. A cell with center z, half diagonal d_cell,
and ray witness w_i is excluded only if

    ||z - w_i|| + e_i + d_cell + epsilon < r_min,c.

The reconstruction of e_i includes projection, quantization, pose/query error,
per-ray age and the stipulated obstacle motion during that age. The dangerous
center region is the requested free region expanded by outer object radius and
maximum travel up to the horizon (including the stipulated clock error). The
whole expanded region must lie inside the verified domain. Every required class
must pass. The code preserves these existing checks without changing raw rays,
errors, shape contracts or geometric expiry.

Because the coverage test explicitly covers a rounded rectangular region
R = B + disk(m), its successful output entails that region is free until the
verified expiry E under A. The numerical parameters used to *construct B and m*
need not themselves be realizable vehicle dynamics for this geometric entailment
to hold: the receiver verifies the region they describe. They must be finite and
admitted by the checked geometry schema. This distinction permits reuse of the
verified region for a separately bounded action.

## 2. A current-state action must fit both space and time

At decision time t, use measured current speed v and an independently justified
speed error e_v. Suppose the next command lasts at most C, the backup becomes
effective within r more seconds, forward speed growth before backup is at most
a, and subsequent braking reduces speed by at least b until zero. Let

    v0 = v + e_v, q = C + r, vp = v0 + a*q,
    T = q + vp/b,
    S = v0*q + a*q*q/2 + vp*vp/(2*b).

Under those external assumptions, T bounds the complete command/backup duration
and S bounds its forward path length before terminal residual drift. With yaw
rate omega, slip beta, half-body dimensions L,W, full-body pose discrepancy e_p,
and residual speed v_res, the implementation encloses the entire maneuver in

    K = [-L, L+S] × [-W-S*sin(omega*T+beta), W+S*sin(omega*T+beta)]
        + disk(e_p + 2*hypot(L,W)*sin(min(pi,omega*T)/2) + v_res*T),

then rotates/translates K by the current pose. It rejects omega*T+beta >= pi/2.
The assumptions include initially forward motion consistent with the stated
slip bound, a valid body/pose enclosure, correct state timestamps, and bounded
terminal drift. These assumptions are not certified by this formula.

Admit the next command only if K is contained in the already verified R and

    ceil(1e6*t) + ceil(1e6*T) < E_us.

For a fixed current state and bounds, the largest permitted integer start tick
is E_us - ceil(1e6*T) - 1, provided containment holds. This is not a deadline that
can be reused after the state changes: containment and T must be recomputed.
The condition no longer requires evidence age <= a fixed 120 ms hold budget.
It does not extend E or prove that the trajectory before t was safe.

Containment is checked by transforming the four corners of the maneuver's core
rectangle into the free-region coordinate frame. For each corner p, compute
the signed distance to B. Require signed_distance(p,B) + maneuver_margin < m,
with a numerical guard. Each corner-centered disk is then inside R; their
convex hull contains the whole rounded maneuver rectangle. This is a sufficient
test. A passing test establishes K subset R, not optimality of either enclosure.

## 3. Conditional finite handoff, with an external watchdog

Keep the previous fully checked command/backup commitment while a new packet is
being verified. Replace it only after current-ray reconstruction, scope and
monotone time/sequence checks, current-state containment and completion-before-
expiry all succeed. Corrupt, replayed, out-of-scope, future, late and invented
packet identities cannot reset the commitment. The checksum alone is not sensor
authentication; authentication and trusted scope configuration remain external.

The command deadline is rounded DOWN, and an independent actuator watchdog must
enforce it despite any sensing/verifying/network stall. If no replacement is
accepted, the precommitted backup supplies only its original finite interval.
After completion the interface returns NO_GUARANTEE; a stationary car is not an
infinite-horizon invariant safe set against moving obstacles. An observed speed
or body-envelope breach latches CONTRACT_BREACH and requests full braking. This
monitor can discover a falsification; absence of a sampled breach does not prove
the continuous physical assumptions.

If the initial commitment is valid and all external contracts and watchdog
obligations hold, each accepted handoff covers its new complete maneuver; each
rejection preserves the old finite backup. This finite induction does not prove
that a new lease always exists. Actual CARLA driving must additionally solve
self-occlusion and legitimate initialization; the current saved-data replay
only checks independent counterfactual current states.

## 4. Where conservatism was reduced, and where it remains

This interface removes one unnecessary coupling: geometric evidence was tied
to an old hold/go/brake schedule even when it could cover a new maneuver from
the current state. It does not remove grid inflation, uniform region lifetime,
bounding-box conservatism, worst-case obstacle motion or actuator uncertainty.
The observed age-grid improvement is an empirical property of this dataset;
neither universal dominance over the old policy nor maximal H* is proved.

Safety supervision with a saved backup is established prior work. For example,
[Nezami et al., 2022](https://arxiv.org/pdf/2206.09735), Sections IV–V,
construct robust tube-MPC supervision and prove backup/recursive feasibility
under bounded disturbances and a terminal invariant set. Our finite geometry
kernel does not reproduce that terminal-set guarantee. Any research novelty
must instead be established for observation-derived, receiver-checkable validity
and its communication/computation tradeoffs, against strong matched baselines.
