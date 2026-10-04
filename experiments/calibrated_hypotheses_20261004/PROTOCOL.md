# One finite development gate before any new qualification/capture

Prior pose-support hulls plus their original prospective truth labels are the
training inputs. Latest shape batch is already-observed development data.
Fit exactly one classwise deterministic local-exemplar model: k8, nearest32
local residual90% scale,50mm scale floor. Scale residuals exclude ALL same-
episode rows and use only the same layout. Guard uses training min/max plus
10% range (minimum1e-6) and max training episode-excluded nearest squared
feature distance. Unsupported inputs fall back to the geometry family;
empty observations refuse. Do not use labels/future at runtime.

Mean-neighbor single circle and neighbor-mode union are the two new estimator
families. Direct score is max(pose violation/10mm, exact outward center error/
local scale), with only pose score on fallback. Per-class max over planned95
old calibration-labelled whole episodes produces descriptive q. No new risk
qualification: the data were previously observed. Do not tune from old test
results within this frozen run or delete failed episodes.

Evaluate plain circle union, global max(pose distance,circle-union distance),
and exact incompatible-pair pruning for the SAME modes, same q/state event.
The clip lower bound is min over surviving modes of max(circle distance,
distance to surviving pose rectangles). It is a conservative intersection
distance, not an exact optimizer or a new Lipschitz/conformal theorem. Prune
only when exact rectangle/center squared distance exceeds radius squared.
Contradictory/empty learned intersections have no authority. Compare all
source ages and failures with current joint ages; no paid utility yet.

Freeze code/input identities before model fit/new prediction. One sheng fit,
complete development evaluation, independent integer state/age audit, publish
all outputs. Existing core geometry sources remain unchanged. If the candidate
is worth further testing, freeze its final model and score BEFORE a separate
new finite capture. No simulator or recurring research job in this gate.
