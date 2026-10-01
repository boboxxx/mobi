# Finite continuous-control realization comparison

Twelve Audi A2 runs: first three straight non-junction spawn locations,
target speeds 0.5 and 1.0 m/s, two fixed controllers. Start at rest after
20 ticks of full brake. Apply continuous control for 160 ticks (8 simulated
seconds), then full brake for 40 ticks. dt=50 ms, substeps at most 10 ms.

Controllers: (1) CARLA's unchanged default Ackermann controller with desired
speed and desired acceleration 0.5 m/s²; (2) a fixed relay: throttle 0.45 below
target, otherwise zero; brake min(0.2,0.2*(v-target)) only above target+0.1.
Steering zero. The desired Ackermann acceleration is not assumed to be a hard
bound. No physics modification, target-velocity override or within-run teleport.

Use one world snapshot per recorded state and match its frame to world.tick.
Record actual controls, speed, pose, timestamps, body geometry, default
Ackermann settings and collision events. Report progress, speed variability,
sampled acceleration, complete observed stop and drift. No data-driven parameter
retuning and no claim of calibrated physics or evidence-guided driving.
