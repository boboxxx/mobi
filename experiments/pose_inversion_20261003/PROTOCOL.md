# Finite continuous-pose inversion replay — frozen 2026-10-03

The preceding shape study only queried supplied true boxes. This study implements
a receiver-owned continuous-pose posterior without using true actor coordinates
or a detector output to construct candidate positions. Existing calibration/test
scans are replayed; this is not newly held-out statistical validation. The fixed
score and thresholds are not retrained or tuned. A design-only probe used the
first available Audi/pedestrian calibration view to inspect visibility support.

## Declared operating domain, not a general traffic certificate

Catalog extents/zero bbox rotations come from the 48 design frames. One declared
blueprint per replay, unknown center anywhere in a public road-frame rectangle
[-12,12] x [-8,8] m, all yaw angles, pitch/roll within +/-2 degrees, center height
within bbox extent_z +/-0.1m above the public road reference. These are explicit
flat-ground upright pose assumptions, not learned or proven physical bounds.
Audit actual annotated poses against them; preserve violations, never drop cases.
Outside the XY rectangle, including its boundary, all states remain unknown.
Unknown object counts/types, terrain and tilted/airborne objects outside this law
are not covered by the earlier single-object calibration. The physical gate stays
closed. Successful domain fit in these saved frames is not external validation.

## Fixed queries and information family

For each of six blueprints select test episode indices 0 and 10, view 0. Pedestrian
data/thresholds come from the separately frozen availability follow-up. Missing
selected data yields explicit unavailable output, never substitution. Query
stationary discs of radius0.75m centered at public road offsets (-6,0) and (6,0).
Future speed bound5m/s, acceleration3m/s2, horizon cap500ms, supplied as assumptions.
Use three ordered raw-return budgets: stride16,4,1. At stride4 also retain the
stride16 score constraint; at stride1 retain all three constraints. Thus receiving
more of this predefined information family never enlarges the ideal posterior.
The existing joint threshold protects this fixed family under the earlier law.
It does not protect arbitrary source-selected ray subsets or new traffic scenes.

## Continuous inclusion and algorithm comparison

A pose cell has three center intervals and three Euler intervals. Bound every
possible padded box by one inner and one outer oriented box. At least8 rays must
definitely enter the inner box. A ray crossing the inner box and exiting the outer
box before its first return definitely passes every actual hypothesis. Divide
this definite count by the number possibly entering the outer box to obtain a
lower score bound. Only lower_bound > calibrated_q excludes the WHOLE cell.
Otherwise retain or split it. Unresolved cells are never declared empty.

Compare best-first by earliest possible contact versus FIFO, both with identical
2000 inspected-node caps, score bounds, priors and bytes. This is an established
branch-and-bound comparison, not a novelty claim. Rays outside a conservative
angular cone are skipped via a normalized-direction KD tree; verify against full
rays. Record all tree nodes and reasons so domain coverage/exclusions can be
independently checked. An exact accepted pose or always-unknown boundary supplies
an upper bound on the SAME capped abstract disc-model expiry; unresolved-cell
distance supplies a lower bound. No assertion of physical optimality follows.

## Cost and evidence

Encode ordered sensor-frame float32 xyz without semantic IDs in actual binary
packets with source timestamp, frame, stride/count and transform. Reconstruct all
earlier allowed subsamples from the received packet. Charge measured packet build,
decode/index/solver time plus a labeled model of20Mbps and20ms one-way delay when
reporting usable lower lifetime. Budgets are independent initial transmissions,
not a measured interactive upgrade protocol or live V2X link. Preserve source
timestamps; do not present historical replay time as fresh capture time.

Record144 matched calls (6 types x2 episodes x2 queries x3 budgets x2 policies).
Independent audits must check packet reconstruction, all
tree splits/leaf coverage, exclusion counts, accepted witnesses and L/U ordering.
Run finite tests on sheng; no CARLA server or recurring loop is required.
