# Fresh matched local-repair integration, frozen before capture

Eight finite runs: two RSU layouts from the previous study, two algorithms
(original fast support renewal / local repair), two ordered repetitions. For
each layout run original then repair in repetition 0, repair then original in
repetition 1. This balances order but is not eight independent road scenarios.
Both algorithms get receiver-owned history, the same compressed cold fallback,
and the same maximum three root attempts. No adverse run is replaced.

Unchanged: Town10HD_Opt first straight corridor 25 m ahead, ClearNoon, Audi A2,
256-channel 2M-ray/s LiDAR; two obstacle profiles, 10 mm point/origin/query boxes,
2.3 by 1.3 m region half extents plus .03 m margin, .4 s geometric lifetime,
.5 m/s relay target, previously frozen constant maneuver model, 50 ms physics,
20 brake-warm decisions, 40 driving-phase decisions, indices 20..24 packet drop.
All source rays are current and every accepted proof is fully receiver-verified.
The original calibration risk statement is NOT reused for adaptive driving.

Shared control integration correction: a verified region is independent of the
particular action chosen when it arrived. While perception is processing, the
local driver may reconsider a fresh one-tick command at EACH physics tick using
CURRENT state and the last region that has FINISHED processing/transport. Each
command still needs full maneuver containment and strict completion before the
UNCHANGED expiry. No in-flight proof is exposed to this local gate. If the gate
fails or a sampled contract breach latches, full brake applies after the old
one-tick command. This change applies equally to both source algorithms. It
prevents an artificial requirement to wait for a new packet for every action.

Measure acquisition, source generation, verification, plus fixed modeled 20 ms
link; advance ceil(total/.05) physics ticks before exposing each new result.
Local gate wall time is recorded; it is a tick-local cost, not an independently
certified WCET. This remains synchronous measured-delay co-simulation, not
real-time wall-clock or wireless driving. Logging and environment RPC overhead
are not a deployed scheduling guarantee. The link is not byte-sensitive yet.

Record each pre-tick gate outcome, cached lease identity/availability time,
actual applied command, full 3D body and current state; preserve every point
cloud, packet, rejected root, dropped packet, expiry and model breach. Close
the drive phase then flush 40 braking ticks. If no forward action occurs,
report failure; dropout flags with no usable message are not a nonempty fallback
experiment. No scheduled/continuing research loop is created.
