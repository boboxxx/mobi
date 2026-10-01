# Ray error and timestamp alignment

This finite follow-up replaces an unexplained planar witness-error input with a computable bound from supplied coordinate boxes and individual ray ages. It preserves the prior 0.05 m receiver error budget; unusable rays are rejected. It does not calibrate a physical sensor, recover missing timestamps, or validate obstacle opaque cores.

The first audit preserves that fixed budget; the explicitly documented follow-up instead uses per-ray bounds. See the [completed report](../../research/visibility_uncertainty_result_20261001.md) and [machine-checked summary](../../results/visibility_uncertainty_20261001/analysis.json).

## Geometry

Let the origin be o, the first return p, and the known physical probe plane be z. The plane crossing is w=(1−t)o_xy+t p_xy−q, with t=(o_z−z)/(o_z−p_z). A ray is eligible only if **all** positions in the origin box are above the plane and **all** positions in the return box are below it. A nominal crossing alone is insufficient.

Within these conditions, t increases with both o_z and p_z. Evaluating their lower/lower and upper/upper endpoints bounds t. For each horizontal coordinate, the extrema of the resulting convex combination occur at a t endpoint and the matching coordinate-box endpoints. Subtracting the query-registration box produces a rectangular enclosure of w. The farthest corner relative to the nominal crossing bounds its Euclidean error. Code includes a small floating-point margin; this is not machine-verified interval arithmetic.

The fixed plane and the object's opaque-core condition at that plane remain prerequisites. Uncertain road height or an object that does not intersect that height cannot be repaired merely by this horizontal error calculation. Input boxes must already include world-coordinate pose/transform effects. If a moving sensor has per-ray poses, supply the N×3 origin array rather than one inaccurate shared pose.

## Time

For a ray observed age A before a common evidence timestamp, an obstacle center can move at most vA+aA²/2. Its center at the common time is therefore excluded only within r_min−projection_error−motion_error of the nominal witness. The adapter returns the sum as an **effective exclusion debit**. It is not claiming that an old empty point is empty now.

The speed bound must hold at each ray's observation and at the common timestamp used by the downstream validity computation; one bound on speed only at the beginning of a long scan does not establish the latter. This experiment assumes a common speed bound over the scan window. Otherwise an upstream model must propagate a larger speed bound to the reference time as well. Clock and future-motion margins in the original profile still apply after the evidence timestamp.

Keep a witness only when this total debit is at most the receiver-agreed 0.05 m. Existing certificate and packet code can then use the same profile safely under the strengthened contract. The support-template method must select exclusively from these filtered current witnesses. This adapter has not yet been incorporated into a dynamic CARLA controller.

## Finite reproduction

From the repository root, using Python 3.8+, NumPy and SciPy:

```bash
python -m unittest discover -s experiments/visibility_uncertainty_20261001 -p 'test_*.py'
python experiments/visibility_uncertainty_20261001/run_audit.py \
  --capture results/visibility_certificate_20261001/carla120 \
  --out /tmp/visibility-uncertainty-new
```

The script refuses an existing output directory. It performs 100,000 box perturbations and uses the first cloud from each of twelve existing conditions. [PROTOCOL.md](PROTOCOL.md) fixes error bounds, scan periods, phases and comparison methods before execution. Exact source and cloud hashes accompany results.

`simultaneous` is the original timestamp assumption, now with bounded projection. `oldest_age` conservatively assigns every ray the oldest assigned age. `individual_age` aligns each ray separately. Rolling ages are **hypothetically assigned from azimuth** because original clouds did not record individual ray times. They must never be described as newly measured CARLA rolling scans or a dynamic driving experiment.

Raw coordinates, query registration and ray timing bounds remain supplied contracts. A Monte Carlo draw passing its box bound checks an implementation; it does not prove coverage for unbounded noise, hallucinated returns, out-of-distribution materials, or real sensor calibration.

## Heterogeneous bounds and exact local search

The first completed audit motivated [WEIGHTED_FOLLOWUP.md](WEIGHTED_FOLLOWUP.md): reject no useful ray solely because its error exceeds a fixed 0.05 m cutoff. Instead use its own projection-plus-age debit, round it upward in 0.01 m bins, and shrink its center-exclusion radius accordingly. `weighted.py` implements the exhaustive reference and a strong matched baseline that selects the best common error threshold. The two methods receive identical bounds and timestamps. `profile.error=0` in these APIs means the full error is supplied per ray, not that observations are noiseless.

While the exhaustive reference was still running, its cost motivated an exact search optimization. `local_search.py` sorts tiles by distance to the queried action. After finding the nearest unresolved tile, farther tiles cannot lower the clearance; outside-domain distance remains included. It reuses per-bin distance queries across the heterogeneous computation and uniform-threshold sweep. This changes computational work, not the certificate's geometric conditions. The existing full-grid reference is retained to verify every result of the new implementation.

```bash
python experiments/visibility_uncertainty_20261001/run_weighted.py \
  --capture results/visibility_certificate_20261001/carla120 \
  --out /tmp/visibility-weighted-new
python experiments/visibility_uncertainty_20261001/run_local.py \
  --capture results/visibility_certificate_20261001/carla120 \
  --reference /tmp/visibility-weighted-new/weighted.csv \
  --out /tmp/visibility-local-new
```

The timing comparison counts both heterogeneous certification and the entire best-uniform sweep. It excludes projection, proof selection/serialization, transmission, verification and action execution. Faster geometry does not by itself establish a feasible end-to-end deadline. The prior version-one packet format still assumes a common error budget; it must not serialize heterogeneous proofs without a corresponding verifier update.

After local/reference equivalence is established, the fixed [larger-error sensitivity](LARGER_ERRORS.md) can be reproduced with:

```bash
python experiments/visibility_uncertainty_20261001/run_sensitivity.py \
  --capture results/visibility_certificate_20261001/carla120 \
  --reference /tmp/visibility-weighted-new/weighted.csv \
  --out /tmp/visibility-sensitivity-new
python experiments/visibility_uncertainty_20261001/analyze.py \
  --results results/visibility_uncertainty_20261001 \
  --capture results/visibility_certificate_20261001/carla120
```

The last command verifies the published artifact tree, including `weighted`, `local`, and `sensitivity` subdirectories. Add `--no-plots` to omit Matplotlib. Thirteen tests passed locally and on sheng. The recorded exhaustive run took 895.31 s; the optimization matched all 288 outputs exactly in this run. Code, input, protocol and reference-file hashes are retained. These observations do not replace an end-to-end, dynamic driving evaluation.
