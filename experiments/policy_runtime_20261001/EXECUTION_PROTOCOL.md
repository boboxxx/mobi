# Finite realization check of the actual proposed policy

Thirty-six CARLA 0.9.15 Audi A2 episodes: first three valid straight non-junction
spawn locations, target initial speeds 0/0.5/1 m/s, hold durations 0.05/0.10 s, with paired go and brake-only actions.
Twenty full-brake warm ticks, then throttle 0.5 until initial target is reached
(maximum 180 ticks); a target-zero episode starts at settled rest. Failed target
preparation is retained. Use actual reference speed when checking a model.

From the reference state execute brake 1.0 for the hold, throttle 0.5 for one
50 ms tick, then brake 1.0 for 40 ticks. In the paired brake-only run, the go tick also applies brake 1.0 and zero throttle. Steering zero, automatic gears and
synchronous batch commands; no target-velocity override or in-episode teleport.
Each sample uses a single world snapshot and asserts its frame equals the tick
returned by CARLA. Record actual controls, bounding-box extent and offset,
world pose, velocity, timestamp, commands, collisions and cleanup.

Measure useful forward displacement during and after the short go command,
maximum displacement, speed growth, low-speed-band entry and source-policy tube
containment for the first 0.4 s. Do not infer a continuous-time hard bound from
absence of sampled violations. Comparison uses the previous frozen policy
parameters without retuning. These are actuator tests, not certificate-guided
driving, statistical calibration, or independent natural road scenarios.
