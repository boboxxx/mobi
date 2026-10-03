# Fixed terrain-clipped score diagnostic

Frozen before running this score: cut_z=0.15m in the existing flat-road public
world frame (road anchor z=0), padding0.03m, minimum8 eligible rays. Intersect
each hypothesized OBB with z>=cut_z before calculating ray penetration. Keep
ground-hit rays: their observed free segment above the clipping plane is useful;
do not filter them away or convert missing returns into free rays.

Use existing 19 calibration and20 test episodes per class, both views and
strides1,4,16. Use the availability follow-up for pedestrians, original capture
for vehicles. A missing episode refuses all exclusions; calibration missing
score0. The per-class threshold is the maximum19 episode scores, each the maximum
across the six view/budget combinations. Unsupported individual hypotheses have
score0, and remain retained. Recalibrate the changed score; never reuse old q.

Re-evaluate the fixed39-pose witness bank under the new nested constraints at
each budget. Read no labels when calculating scores. Ground truth poses are used
only for calibration/error measurement; source ray xyz remain the only ray input.
This is a retrospective model repair on already inspected data, not a new
independent test or a confirmed5% deployment guarantee. Do not select a cutoff
using these results. No continuous-set solver, physical TTL, new CARLA trial,
or joint temporal safety claim is established by this experiment.

Interpretation: under a *prospectively fixed* score and exchangeable complete
calibration/test episodes, the rank argument provides marginal family coverage.
The present data reuse does not verify that premise. Road uncertainty, arbitrary
terrain, unknown shapes, and partial actors remain outside validated scope.
