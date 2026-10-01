# Finite independent-episode action calibration

Frozen before capture, 2026-10-01. Purpose: replace falsified fixed acceleration
constants by explicitly statistical, state-conditioned *sampled* maneuver bounds.
This does not calibrate sensors, establish continuous-time safety, or prove
coverage for states selected adaptively by an evidence-guided driving policy.

799 fresh Audi A2 episodes on the same exclusive CARLA 0.9.15 Town10HD_Opt world.
Each resets by spawn/destruction. Independently draw a location uniformly from
the first three non-junction spawn points whose 35 m-ahead waypoint is also
non-junction and within 3 degrees heading; target speed uniformly in [0.3,1.2]
m/s; prefix length uniformly from integers 20..159. Full brake for 20 warm ticks,
then drive the prefix with the previously fixed relay: throttle .45 below target,
otherwise zero; brake min(.2,.2*(v-target)) only above target+.1. Zero steering,
unchanged vehicle physics, fixed ClearNoon weather, 50 ms ticks and <=10 ms physics
substeps. No forced speed, within-episode teleport, sample deletion or retry on
an unfavorable outcome. Abort on infrastructure inconsistency.

At the prefix endpoint, record current state, last acceleration and actual gear,
compute ONE additional relay command, execute for one 50 ms tick, then full brake
for 40 ticks (2 s). Save every warm/prefix/command/backup snapshot, control
readback, body dimensions/offset, collisions and input plan. Roles are frozen:
100 training, 299 calibration, 400 held-out test episodes; independent NumPy
PCG64 streams with seeds 2026100101, 2026100102, 2026100103 respectively.

For every episode, in the reference body frame, derive a rounded rectangle with
half dimensions 2 m and 1 m plus four target extensions: forward, rear, lateral,
and the first sampled time from which ALL remaining recorded speeds stay <=.02
m/s, with at least five samples remaining. Include actual bounding-box offsets
and rotation in spatial targets, and include the reference pose and all 41 future
samples. If a collision occurs or no stable speed band exists, mark failure and
use infinite joint nonconformity (never omit it). Spatial observations continue
through the full 2.05 s even after the recorded speed band is reached.

Fit two predictors using ONLY training episodes: a constant mean baseline and
ordinary least squares with fixed features [1,v,v²,last_acceleration,
gear_is_1,planned_throttle,planned_brake,target]. Predictions are clamped to
nonnegative spatial extensions and >=.05 s time. Fixed residual scales are
[.1 m,.1 m,.1 m,.1 s]. Score each calibration episode with the maximum normalized
one-sided residual across the four targets; clamp score at zero. Use the maximum
of the 299 calibration scores for each method, with no tuning afterward.

For a FIXED trained predictor and iid calibration/deployment episode law, the
max-score tolerance bound has failure probability <=1% with calibration
confidence >=1-(.99)^299 (>95%). This is a population statement for this frozen
episode distribution, not a hard bound for every state, not a conditional bound
on a selected subset, and not an unlimited online guarantee. Both candidate
methods use the same data, risk target, joint score and correction rule. A joint
confidence statement about both methods requires a multiplicity adjustment;
report guarantees per method. The state-conditioned method is the prespecified
candidate; do not select a method from held-out outcomes.

On the untouched 400 test episodes report joint exceedances, exact one-sided
95% binomial upper bounds, predicted extents and duration, old traction-3 failures,
and fixed speed strata [0,.25), [.25,.75), [.75,infinity). No retuning or replacing
the test set. Also report geometry/time admissibility in ONE fixed saved free
region (dense_0_free_03_v0.5_h0.4.pvx), hypothetically placing the current vehicle
at that region's reference pose at age .13 s. Add .03 m pose margin; use the same
region and age for both predictors. This is a counterfactual geometry check, not
actual joint sensing/driving. Conditional-on-admission error may be larger than
the marginal 1% bound; report it separately and do not promote it to 1% safety.

Unobserved inter-sample excursions, persistent post-window drift, changed weather,
maps, vehicles, controllers, or state-selection laws remain outside this claim.
Record them as limitations rather than deriving hard physics from finite data.
