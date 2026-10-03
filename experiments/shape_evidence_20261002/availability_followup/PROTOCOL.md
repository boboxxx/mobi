# Fresh availability-aware follow-up, frozen before new capture

2026-10-03. The initial six-class test has been inspected and is permanently
preserved. Its three missing pedestrian calibration episodes made q=1. This
follow-up is a new experiment, not a reanalysis claimed as an independent win.

Use the unchanged score, sensor, map, actor settling and randomized pose law from
the parent protocol. Only walker.pedestrian.0001, new disjoint PCG64 seeds
2026100505 (19 calibration) and 2026100605 (20 test); exact draws in plan.json.
At most 78 new frames. Never resample a spawn failure. No tuning on new test.

Pipeline change: if any required frame is unavailable, emit the whole hypothesis
space and refuse authorization for the episode. Its exclusion nonconformity is
therefore exactly zero, since it cannot exclude the true hypothesis. Assign score
zero to failed calibration episodes. This is a definition of an abstaining
prediction procedure, not imputing a missing label as a successful observation.
The same rule applies to test/deployment; missing data must be observable and
trigger refusal. Silent corruption or unreported detector failure is not covered.

Joint score=max over 2 views x strides (1,4,16), rank 19 of 19 at alpha=.05.
Compare the same frozen solid-box, transferred full-only and joint rules.
Unconditional marginal exclusion risk includes refusals; it does NOT give 5%
coverage conditional on available/authorized episodes. Report total scheduled,
successful, refused, true exclusions, and unconditional episode confidence
bounds as well as the conditional successful-episode bounds when meaningful.

The eight truth-referenced translated boxes remain a diagnostic, not evidence
of empty roadway. No actual TTL/control claim. Freeze, preserve and publish both
positive and negative results. This one finite follow-up is not a recurring loop.
