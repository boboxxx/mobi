# Exact age and current-observation count revalidation

This study changes computation, not the terrain-clipped calibrated score or its
pose, terrain, inventory and dynamics premises. No new risk guarantee follows
from faster computation. Calibration/test reuse and ideal semantic-LiDAR data
remain limitations inherited from the previous study.

## Exact age without repeated Fraction construction

Distances and radii are integer micrometres, time t is integer microseconds.
For the FIXED v=5m/s, a=3m/s² model and0.75m query radius, the reach is

    R(t) = body_radius + 750000 + 5t + 3t² / 2000000.

Strict separation is exactly equivalent to

    (dx²+dy²) * 4000000000000
        > [2000000*(body_radius+750000) + 10000000*t + 3*t²]².

The enforced coordinate/radius/time ranges fit unsigned128-bit arithmetic.
A floating root supplies only an initial guess; integer comparisons correct it
until it is safe and its next tick is unsafe, unless capped. Thus the floating
root cannot silently round validity upward. Regression checks use the independent
historical Fraction implementation at1500 random inputs and18 contact boundaries.
The geometry outside this scalar calculation still uses float64 engineering
margins; this does NOT provide formal directed-rounding interval arithmetic.

## Additive count certificates

For each continuous pose cell, the existing inner/outer clipped enclosures yield
four counts: Nplus (possibly eligible), Nminus (definitely eligible), Pminus
(definitely passed), Hplus (possibly nonpassing). Each is a sum of per-ray0/1
contributions, separately for the two nested budgets. The same score lower bound
is used:

    max(Pminus/Nplus, 1-Hplus/Nminus, 0), when Nminus>=8;
    0 otherwise.

An inherited split tree remains a complete partition regardless of new data.
For each old excluded leaf, let Delta contain ALL slots whose current xyz bits
differ from the old packet. If sensor transform, class/calibration identity,
return count and budget remain compatible,

    counts_current = counts_old
                     - sum(old contribution over Delta)
                     + sum(current contribution over Delta).

This identity permits changed directions and reordered returns: they are simply
removed and added with their correct slot/budget weights. It does not assume
that a changed return travels along its old ray. Zero/low support never excludes.
Any old exclusion which fails after the update is revoked. Previously unresolved
leaves remain retained even if new measurements might exclude them; this design
is conservative and can need additional refinement. It never reuses the old TTL.

## Why a current packet is required

The receiver first reconstructs the complete current packet through lossless
reference coding and verifies its checksum/calibration identity. The current
source frame and timestamp must strictly increase. Matrix bits, declared class,
original return count and budget must match the cache contract. Packet/reference
mismatch refuses reuse. Therefore 'unchanged' means a verified current observation
matches, not that nothing arrived. Checksums establish integrity against accidental
mismatch; they are not sender authentication.

The new lower horizon is the minimum of all retained cell horizons and the
unknown-boundary horizon. This preserves the same full-current-score support
property as recomputing every old excluded leaf from scratch. Identical counts
are verified against that paired baseline and an independent world-halfspace
reference. It need not match a newly refined current partition, and cannot prove
that the remaining lower/upper gap is small.

## Cost and limits

Compare delta and full rechecking on the SAME inherited partition and the SAME
current lossless wire. Charge current packet creation, lossless encode/decode,
receiver verification/rechecking, wire serialization, propagation, clock margin
and action reserve. Pay old reference and initial proof construction; if they are
not ready by the next source timestamp, charge the delay too. Tests use separate
query tasks and20.5s gaps between saved observations, not a joint live schedule.
Only worst observed timings over the finite repeats are used in the net accounting;
no WCET or physical sensor-acquisition guarantee is established.

A1mm synthetic perturbation changes every return's bit pattern in this fixture.
Exact-bit delta updates then lose their sparse-change premise. Silently ignoring
small changes would invalidate the additive identity. Robust geometric margins
or independently calibrated measurement uncertainty must justify such reuse;
this experiment does not implement that additional mechanism. The two positive
modeled remainders do not establish robustness to noisy real sensors or useful
physical driving.
