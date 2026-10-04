# Frozen fresh whole-episode shape-support qualification

One finite new CARLA0.9.15 Town10HD_Opt/ClearNoon batch, not a recurring job.
The pose_support_20261004 data and all earlier corpora are development only.
Six known classes, one known actor per episode, same fixed road and RSU layouts.
Ninety-five calibration and60 test draws perclass. Seeds2026103100+class and
2026103200+class, NumPy RandomState. Position U[-8,8]x[-4,4]m, yaw U[0,360),
vehicles speed U[1,3] and walker U[.5,1.8]m/s. No replacement for failed spawn.
Same30 settling ticks,3 sensor warmup ticks, physical motion for21 ticks@50ms.
Retain two simultaneous source scans at steps0/5/10 and all21 truth snapshots.
Store every-fourth semantic return, but labels are audit only. Additionally
measure the actual stride-four copy during capture; do not simulate its cost.
The collector differs from the prior one only by that timing field.

The fixed old XYZ-only background map, known extents, complete point-group
frontend, exact hull reduction,180-cell yaw cover,8mm quantum allowance and
fixed near-upright padding remain unchanged. The near-upright construction is
ONLY a feature/prior of an arbitrary SET PREDICTOR, not a required physical
assumption for the statistical current-center coverage claim. Freshly score
membership directly, including tilted/mixed/poor detections. Do not reject
episodes using hidden pose or retune the padding/background using new results.

For each available source, body score=min over groups of max-point radial
excess above ceil(R3D)+8000um. Pose score=minimal nonnegative uniform rectangle
expansion that includes the true source center in some group/cell. Joint score
is their maximum. Both scores use exact binary-rational truth coordinates and
integer upward radii. Score each whole episode by max across all six sources;
missing frames and wholly failed plans issue no new fact and have score0.
Use max of95 calibration episode scores perclass as common delta for BOTH
models. Write an immutable calibration receipt before processing test packets.
Test scores are diagnostics and cannot alter registry, model or policy.

If independent complete episodes follow the frozen law, the probability over
calibration that any class's episode-any center-exclusion risk exceeds5% is
at most6*(.95**95), regardless of whether the shape prior holds. This controls
one joint current-center event; it is not conditional-on-grant coverage, infinite
stream coverage, unknown inventory or a future physical guarantee. Read THEORY.md.

Four paid policies: sphere_hull,pose_hull,joint_hull,joint_raw. All hull policies
use the identical complete hull message and identical common source profiles.
RAW receives full retained XYZ, recomputes frontend and exact hulls before the
same joint inference (strong optimized baseline). Every policy measures three
complete source/decoder jobs; no cached geometry receiver timing. Source fee
adds the capture's real stride-copy observation to complete XYZ extraction and
wire/frontend/hull processing maxima. RAW source pays extraction and actual
RXYZ encoding; complete geometry is receiver work. Do not use hidden target IDs,
true center, actor pose, future observations or other views in runtime inference.

Actual checksummed zlib6 setup registers old static-map fitting provenance,
catalog, basis/transforms, grid, fixed sources, delta and motion/query parameters.
RAW header uses a separately pinned fresh transport identity and calibration
hash, not the old producer's header. Cold pays setup through the same source,
link and receiver FIFOs at t0; service/native runtime is already initialized.
Warm assumes previously installed context; neither is a cold-process benchmark.

Link20/2Mbps, propagation20ms, reserve220ms, cap500ms, query±6m/R.75m,
body disc R3D and displacement5t+1.5t^2m remain fixed. Keep source epochs;
receiving never refreshes age. Every360 planned test episodes has32 queries;
all failures remain in11520 denominators. Refused/precision-missing facts preserve
old still-valid deadlines; a jointly empty model revokes. Receiver chooses the
maximum lower source lifetime on ONE joint coverage event, without independence.
Its lower bound is not an exact optimum for the joint intersection.

Independent auditor reconstructs raw XYZ groups with separate SciPy raster,
all-point projections and exact fractions, ball/hull certificates, calibration
receipt, real packets/selection/processing maxima and all three FIFOs. Verify
the frozen plan/sources before capture/evaluation. Test episode-any exclusions,
availability, perclass one-sided95% upper bounds, six-class simultaneous upper
bounds, source oracle gaps, tilt-prior diagnostics, measured fees and sampled
future grid conflicts. Report all failures without changing criteria.
Check captured nominal bbox extent/corners and center displacement separately;
no continuous physics, ray/mesh optimum, radio/ego or novel selector claim.
Owned server lifetime<=60min, capture timeout3300s, ownership-checked stop and
scene cleanup. If a process stops unexpectedly, retain partial outputs and cause;
an observation timeout alone must not restart this finite batch.
