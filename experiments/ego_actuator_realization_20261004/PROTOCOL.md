# Finite ego actuation and stopping realization

This is a required physical component of evidence-guided ego integration, not
scene/policy risk qualification. No semantic perception, target truth, radio or
expiry grants control these runs. Historical actuator bounds and fixed-query
risk certificates do not transfer. No recurring job or tuning loop is created.

Freeze/publish all sources, the complete36-episode plan and independent analyzer
before capture. CARLA0.9.15/Town10HD_Opt/ClearNoon,50ms fixed ticks with10ms
substeps, Audi A2 standard physics, no other dynamic actors. Three first eligible
map spawn points whose35m-ahead waypoint is nonjunction and within3deg heading;
use the original spawn transform. Two repetitions per condition, reverse mode
order on odd repetition. Every episode owns/destroys ego and collision sensor.

Startup stage18 episodes: each location/repetition runs automatic throttle.45,
manual first gear throttle.45 and manual first gear throttle.8. Forty full-brake
settling ticks,60 fixed-throttle go ticks,80 full-brake ticks. Do not change mass,
torque, gearbox, velocity or physics. Record requested controls and actual
controls/gear, body vertices, bounding-box centers, all3D motion snapshots, wall
command/tick times, physics configuration and all collision events.

Feedback stage18 episodes is predeclared independently of startup outcomes:
manual first gear relay throttle.8 below target, otherwise zero throttle and
brake=min(.4,max(0,.4*(speed-target))) when above target+.05. Target speeds
.3/.6/1.0m/s, same locations/repetitions,40 settling/60 feedback/80 brake ticks.
Use only own measured speed for relay. Speed>1.5m/s causes immediate emergency
full brake and marks the entire episode refused; no replacement. Settling speed
must be below.02m/s. Operational exceptions are retained as failed plan entries.

Useful physical motion diagnostic: forward displacement>.5m and zero collisions.
Analyze startup separately from feedback; do not select a best policy or infer
new universal vehicle bounds. For the final go tick plus first full-brake prefix,
measure first speed<=.02m/s followed by at least3 consecutive low-speed ticks,
confirmation time, maximum3D center excursion and body-vertex enclosing radius
relative to the go-end center. Compare the actual50ms command plus stop time
with220ms action reserve and500ms maximum source-age cap. These are sampled
diagnostics, not continuous stopping guarantees or IID certification.

Independent analysis reconstructs speed from raw velocity, forward progress from
spawn yaw, bounding-box center from the full recorded transform and local box
offset, planar/body distances from raw vertices, command phases/gear and tick
increments. All36 plan outcomes must appear, including spawn/settling/capture
failures. Retain full episodes as lossless deterministic gzip with original
logical byte hashes. Compare independent local/sheng analysis bytes. Restore
world settings/weather, actors zero, stop only exact owned serverPID/path/start.

The next integration must explicitly budget whole ego motion and fallback
braking; a current position disk and a source TTL alone do not justify motion.

Implementation semantics reviewed against the official tagged source:
https://raw.githubusercontent.com/carla-simulator/carla/0.9.15/Unreal/CarlaUE4/Plugins/Carla/Source/Carla/Vehicle/MovementComponents/DefaultMovementComponent.cpp
It enables automatic gears when manual_gear_shift is false and requests the
declared gear when true. This source reading motivates measuring realization;
it does not establish the cause of the previous stationary automatic runs.
