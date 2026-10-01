# Finite actual-ego integration diagnostic

Frozen before fresh capture. Four runs: two RSU layouts (lateral/height 4/8 and
8/6 m), each with current-rays-only and receiver-owned history. Same first
straight nonjunction corridor (25 m ahead) as prior ray studies, Audi A2,
ClearNoon, semantic LiDAR 256 channels / 2M points/s / 20 Hz; XYZ only enters
proof generation. No semantic object IDs or obstacle labels enter the proof.

Before creating the ego vehicle, attempt at most three root proofs from fresh
actual rays. A fully receiver-verified root asserts absence of modeled EXTERNAL
obstacles in a fixed rounded rectangle, half-length 2.3 m, half-width 1.3 m,
margin .03 m, for .4 s. Creating the registered own vehicle changes the modeled
world only by adding that known ego; its own occupancy is excluded from the
external-obstacle proposition. No other actors are spawned during the run.
This controlled initialization is not deployable initialization on a road.
A missing/expired root is failure, never replaced by a free Boolean or oracle.

Use the existing strict body receiver, source-backed current rays and two
unchanged obstacle profiles. Region construction uses zero translational/
rotational growth; it describes geometry, not a dynamics assertion. History can
exclude centers only from previously accepted, unexpired regions. The baseline
uses current rays only after the common initial root. Both get the same fixed
region size and .4 s horizon. No horizon/error/shape tuning after capture.

20 warm brake decisions then 40 evaluated decisions, relay target .5 m/s;
candidate throttle .45 when v<target, otherwise the previously fixed relay.
Drop every candidate packet at evaluated indices 20..24. Both arms execute
FULL_BRAKE without a usable current commitment. Use the frozen constant joint
envelope from the previous 100/299 split: no refit or use of new outcomes.
Its time bound is enlarged to complete 50 ms ticks. Both current-state spatial
containment and completion strictly before region expiry are required.
No original 1% calibration guarantee is asserted for these adaptive states.

Each accepted command lasts at most one physics tick (50 ms); the tick driver
then applies full brake until a new command is accepted. Preserve the finite
backup and log actual body-envelope/stop-time breaches, which latch rejection.
The tick driver must execute this independently of proof success/failure.

This is synchronous DELAY CO-SIMULATION, not real-time wall-clock driving:
measure capture, generation and verification wall time, add a modeled 20 ms
link, then advance ceil(total/.05) complete physics ticks under the PREVIOUS
commitment before considering the result. Thus processing cannot use frozen
physics as free evidence lifetime. The own vehicle really receives controls
and advances CARLA physics. Process hang protection on a real actuator remains
unimplemented; the simulator itself does not advance while Python is blocked.

Save all XYZ frames used by the encoder, raw proof packets, source hashes,
per-tick actual states/full 3D corners/controls, receiver outcomes and timing.
Record all failed roots, expiry, baseline rejection, dropped messages, breaches
and zero progress. Four runs are integration diagnostics, not independent
statistical coverage or cross-scene generalization. No scheduled loop.
