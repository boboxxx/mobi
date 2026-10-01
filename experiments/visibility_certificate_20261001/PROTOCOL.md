# Finite visibility-to-expiry study, 2026-10-01

Frozen before new production measurements. Prior 119/120-cell coverage failure motivates this design. No continuous research loop. Negative outcomes remain in the report.

## Conditional problem

The queried action occupies a disk of radius R around a declared point. Every relevant opaque obstacle contains an opaque horizontal disk of radius r_min at the specified probe height and is contained horizontally in a disk of radius r_max about the same center. Accepted first-return rays are correct, with declared planar witness-location error <= epsilon. Obstacles have initial speed <= v and acceleration norm <= a, cannot teleport/appear inside the domain, and probe-plane assumptions continue to hold. Pose, clock and road model bounds are explicit prerequisites, not learned guarantees.

A ray crossing the probe plane before its first return certifies an empty point. Such a witness excludes centers within r_min-epsilon. Cover whole center-space tiles using the nearest-witness distance plus the tile circumradius; every other tile remains potentially occupied. Include outside-domain centers. Take a lower bound on the distance of all possible centers to the action disk inflated by r_max, then invert v*t+a*t^2/2 and subtract clock uncertainty. No polygon interpolation across unobserved rays and no percentage-coverage threshold. Zero expiry is a valid result.

## Fixed validation

1. Unit tests and randomized analytic scenes with opaque disk obstacles: exclusion must never remove a true center under stated bounds; distance/expiry must not exceed earliest modeled collision. Perturb witness coordinates within the declared bound. Test empty scans, true hidden pockets, domain boundaries, bad assumptions and time/packet corruption. 2,000 finite synthetic scenes, also test r_min/r_max classes separately.
2. Replay the four archived CARLA point clouds, without calling replay a new simulator run. Compare the previous strict 0.5m coverage gate, unsafe 99%-coverage relaxation (diagnostic only), and center-exclusion certificates. Report primary grid 0.1m and a 0.05/0.2 sensitivity separately, both views and occupied conditions.
3. New CARLA acquisition on sheng: two mounts, free/near obstacle/far obstacle at fixed offsets, 10 measured frames each (60 total), preserved per-frame origin/XYZ and actor-center evaluation labels. Use both dense rays and predetermined 8-fold thinning. Runtime method cannot access actor labels. Missing returns remain unknown. Exact actor labels are used only to test false center exclusion, not as a sensor model guarantee.
4. Serialize proof witnesses with explicit quantization error and verify on the receiver. Fixed target validity 0.1s and 0.2s; packet corruption/expiry/changed action scope must fail closed. Report actual serialized bytes and verified expiry; do not claim new set-cover theory or wireless hardware measurement.

Primary geometry: query disk R=0.5m; obstacle-class sensitivities (r_min,r_max)=(0.2,0.4),(0.55,2.5); probe z=0.6m above local road, witness error 0.05m, clock error 0.02s, v=5m/s, a=3m/s^2. Domain +/-15m around query; grid 0.1m. These are explicit model assumptions, not universal vehicle/pedestrian specifications. Additional unmodeled geometry should result in a scope limitation, not a post-hoc safety claim.

## Research interpretation

Center-space exclusion, reachability and set cover are established ideas. Evaluate this as an implementable sensing-to-communication interface, not as established MobiCom novelty. A conditional mathematical guarantee does not establish opaque-core assumptions for arbitrary real meshes or detector errors. An impossible observation cannot be made informative by a better scheduler.
