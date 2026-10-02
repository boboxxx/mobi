# Finite useful-lifetime study, frozen before execution

Question: can coverage-preserving ray thinning and horizon choice retain more
usable certificate time after their own computation, receiver verification,
and byte-dependent transport costs? This is an archived-input diagnostic,
not new driving, a physical guarantee, or a novelty claim.

Use the same six explicitly post-analysis-selected states as the October 2
repair study, including sparse-view and no-history negatives. Reconstruct
receiver history from the original run; never initialize an unseen-free prior.
Evaluate horizons 200, 400, 450, 475 ms, three repetitions, and four methods:
nearest-cell support (`body.pack`), established greedy cover (`compress.pack`),
established repair/reuse with its greedy fallback, and reverse deletion of
redundant nearest-cell rays. All generation calls include source quantization,
projection, selection, serialization and the complete geometry check. Randomize
the order of the four methods per state/horizon/repetition with seed 20261002.
One numerical-library thread for every method. Keep failed candidates and costs.

For every nonempty packet, independently decode, check selected raw-ray
provenance and verify with the unchanged full receiver. Independently compute
its maximum fixed-region horizon and compare it with the full-domain reference;
this diagnostic is excluded from online timing and cannot extend the sent lease.
Archive every first-repeat packet. A derived horizon must never exceed the
full-input geometry frontier under the same receiver history.

Primary quantities: generation ms, receiver ms, packet bytes/rays, and
`sent_horizon - acquisition - generation - receiver - (20ms + bytes*8/20Mbps)`.
Use acquisition from the archived capture when available; report its definition
and missing values explicitly. A second diagnostic rounds aggregate modeled
age upward to 50 ms physics ticks and reserves the existing 200 ms action bound.
It is hypothetical timing admission only, not actuator effectiveness.

Horizon-grid winner is a post-analysis oracle. An executable menu procedure
must pay the generation and verification of ALL attempted candidates before
selecting a retained packet; report that cost separately. Timing is observed,
not WCET, and is not converted into a future reliability guarantee.

Before broad deployment, unit tests must check no unobserved hole is filled,
cross-class/aged-ray coverage, actual packet corruption rejection, and redundant
deletion invariants. Freeze code before the server run. If defects require a
repair, preserve failed outputs and distinguish the corrected run.
