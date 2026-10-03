# Finite continuous-set follow-up

After the fixed clipped-score calibration and witness-bank results, run the same
12 available observations and2 public queries with stride4 (retaining stride16),
priority ordering and2000-node budgets. No test-scene selection. Use the existing
six-dimensional prior, disc dynamics and original point timestamps. Replace only
the point score and inner/outer-box intersections by the fixed above-road clip.
A calibration digest in newly encoded packets identifies the changed score data.

After observing all24 lower bounds still zero but1076 whole-cell exclusions,
run one additional fixed batch of all24 queries at16000 nodes. This is a compute
sensitivity diagnostic, not tuning on an independent test, online feasibility,
or a proof of physical safety. Preserve both batches and all trees/packets.
No more budgets are automatically scheduled. Even positive geometric horizons
must pay measured runtime and communication before being called usable TTL.
