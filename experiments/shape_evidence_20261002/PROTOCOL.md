# Frozen finite shape-evidence validation

Frozen before any new capture on 2026-10-03. Existing 48 physical-contract frames
are design data only. No threshold/model selection using the new test partition.
This experiment validates occupied shape-hypothesis retention, not an unknown
obstacle inventory, continuous pose inversion, collision-free driving or deployment.

## Population and split

Six fixed CARLA 0.9.15 blueprints, Town10HD_Opt, ClearNoon and the previous fixed
straight-road target. Each class has 19 calibration and 20 test episodes. Exact
PCG64 draws and separate seeds are in plan.json: longitudinal displacement
Uniform[-1.5,1.5] m, lateral Uniform[-0.5,0.5] m, yaw Uniform[0,360) degrees.
Two RSU views (lateral,height)=(4,8),(8,6) m belong to ONE episode; neither views
nor subsamples are independent experimental units. Settle 30 synchronous 50 ms
ticks then freeze actor physics. No dynamic safety claim. Spawn failures and
missing captures remain; a failed calibration episode receives maximum score 1,
a failed test episode abstains and is counted as unavailable. No replacement.
Nominal total: 234 episodes, 468 newly captured frames.

## Fixed score

model.py is frozen with padding 0.03 m, minimum 8 eligible rays and fixed
subsampling strides (1,4,16). Ignore semantic IDs/tags in scoring. Transform raw
LiDAR xyz to world coordinates. For an oriented enclosing-box hypothesis, count
observed rays entering the box before their first return and the subset leaving
it before that return. Nonconformity is their ratio. Fewer than 8 eligible rays
or an origin inside the hypothesis means abstention/score zero. A missing return
does not establish empty space. Box interiors are NOT assumed opaque. Padding
is a heuristic of this calibrated pipeline, not a certified sensor-error bound.

Ground-truth actor pose and bounding box define the true hypothesis only for
calibration/evaluation. This is not a deployed detector or a demonstrated ability
to enumerate all possible poses. Hypothetical boxes are explicit algorithm inputs.
Actual bbox extent replaces the old incorrect class-wide outer radius; no physical
mesh enclosure outside the CARLA-provided bbox contract is established here.

## Calibration and comparison

Per class, joint episode score=max over both views and three strides. At alpha=.05,
use exact split-conformal rank ceil((n+1)*.95), including infinity sentinel
(represented by score upper bound 1, giving no exclusions). Reject only if score>q.
For n=19 this is the maximum calibration score. This gives marginal coverage
over exchangeable calibration and test episodes, not 95%-confidence conditional
risk <=5%, not conditional coverage among accepted messages, not time-uniform risk.
Selecting among the six predefined cases is covered; arbitrary subsets are not.

Compare q=0 solid-box diagnostic, full-only calibration (max two full views)
transferred to all budgets, and joint calibration. No baseline is tuned on test.
Report per-class episode-any false exclusions, frame/budget exclusions and
abstention. Per-class one-sided exact binomial 95% bounds describe test risk for
the fixed calibrated rule under iid sampling. Stratified aggregate counts are
descriptive, not a pooled-binomial confidence guarantee.

## Utility diagnostic

For each true pose use 8 predeclared translated box hypotheses: forward offsets
(-6,-3,3,6) m crossed with lateral offsets (-3,3) m in the target-road frame.
Their locations intentionally use truth for this matched diagnostic, so utility
is NOT deployable free-space coverage. Report rejection/support for ALL hypotheses,
without filtering by observed occupancy. They may overlap background geometry or
the true actor; do NOT label them empty. This checks that calibration is nonvacuous.

## Evidence and audit

Preserve raw semantic LiDAR bytes, timestamps, transforms, actor truth, failures,
cleanup and hashes. Scores read xyz/origin/hypothesis only; IDs are audit-only.
Independently recompute slab intersections using a face-event reference, quantile
ranks, membership, seeds/splits and complete episode family outcomes. Test edge
cases, unsupported geometry and strict ties. Record actual CPU timings separately
from simulation time. No link/closed-loop inference from this static study.

If failures occur, preserve and report them; changing the model requires a new
independent evaluation, never a retuned claim on this test set.
