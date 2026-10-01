# Finite post-analysis expiry-frontier diagnostic

Frozen after the eight live-repair runs, before computing their horizon results.
Use every root decision and the first warm and first drive decision in each run.
No new driving, calibration, independent scenario or held-out improvement claim.
For each input, recover only receiver history actually valid at its integer
reference. Compute the largest integer-microsecond horizon up to 2 seconds for
(1) all observed rays and (2) the actually transmitted subset, where present.
Keep both object classes, all uncertainty contracts and the fixed full-body
region unchanged. No interpolation over unseen space. The full-ray frontier is
an offline information-capacity diagnostic, not necessarily a legal-size packet.

Compare the proposed frontier against direct reference geometry at 20 horizons
(100..2000 ms), at its reported boundary and one microsecond above it. Every
nonzero subset frontier is reserialized and checked by the unchanged receiver
geometry. Record compute costs and bottleneck class/unexcluded cell. Deduct the
actual archived age and the 200 ms sampled maneuver bound to report offline
slack, not commands that occurred. Frontier computation cost is separately
reported; neither precomputed nor observed costs establish a future WCET.

Also diagnose every initialized run's first warm frame, strict integer parent
validity, original float root-ready test and integer next-tick reservation. The
strict fix must never revive expired history. This finite diagnostic does not
restart the CARLA experiments or add a continuous research loop.
