# Finite actuator realization probe (post-analysis)

The ten completed fresh evidence runs admit commands but do not show useful
forward motion. Before another evidence integration, diagnose automatic gearbox
state as a possible cause. This hypothesis is not established in advance.

32 new component episodes: four repetitions, throttle durations of 1,2,4,8
50-ms ticks, paired default automatic control versus manual first gear. Reverse
mode order on odd repetitions. Audi A2 at the original first-straight target,
ClearNoon, no external actors, 15 initial full-brake settling ticks, .45 throttle
then 40 full-brake ticks. Every episode creates/destroys its own ego and collision
sensor; record full 3D snapshots, actual commands, reported gear/manual flag,
and gearbox configuration. No initial velocity override. Compare peak speed,
projected go/brake displacement, final speed and collision count.

These are actuator component probes, not evidence-guided driving. The manual
control law differs from the calibration law; any better response does NOT
justify reusing the old statistical maneuver bounds or integrating it without
new calibration. This is a finite diagnostic, no recurring research loop.
