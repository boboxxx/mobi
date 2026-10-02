# Frozen finite recursive validity study

Seven matched methods: fixed_strict, fixed_forward, fixed_terminal,
coarse_forward, coarse_terminal, fine_forward, fine_terminal. All reuse the same
120 selected raw dictionaries, original physical profiles, complete accepted
42-packet prefixes, local position windows 9/11.5m, immutable typed lossless
transport and bounded receiver-owned exact caches (4 geometries/64 updates).
Each condition/repeat starts from the same independently validated warm root,
empty caches; all new verification and encoding are measured on sheng, one
thread. Setup is separately paid/reported and is not a fresh cold bootstrap.

Six runs, twenty frames, three repeats, three presets = 7560 charged rows:
standard 20Mbps +20ms latency; slow 0.5Mbps +20ms; blackout standard link dropping
indices27,28,29. Dropped packets still pay sender/link work, never update facts.
Repeat method order is shuffled with seed20261008. These are saved-source model
presets, not actual wireless, fresh CARLA or a WCET measurement.

Source arrival/acquisition and generation services are frozen from the prior
streaming study (same run/repeat/index). A sender FIFO pays generation followed
by measured encoding; serialization has its own FIFO, then20ms propagation;
receiver FIFO pays actual measured validation/update/frontier. All duration
charges round outward to integer microseconds. Root receiver availability plus
measured reset cost initializes receiver FIFO. No packet supplies its own
checkpoint, skipped history or backdated action authority.

After receipt only, terminal variants use the integral of the minimum of the
two endpoint speed cones for past propagation. Future frontier always uses the
latest endpoint and one-sided acceleration bound. Strict fixed uses overlap;
forward/terminal fixed may preserve the known K fact if past displacement is
within the previous fully checked forward collar budget, including its original
clock allowance. Current collar is then fully revalidated. Source timestamps
and sequence must increase, even for unsuccessful bridges. Facts may persist
after action expiry; expired action grants are never reactivated by history.

Fresh admission uses the previous study's stipulated source-aligned 50ms upward
age rounding (minimum50ms), and strict age+200ms<horizon. Authority is only
available after completed verification and is retained for the same fixed body
region if a later loose posterior has horizon0. Also report union coverage of
action intervals [rounded availability, endpoint-200ms), plus the previously
accepted warm root interval, on [frame20_ref, frame39_ref+500ms]. Interval end
strictness has zero effect on Lebesgue duration. No new moving control claim.

All first-repeat states and packets are saved by content SHA256; all7560 timing
rows are retained. Independent audit reconstructs complete prefixes, source
provenance, uncached mathematical grid transitions using vertex KD trees
(pure memoization of its own independently computed repeated operands allowed),
two-cone formula independently, every first-repeat state/H/H+1 boundary, all
packet bytes, FIFO costs and coverage. No candidate/native/EDT audit imports.

Conditional physical contract: continuous persistent class trajectories exist
at the trusted root; ALL class members obey norm-speed bound at each actually
selected observation time, norm-acceleration throughout; effective reference
speed includes the latest actual ray age. Core opacity, radius/error/pose,
global time and source authenticity remain assumptions. Class births or only
detected-object endpoint caps do not satisfy this contract. No physical safety,
continuous useful driving or new reachability theory is claimed.
