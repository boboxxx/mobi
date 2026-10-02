# Finite causal-maintenance implementation study

Frozen after the on-demand continuity study: greedy fixed and shortened chains
restore geometry in 6/12 targeted cases each, but 0/36 timed repetitions pass.
This follow-up changes implementation and scheduling, not the physical model,
root fact, required collar, strict expiry, 475ms horizon or 200ms reserve.

Use a compiled regular-grid enumeration of individual STRICT witness balls.
For sender selection use all actual crossing rays and the established maximum
uncovered-cell greedy, not a new set-cover algorithm. Every selected raw ray
still goes through full schema/projection/geometry verification. A standard
bounded zlib envelope losslessly compresses the existing typed bundle. Neither
a cached bitmap nor a sender claim replaces receiver geometric verification.

ALL six initialized archived runs, ALL observations drive20..39, target25 and39,
three repeats: 360 source generations and 72 targeted cold/backfill evaluations.
Maintain independent fixed475 step proofs as observations arrive, without knowing
the next timestamp or future target. Charge each acquisition and measured source
generation on a single FIFO worker in simulated capture timestamp order. No
free preprocessing: record its cost, simulated completion and queue lag. Source
availability is measured archived acquisition time, not an ideal instant scan.
Receiver retains the same verified pre-outage anchor; cached sender proofs do
not themselves establish a new receiver fact.

At targets select the same strict-overlap historical references as the previous
fixed475 protocol, wait for all selected source proofs to finish, then charge
bundle serialization, lossless compression, decompression, complete geometry
verification and 20ms + actual compressed bytes*8/20Mbps. Round total target age
up to 50ms and reserve200ms. Compare cold proof using the same native geometry,
source contract and compressed transport; report failed geometry as failure.

Compile and test before measurement. Verify raster coverage against independent
KD-tree ball queries on random grids, edge boundaries and actual saved bundles.
Archive raw selected source proofs, transport packets, all negative calls,
source/input/kernel hashes, queue/cost arithmetic and every first-repeat chain.
This retrospective timestamped pipeline is not measured wall-clock CARLA,
physical wireless, moving ego, WCET or a novelty demonstration. Faster maintenance
and compression are established implementation techniques; factual continuity
is established set-membership/reach-avoid reasoning.
