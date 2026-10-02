# Fresh finite online evidence batch, frozen before capture

Ten runs in Town10HD_Opt, ClearNoon, CARLA 0.9.15. Three deterministic straight
corridors: collect prior first-straight targets 25 m ahead, keep targets separated
by >=15 m, use the first three. This gives geographically different controlled
corridors, not statistically independent natural traffic. For each corridor,
view0 RSU (4 m lateral, 8 m high), pair generalized original repair and coverage
reuse at the SAME 475 ms target and one-thread library configuration. Use a
modeled 20 Mbps link with 20 ms fixed overhead. Reverse method order in corridor1.
Add two corridor0/view0 runs with 20 ms-only link to expose byte-cost effects,
and two corridor0/view1 (8 m lateral,6 m high) 20 Mbps negative controls. Thus
six corridor-paired rate-limited runs, two fixed-link ablations, two sparse-view
controls; no adverse run is replaced. Reference and reuse produce the same
packet on an identical input. Trajectories may diverge due to measured costs.

475 ms is a fixed requested proof horizon, chosen after the archived root
frontier was 480.303 ms. It is NOT an online maximal-horizon claim. The actual
current rays/history must certify each packet at that requested horizon; failed
renewals use the same complete compressed fallback. Both methods start without
history, with maximum 3 roots. A late but verified root may supply a geometric
proposal template, but cannot supply live prior occupancy. Strict integer
arrival expiry and a conservative 50,001 us next-sample reservation apply.

Keep the full-body 2.3 x 1.3 half-extents/.03 margin, opaque-core/motion/error
contracts, 256-channel 2M/20Hz LiDAR, the frozen 200 ms sampled maneuver envelope,
.5 m/s relay target, per-physics-tick completed-cache gate, 20 warm decisions,
40 drive decisions, drive indices20..24 message drop, and 40 final brake ticks.
Every received packet is fully verified by the unchanged receiver geometry.
Measure acquisition, source and verification, plus modeled link duration:
20 ms + packet_bytes*8 / 20e6 (or 20 ms for fixed-link ablation). Advance the
ceil-to-50ms sum before exposing a proof. A dropped valid packet still consumes
modeled link time; receiver verification is skipped. Source production continues.

Save every cloud, packet, current state, actual control, cache arrival, rejected
root, expiry, drop and sampled breach. Log corridor pose, method, link and target
horizon. Final replay regenerates source output; checks original/reuse byte
identity on the actual inputs, full-reference receiver equivalence, strict
arrival/root boundaries, wire delay, and each applied control/body observation.
A nonempty dropout/backup observation requires actual movement and valid messages
suppressed; missing proof with stationary ego does not satisfy it. Return full
brake on failure and preserve all negative outcomes. Controlled pre-ego external
clearance and statistical actuation component assumptions remain explicit.

This is finite measured-delay synchronous co-simulation, not real-time WCET,
physical road safety or actual wireless transport. Dedicated server lifetime is
30 minutes and is stopped after the finite capture. No recurring loop is created.
