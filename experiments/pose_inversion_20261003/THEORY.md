# Continuous pose inclusion, score bounds and the meaning of a zero lifetime

The previous score model supplies marginal retention of a true given box under
its fixed calibration law. Inverting it requires considering all possible poses,
not substituting the true box center into a receiver algorithm. This study's
operating domain is explicit and restrictive: known catalog shape, flat-road
height band, upright pitch/roll, all yaw angles, and unknown horizontal position.
All XY positions outside the computational rectangle remain unknown. Natural
traffic inventory, new object shapes, terrain and pose/motion contracts are not
validated by this finite replay.

## Continuous enclosure

For a cell C in xyz/pitch/yaw/roll, let B_theta be the padded hypothesis box.
Construct B_minus subset B_theta subset B_plus for every theta in C. The initial
implementation uses a rotation displacement norm plus axis-specific translation
bounds. The refined implementation writes R0^T R(theta)=Ay Ap Ar, fixed-axis
rotations for yaw, pitch and roll perturbations. Rodrigues' formula bounds each
absolute perturbation by

    |A-I| <= sin_max(h) |[u]_cross| + (1-cos_max_angle(h)) |u u^T-I|.

Expanding the product bounds |R0^T R-I| by a nonnegative matrix D. For padded
extent e and representative-frame translation half-width t, valid box extents are

    outer = e + D e + t,
    inner = e - D^T(e+t) - t.

Negative inner extents mean unresolved, never empty. The inner formula follows
from bounding the actual-frame coordinates C^T(x-delta_center), using |x|<=inner
and inner<=e. The outer formula bounds vertices in the representative frame.

## Lower bounds on the fixed point score

Let N_minus be rays definitely eligible through B_minus, N_plus the rays possibly
eligible through B_plus, P_minus rays that enter B_minus and leave B_plus before
their first return, and H_plus possibly eligible rays that have NOT exited B_plus
before the return. If the origin might lie inside a hypothesis or N_minus<8,
return lower score zero. Otherwise

    score(theta) >= P_minus / N_plus,
    score(theta) = 1 - H(theta)/N(theta)
                 >= max(0, 1-H_plus/N_minus).

Taking the maximum is valid and retains the dependence between the score's
numerator and denominator. For example, an outer box with no possible interior
returns has score lower bound one whenever support is sufficient. A bound above
the frozen calibration quantile removes the entire cell. Other cells are split
or retained. Point samples can supply feasible witnesses but cannot remove a cell.

The KD-tree prefilter only omits ray directions outside the cone subtended by an
outer enclosing sphere. Every excluded real-data cell would be checked again
using all rays by the independent auditor. In this actual run there are zero such
exclusions, so that real-data exclusion audit is vacuous; randomized geometry
tests and analytic inclusion arguments are the substantive evidence for bounds.

## Complete computational coverage is not complete physical modeling

Every root-to-leaf split partitions one interval, and unresolved leaves remain.
Their union therefore outer-encloses the exact score-accepted pose set inside the
declared prior. This is continuous coverage; it does not assert all retained cells
are possible or identify the true pose. Here no cell was excluded within the node
budget, so the returned outer union still equals the prior, despite many splits.

For each information stage, retain the score constraints from all earlier fixed
subsamples: W_16 contains W_4 contains W_1. This avoids forgetting a valid old
constraint when a denser cloud changes the penetration fraction. Arbitrary ray
selection is not covered by the existing calibration.

Within the constructed disc-motion abstraction, each retained cell's nearest
possible center gives a lower time bound. An exactly accepted pose, or an always
unknown boundary state, supplies an upper bound on the SAME capped500ms problem.
The footprint disc radius is the enclosing3D bbox radius, rounded outward. Future
translation has assumed initial speed5m/s and acceleration3m/s2. These upper
witnesses are valid for this deliberately enlarged disc model, not necessarily
for the exact body geometry, road-constrained motion or a physical CARLA mesh.

This distinction matters empirically: some zero-time disc witnesses do not even
overlap the query using their tighter projected bounding box. Even bbox overlap
does not establish a mesh collision, since the interior can be empty. A positive
upper bound from a finite witness bank also does not establish positive optimal
lifetime: an undiscovered earlier witness may exist. A zero upper bound does prove
zero for the constructed score/disc model, subject to the stated arithmetic model.

## Numerical and statistical scope

Integer/rational prior lifetime code is checked with a separate70-digit analytic
reference. New geometric code uses float64 with explicit outward engineering
guards; containment regressions and independent face intersections check it, but
this is not a formally verified directed-rounding interval implementation. The
real-arithmetic derivation must not be promoted into an unconditional machine or
physical guarantee. The earlier calibration's single-object marginal law remains
unchanged; this replay is not new evidence for its population risk.

## Scientific consequence

True-hypothesis retention can coexist with a very broad set of false poses and
zero useful expiry. Computing that set more carefully is necessary for diagnosis,
but does not repair a weak measurement model. A calibrated pose-localizing front
end and an orientation-aware, validated trajectory enclosure are needed before
claiming useful driving authority. Communicating an entire raw cloud also misses
the modeled deadline here even with zero computation. The next candidate must
jointly provide sharper task-relevant state constraints and compact messages;
it cannot rely on the preceding calibrated box fraction alone.
