# Full-body measurement correction, frozen before the final capture

The initial `capture.py` records yaw and a horizontal bounding-box rectangle.
That is insufficient to claim a full vehicle footprint when pitch/roll change.
Its independent-episode corpus is retained as a preliminary measurement batch
and excluded from final fitting/calibration/testing. No preliminary outcome
metrics were inspected to choose a predictor, correction or sample plan.

`capture_3d.py` repeats the exact PROTOCOL.md random requests, split seeds,
controller, weather and sampling parameters, adding pitch, roll, box height and
z offset, and all eight world-space bounding-box corners computed from the SAME
actor-snapshot transform by CARLA's BoundingBox.get_world_vertices(transform).
The bounding box's own local transform is included by that API. Spatial targets
now use the XY projections of those eight corners, not a yaw-only reconstruction.
Reference and all future snapshots have these measurements. The temporal target,
features, predictors, scales, calibration maximum and held-out rules are unchanged.

This corrects sampled full-body geometry; it still does not observe motion
between the 50 ms snapshots or certify a physical pose error contract. Keep the
preliminary data in a separate archive; do not combine repeated requests from
the two batches as independent calibration or test samples. Final sample counts
remain 100 / 299 / 400.
