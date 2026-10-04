# Post-run audit completeness repair

The original frozen audit fails its calibration-score dictionary equality because
the producer also creates zero-score keys for fully missing planned calibration
episodes while forming its max95 radii. The first auditor only populated captured
records. Keep the frozen audit, all fitted models, radii and predictions unchanged.
The separate audit_complete.py adds exactly the planned missing-episode zero keys
before dictionary comparison. This is a post-result audit repair, not model/radius
refitting, threshold tuning or a new run. Retain original failure log and repair
receipt; full max95/membership/age checks still run. Missing capture is refusal,
not optimistic evidence.
