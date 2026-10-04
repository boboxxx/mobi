# Finite static-background frontend diagnostic

Freeze before producer outputs. Use only calibration step-zero XYZ scans from
causal_state_20261003 to fit two per-layout static occupancy references. No IDs,
semantic tags, actor poses, per-point labels or prospective scans enter fitting.
The old and current datasets have the exact same public basis and sensor layouts.
In the local ROI |x|<=12, |y|<=8, 0.3<z<3 m, voxelize at0.1m. A voxel is static
if present in at least ceil(0.9*N) fit scans for its layout. Count presence once
per scan, not points. These constants are fixed; no threshold sweep.

For every prospective_expiry_20261003 scan, remove only current XYZ points in
static voxels and run the unchanged2D component frontend on the remainder.
There is no nearest-target selection and no class/pose label gating; all current
candidate centers remain. Extent and local basis stay known as in the parent.
Refuse if there is no proposal. Missing proposals create no free-space evidence.
The diagnostic score is nearest-proposal error, maximum over every available
frame in each of the95 planned calibration episodes, with zero only on refused
frames. Report max-score radius+8mm quantization allowance and all test failures,
refusals and state-model geometric horizons. Do not drop failed plans or outliers.

This uses already-inspected calibration/test data for development. The max95
radii are descriptive: do NOT inherit a prospective risk guarantee for this
changed frontend or claim a new holdout. Future frozen capture/calibration is
required before statistical claims or use as an authority source.

Also repeat extraction with one declared deterministic local XYZ shift
(+1,+1,+1)mm and(+10,+10,+10)mm before subtraction and proposal extraction,
keeping the same fit map and unperturbed descriptive radii. Report exclusions,
refusals, proposal changes and geometry changes separately. These are synthetic
shift diagnostics, not measured sensor-noise distributions or robustness bounds.

Observe source extraction/quantization cost three times per unshifted current
scan; save all samples and max. This diagnostic creates no paid action policy,
no fresh messages, network replay, actual link or ego control. Record the complete
compressed background setup bytes and fit inputs; sharing is not cost-free.
Existing parent action counts are never attributed to this new frontend.

Offline only: use saved per-point actor IDs to diagnose target returns removed
by the reference and existing merged-component failures. Never feed those IDs
into fitting or online extraction. Independent auditors reconstruct occupancy
by sorted unique voxel arrays, reconstruct component proposals independently,
verify radius/horizon endpoints and counts on both hosts. Parent input bytes and
code remain unchanged. No recurring research job; no novelty claim for standard
background subtraction or clustering. Full project objective remains active.
