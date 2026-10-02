# Finite physical-contract falsification, frozen before new capture

The historical-repair algorithm is conditional on every relevant obstacle having
an opaque horizontal core and a bounded outer footprint about the SAME center.
An enclosing bounding box does not prove an opaque core. Before new dynamic
performance claims, attempt to falsify the existing r_min/r_max assumptions using
new CARLA0.9.15 semantic LiDAR scans and independently recorded actor state.

Use the existing first straight Town10HD_Opt corridor25m-ahead rule, ClearNoon,
50ms synchronous physics and the unchanged256-channel2M-point/s20Hz semantic
LiDAR (35m,10/-90deg). Two existing RSU mounts:4m lateral/8m high and8m lateral/6m
high. Fixed task plane = corridor reference z +0.6m. Six blueprints in this order:
vehicle.audi.a2, vehicle.tesla.model3, vehicle.mercedes.sprinter,
vehicle.diamondback.century, vehicle.kawasaki.ninja, walker.pedestrian.0001.
Class vehicle uses(.55,2.5)m; walker uses(.2,.4)m. Four yaw offsets0/90/180/270.
One settled static actor at the task center per condition, no ego controller.
Total48 frames; missing blueprints/spawn failures are recorded, not substituted.
Freeze settled pose for each yaw to isolate geometry. This does not validate
moving-object contracts or actual driving. No model tuning on these48 frames.

Save exact raw semantic LiDAR bytes, sensor transform/time/frame, world pointcloud,
actor transform and bounding box vertices, actual velocity/acceleration, blueprint
and tags. Ground-truth actor identity/pose are audit-only and never encoder inputs.
Record same-frame snapshot identity. Retain every outcome and all failed probes.
Capture has a dedicated30-minute server cap, cleans only actors it created and
restores prior settings; no recurring loop. Do not start if another CARLA exists.

For each actual obstacle center, independently test whether any observed
first-return ray crosses the declared probe plane inside its claimed opaque core.
Use the unchanged quantization/error projection kernel as a separate operational
check: can its negative evidence exclude the grid tile containing the actual
center? Preserve the most decisive exact source ray and reference calculations.
A robust contradictory ray falsifies the declared observation/core interpretation
for that condition; no contradiction does NOT certify the continuous object mesh.

Also report the maximum radius of actual LiDAR returns tagged with that actor and
of its transformed bounding-box vertices. An actual return outside r_max directly
refutes the outer envelope; a bounding box outside r_max only shows that the box
cannot establish containment (its corners need not lie on the physical surface).
Do not confuse enclosing geometry with a solid interior or classify a missing
return as empty. Frame-simultaneous ideal semantic LiDAR is not a noisy physical
sensor, and no real-world statistical calibration follows from this finite test.

If the old contract fails, preserve old conditional mathematics/results, record
which deployment interpretation is invalid, and implement a fail-closed eligibility
boundary before feeding affected observations to a safety-authority path. Do not
repair a failed universal claim by choosing a smaller core on the same test data
and reporting the same data as validation. Further representation changes or
held-out calibration require a separately declared follow-up.
