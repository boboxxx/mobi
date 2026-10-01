# What local reuse does and does not authorize

A receiver-verified region R with expiry E is a statement about external
occupancy over a time interval, conditional on the existing sensing/shape/motion
contracts. It is not a one-use command token. At a later tick t, a current-state
maneuver enclosure K(t), completion bound T(t), and strict tests

    K(t) subset R,  ceil(1e6*t) + ceil(1e6*T(t)) < E_us

suffice for that finite maneuver under the additional actuator assumptions.
They may be rechecked using the same R at subsequent ticks. Each check uses the
new measured state, keeps the original E, and includes its own full backup.
An in-flight message supplies no region for this check. Missing, late or invalid
messages leave only the previously available region; they do not reset its age.

The capture program therefore separates receiver history from the locally usable
region. It exposes a new region to the control gate only after advancing the
measured processing/transport delay in physics. Raw logs contain the available
region ID and availability time before every tick. Independent replay reconstructs
this timeline and checks that no pending region authorized a command.

This is the same finite conditional argument as the earlier handoff interface,
not a new invariant-safety theorem. In this experiment T and K come from a
statistically calibrated sampled maneuver envelope. Deployment changes the state
law; neither its iid calibration risk nor continuous-time validity is claimed.
A sampled breach latches full brake. Absence of a breach cannot establish the
physical contracts. A stopped car is not guaranteed safe for unlimited time.

Reusing R can remove an unnecessary per-message control wait. It cannot solve
insufficient ray coverage, an expired parent, inadequate actuator bounds, or an
independent actuator scheduler failure. The tick driver is synchronous simulation
infrastructure, not a wall-clock watchdog for a physical vehicle.
