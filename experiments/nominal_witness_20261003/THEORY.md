# What a feasible upper witness can and cannot establish

The previous repair study computes a lower bound L on a capped robust horizon H.
For raw observation Y, let A(Y) be the frozen terrain-score acceptance set. For
message m representing a set of observations Y(m), define the message set

    X(m) = union over Y in Y(m) of A(Y), plus the declared unknown region.

Under the same body-disc dynamics and500ms cap,

    H(m) = min(500ms, inf over x in X(m) of first_possible_contact(x)).

This is the existing score/disc model, not a complete physical scene estimator.
The prior class/extent, terrain, sensor transform and motion assumptions remain.
The historical score's deployment coverage has not been established.

## Receiver-only witnesses

Choose one legal observation Y0(m) using the old endpoint at each inlier ball
center and the transmitted current endpoint at each exception. This construction
requires no hidden current raw packet. Since Y0(m) belongs to Y(m), any pose x
accepted by both nested scores on Y0(m) belongs to X(m). Its model contact time
T(x) therefore supplies H(m) <= min(500ms,T(x)). Taking the smallest verified
witness time together with the prior unknown-boundary upper bound is sound.

A heuristic optimizer proposes poses; it does not prove feasibility. Feasibility
is checked with exact integer score comparisons and then independently rescored
using all rays and seven world-coordinate halfspaces. An optimizer failure or
large returned distance never justifies excluding a state. No completeness or
global-optimality claim follows from differential evolution or candidate transfer.
All294912 evaluations are retained; only claims based on independently verified
witnesses are made. Floating-point engineering checks remain distinct from formal
outward-rounded numerical verification.

With the previously audited lower proof, L <= H(m) <= U. Hence a requested
absolute tightness tolerance epsilon requires U-L <= epsilon. This study's pooled
brackets range from32.075ms to430.799ms in width; none meets10ms. Finding accepted
states closes the earlier *missing-upper-witness* problem, not the entire gap.

## Distinguishing raw and communicated evidence

The actual current observation Ya is also a member of Y(m), so A(Ya) is contained
in X(m). Under identical contracts H(m) <= H_raw(Ya). However, the nominal set
A(Y0) need not contain A(Ya), or vice versa. Consequently two heuristic upper
witnesses U_nominal and U_raw need not be ordered, and their difference is not the
true compression loss H_raw-H(m).

The post-search auditor tests the identical fixed candidate pool on Ya. Raw data
does not influence proposal generation. If a nominal witness fails under Ya,
the full coordinates refute that particular state; other adverse states may
remain. Here18/36 closest nominal witnesses fail the actual-raw score. This is
evidence that extra coordinates can disambiguate particular states, not a proof
that sending them restores a positive horizon.

Conversely, an accepted actual-raw witness with time U_raw <=240ms proves
H_raw <=240ms and H(m) <=240ms. The fixed model charges20ms propagation,20ms clock
and200ms action reserve before coding, serialization and computation. Even making
those latter costs zero cannot produce positive remainder in such a task. Seven
tasks have this obstruction. This is stronger than merely observing a slow
implementation, but weaker than a statement about unavoidable physical danger:
changing a justified state or motion contract, the action or reserve can change
the problem. Shortening the reserve without evidence is not a solution.

## Concrete surviving raw witness

The Tesla query at(6,0) admits pose
`[2.4164609984,-0.7404501763,0.6950466749,0.0086351892,2.5038006934,-0.0016354680]`
in the declared local coordinates/radians. On the unperturbed complete stride4
input and its stride16 subset, penetration counts are232/556 and57/142, both
below the frozen28/65 threshold. The independent model contact upper bound is
35.083ms. The same pose passes under both1mm and10mm perturbed actual observations.
This is not a low-support loophole: both ray counts exceed the minimum8.

The pose need not describe the physical actor. It is a counterexample permitted
by the current score. The body disc can also be conservative relative to an
orientation-aware physical footprint. The experiment does not identify how much
of the short horizon belongs to the inverse-score model versus the motion/body
abstraction. Both require validation before general traffic claims.

## Consequence for the research direction

Faster proof search and smaller packets alone cannot remove these seven model
obstructions. A stronger, independently calibrated state model using positive
object evidence and/or a validated directional motion/body contract must be
evaluated against the frozen witness bank and new independent observations.
Tightening the existing threshold on these counterexamples is not fresh risk
calibration. Nor can witness search be claimed as a new optimization algorithm:
the solver is established [SciPy differential evolution](https://docs.scipy.org/doc/scipy-1.10.1/reference/generated/scipy.optimize.differential_evolution.html).
This work contributes a reproducible diagnosis and stronger conditional bounds;
the complete MobiCom research objective remains unachieved.
