# Native and incrementally revalidated pose expiry

Finite engineering follow-up to terrain_score_20261003, preserving its score,
calibration and physical limitations. Profile the existing Audi test00 query+6
at16000 nodes. Use all six classes and both fixed queries for evaluation.

Implement a C++17 kernel with exact integer-microsecond cell expiry, the same
refined continuous pose enclosures, seven-plane clipped-ray counts, nested16/4
budgets, and conservative unknown boundary. Disable exact-pose probing explicitly;
this preserves lower-bound validity but may leave upper bounds looser. Preserve
full trees for independent audits. No fast-math. No training or new calibration.

For warm reuse, retain a previous query's complete partition and geometric count
certificates. Reconstruct the COMPLETE current packet losslessly against an
explicitly paid reference; then compare every xyz return, source frame, sensor
pose, calibration and shape identity. A cached count can be updated by subtracting
old changed-ray contributions and adding current changed-ray contributions. Any
previously excluded cell that no longer excludes is retained, never assumed safe.
No unchanged-current-data certificate follows merely from missing transmission.
Mismatch/refusal requires fresh computation or zero authority. No cached expiry
is stamped with a new timestamp without current observation verification.

First measure full computation at16000 nodes over all12 existing selected scans
and24 queries. Revalidate each test00 tree using its own class's test10 scan for
12 warm queries; recompute all cells from scratch as a correctness/performance
baseline on the same inherited partition. Charge cold initialization separately,
including reference transfer. Preserve all failures; no success filtering. A
single64000-node follow-up may be used to measure offline proof tightness versus
warm checking cost, retaining both budgets. This is a finite saved-data study,
not an ongoing loop, new CARLA capture, fresh risk validation, physical moving
closed loop, or established MobiCom novelty. Current wire/clock/action costs and
source age must be paid before claiming a positive modeled usable remainder.
