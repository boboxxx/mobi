# Minimal cross-runtime audit repair after the first failure

The frozen `audit.py` failed its plan-reconstruction equality check on sheng.
The published plan was generated under NumPy 2.4.4; sheng uses NumPy 1.24.4.
All indices, seeds, coordinates, yaw draws, and vehicle speed draws match.
Only 37 walker speed reconstructions differ, by at most
2.220446049250313e-16 m/s. The same immutable plan was used for capture.

`audit_portable.py` preserves the original checker and changes only the walker
speed replay comparison: exact equality or at most one binary64 ULP, checked
with exact fractions. Other replay fields remain exact. The frozen plan hash,
all observed truth membership, geometric bounds, raw-data hashes, calibration,
packets, fees, and FIFO checks remain unchanged. No predictor or threshold was
refitted; no episode was recaptured. Both original source and first failure log
are retained; `audit_repair_receipt.json` records every differing draw and hashes.
Original source freezes remain intact and are checked by the repaired auditor.

The first sheng resume used `audit_portable.py` in place of `audit.py` in
the frozen README reproduction command; the final cross-host version is v2. The stronger lease baseline remains
independently frozen before calibration/evaluation outputs; its source job,
receiver job and all actual packet/setup bytes are paid separately. Run its
independent `audit_lease_baseline.py` against the archived producer output.
`compare_results.py` and `plot_results.py` only present completed audited data;
they do not change a score, policy or timing measurement.

Local NumPy 2.4.4 then exposed a second exact-equality failure in projected
truth coordinates computed under sheng NumPy 1.24.4. Both the failed local
log and the already completed sheng portable audit remain archived.
`audit_portable_v2.py` independently evaluates the affine transform with exact
fractions and checks each stored binary64 coordinate against a forward error
bound: 16 times unit roundoff times the input-product magnitudes, dominating
the eight elementary operation error budget. Every bound must be below 1 nm.
Membership and calibration continue to use the SAME declared stored binary
coordinates and exact fraction/integer scores; no epsilon is inserted into
membership, distance, horizon, risk or grant tests. The numerical representation
of source truth must not be presented as exact continuous physical truth.

The v2 auditor also replaces a quadratic metadata scan with a unique
cloud-to-split index, preserving the requirement that every calibration input
is a calibration cloud. All original geometric checks, scores, packets, fees,
traces and physical-snapshot counters must equal the earlier sheng audit;
only audit source identity and explicit coordinate-rounding checks are added.
For cross-host reproduction use v2. Raw binomial summaries are preserved;
`normalize_summary.py` rounds only two presentation risk fields to 15 decimal
places to reconcile a SciPy last-bit difference. It changes no calibration rule.
