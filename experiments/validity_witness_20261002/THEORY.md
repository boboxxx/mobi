# Conditional validity with a measurable conservatism gap

Let O be the complete actually received negative-ray history and trusted prefix,
C its explicit aligned-timestamp, source, quantization, pose, probe-plane/core/outer and
motion contracts, and R the stipulated stationary protected rectangle. All
required classes participate. Let M(O,C) contain every persistent hidden-world
trajectory population consistent with that information. Define

    H*(O,C,R) = inf_{world in M(O,C)} first dangerous time for R after reference.

This is a continuous occupancy lifetime from source reference. It is not the
probability of collision, a point prediction, or safety only on a late isolated
action interval. The saved replay stipulates truthful relative ray timestamps
in a common phase and uses the existing20ms FUTURE clock allowance. Arbitrary
unknown packet-wise clock offset/drift is not covered or calibrated. The lower
proof retains that future allowance and the specified ego pose allowance. An
upper witness chooses the nominal pose/timing realization while remaining
robust to all given endpoint errors.

The previously independently verified conservative observer proves every
trajectory safe up to L (strict expiry semantics). An individually verified
admissible hidden trajectory entering even the nominal rectangle by U gives

    L <= H* <= U.

Therefore the missed usable lifetime is bounded by U-L. For L>0,U>0,
relative lifetime lost against H* is at most 1-L/U. L=0 does not prove that H*
is zero; a restricted search finding only a late U does not prove an earlier
trajectory impossible. If no witness is found, U is unknown, not infinity.
For the joint task, L=min class lower bounds and U=min any verified class
witness time. Shape/core, task, received history and clock allowances must match.

The lower bound uses conservative tile support and the existing two-endpoint
PAST integration. This integration and set filtering are established ideas;
no novel theorem/optimality is claimed. A terminal speed bound is used only
after the corresponding observation has arrived and passed checks. Future
travel remains one-sided. Finite receiver fact memory remains separate from
finite action authority. For a requested200ms action reserve and delivery/
verification age A, admission still requires A+200ms<L. Witness search time is
offline diagnostic cost, not a way to turn a stale lower proof into authority.

## Constructive witnesses

At every actually received ray timestamp, speed is5m/s. Between two consecutive
timestamps separated by d seconds, velocity is continuous along one fixed
inward direction. It accelerates at3m/s² for d/2 then decelerates at3 for d/2.
Its displacement is5d+3d²/4. Prior to the first sample speed is constant5;
after the last it accelerates inward at3. Acceleration norm is bounded almost
everywhere; the original model has no jerk bound. Actual timestamps are integer
microseconds; independent integration uses exact rational arithmetic. The
reference age after the final actual sample is integrated separately.

The opaque sphere and ellipsoid candidates are subsets of the allowed shape
class. A sphere has radius r_min. An ellipsoid contains that sphere and has
outer semiaxis<=r_max. Their centers lie on the agreed probe plane. All full3D
selected ray segments, including endpoints, remain clear at their actual
timestamps. A Euclidean endpoint Hausdorff error bound epsilon gives spherical
clearance r_min+epsilon. Ellipsoid whitening has norm1/r_min; normalized
clearance1+epsilon/r_min suffices. Both use an additional strict numerical guard.
Any finite-family failure leaves arbitrary curved/differently shaped candidates
unresolved. World objects may start outside the computational window; no
unverified root-free region or spontaneous birth is introduced.

These candidates meet the original abstract core/extent/kinematic ray model.
They need not follow roads or avoid walls/terrain: those conditions were not
part of C. This is not an alternative full physical CARLA world or an actual
Audi collision theorem. A stronger lower bound based on full3D spherical cores
cannot be silently substituted for the original weaker plane-core contract.

## Communication matters

O contains selected transmitted rays. The sender's full current scan can have
additional valid rays. A one-ray fact whose error-bounded plane crossing lies
inside a candidate's core refutes that candidate. It changes O; the old witness
must then be rechecked, and the whole safety certificate must be recomputed.
Refuting one trajectory never establishes a new L. Full scan acquisition,
selection, transport and receiver recomputation all consume usable lifetime.

A defensible research question is whether a communication system can reduce
the certified gap efficiently, reporting unknown cases honestly. It needs
evidence selection, matched strong baselines, paid delivery/verification and
loss handling, rather than unqualified maximum-TTL claims. The present finite
implementation supplies verified lower/upper diagnostics and additional-ray
refutations, not an optimal online evidence-selection/control system.
