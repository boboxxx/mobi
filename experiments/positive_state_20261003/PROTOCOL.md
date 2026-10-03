# Fresh positive-evidence center-set validation

Frozen before capture. Existing observations and the545-pose counterexample bank
are development/regression data only, never a fresh final evaluation set.

## Population and independence

CARLA0.9.15, Town10HD_Opt, ClearNoon, the same six known blueprints and inherited
known bbox extents. Independently sample39 calibration and60 test episodes per
class: longitudinal Uniform[-8,8]m, lateral Uniform[-4,4]m, yaw Uniform[0,360).
New disjoint seeds2026100700+class index and2026100800+class index; all594 draws
are frozen in plan.json. Two RSU views(4,8),(8,6) per settled/frozen actor form
ONE episode. This widens the previous position law; no result is claimed for
arbitrary maps, unknown inventories, interacting traffic or physical sensors.

Retain original sensor settings and every fourth return from each raw scan,
including audit-only semantic fields. Record original counts and sampling stride.
The estimator reads only the stored XYZ and known sensor/road/class contracts.
No current actor ID, semantic tag, truth pose, bbox center or query informs it.
The two views are scored separately; this is not free temporal fusion.
Spawn/missing failures are preserved without replacement. No other CARLA process
may be disturbed. Own server/actors must be cleaned up after this finite batch.

## Fixed XYZ frontend

Transform into the declared road frame. Retain XY in[-12,12]x[-8,8] and height
(0.3,2*extent_z+0.3). Use0.2m XY grid cells and8-neighbor connected components.
Keep components with at least3 sampled returns, each XY span <=2*norm(extent)+0.2m,
and Z span <=2*extent_z+0.2m. Each remaining component proposes its XY bbox
midpoint. Keep ALL proposals; never choose the true component using labels.
No proposals in either required view, or any missing frame, causes the whole
episode to output the full center plane and refuse authorization.

For an available episode, score=max over the two views of distance from the true
center to the nearest proposed center. Ground truth is used only for calibration
and evaluation of this distance. For a refused episode, score0 because the full
plane cannot exclude the truth. Calibrate one radius per class at rank
ceil((39+1)*.95)=38 of39 scores. This is ordinary split conformal, not new theory.
This gives marginal simultaneous two-view coverage under exchangeability, not
coverage conditional on availability and not trajectory/time-uniform coverage.
Missing or wrong component selection that still outputs proposals is NOT a
refusal; its potentially large true-center residual must count in calibration
and test coverage. No class-specific tuning after fresh capture.

Quantize proposed centers to nearest1cm and inflate the calibrated radius by8mm
plus outward micrometer rounding. Use a union of center discs, not a selected
best component. Message metadata identifies source frame/time, fixed class,
sensor/road contract, calibration and radius. Coding must preserve the union.

## Endpoints, cost and comparisons

Report every class's39 calibration and60 test outcomes, missing/refused episodes,
any-view true-center exclusions, exact one-sided95% binomial upper bounds, radius,
proposal counts and message size. These six class laws are stratified; do not
pretend a pooled count establishes homogeneous5% risk. A19/20-style small sample
success is not evidence of a tight deployment risk bound.

For each available view, evaluate fixed query centers(-6,0),(6,0) with radius0.75m
and the inherited body disc ceil(norm(extent)) at micrometer resolution, speed5m/s,
acceleration3m/s^2 and500ms cap. Exact minimum distance to the union gives the
geometric horizon for THIS calibrated center-set/disc model; it is not the
optimal horizon of the full point-cloud inverse problem. Test actual true-center
membership, not merely existence of a useful horizon. Compare an uncalibrated
zero-radius proposal diagnostic and truth-center oracle only as labeled audits.
No state-of-the-art or MobiCom novelty claim from those baselines.

Charge observed capture callback time, extraction, coding/verification, modeled
20Mbps wire,20ms propagation,20ms clock and200ms action reserve. Three processing
timing repeats; use worst observed per-frame pipeline time, not WCET. Simulation
timestamps differ from wall time; static settled actors do not demonstrate live
dynamic control. Gate the entire two-view episode on availability; finite static
analysis may inspect both views before evaluating outputs, so no causal online
family-completion or sensor schedule is claimed.

Independently rederive positive components, quantile rank, family coverage,
message reconstruction, center-rounding containment and analytic first-contact
brackets. Preserve all raw sampled scans, failures, hashes, test logs, timing and
audit outcomes. Frozen old witness bank is regression-only. Full scene coverage,
physical body/motion/sensing contracts, new-map generalization, online causal
availability, a real link and useful closed-loop control remain separate duties.
