# Fixed free-region handoff diagnostic

Use all 1,044 cases from the frozen binary-combined runtime stage, including
every failed geometry case, and its 87 saved immutable PVX1 packets. Recheck
every available packet on sheng. Per episode/speed/horizon, maintain independent
monotone receiver state and current-ray index hints. Check the recorded packet
hash before use. Retain the old acquisition and source-generation times and
20 ms stipulated link, replace the old receiver time by the new measured reader
time, then include the measured new gate computation once. Also report a fixed
additional 1 ms sensitivity. These are hybrid saved-data timing diagnostics,
not fresh end-to-end network measurements.

The counterfactual current position is query + initial speed * evidence age along
the packet yaw, with unchanged current speed. Each case is independent. This is
not a reconstructed continuous trajectory, a proven safe waiting policy, or a
claim that the physical controller follows constant velocity. Compare the old
hold/go/brake timing predicate and the new complete command/backup containment
gate at the SAME final time and current packet. No parameter tuning after results.

The new gate uses the existing default external actuation bounds, including
traction 3 m/s², braking 4 m/s², 20 ms reaction, 50 ms command and 20 mm/s current
speed uncertainty. The actual actuator diagnostics have already disproved
promoting those bounds to unconditional CARLA guarantees. Every output must
therefore have physical_movement_authorized=false.

In addition, evaluate a deterministic age grid 0..500 ms in 1 ms steps on each
verified region, comparing old and new gates at identical hypothetical ages.
Report full sets/counts and longest admitted age, including non-contiguous sets;
do not silently call the largest passing grid point a continuous validity bound.
This separates the interface's logical effect from machine timing fluctuations.

No changing the underlying sensor, obstacle, error, packet, or region contracts.
No unregistered initial-free premise, expiry reset, infinite stop guarantee or
data-derived hard physical bound. The independent watchdog is an external
execution requirement; this saved-data replay does not implement that actuator.
