# Finite prospective component calibration and selective policy certification

Models, support guard, scores, geometry, queries and service policies are frozen
before capture. Sources and complete dependencies must be published on GitHub
before any new scene runs. The previous datasets are development only.

Plan2520: six classes ×260 calibration episodes,600 IID certification episodes
(uniform random class), six classes ×60 test episodes. Coordinates/yaw/speed are
drawn from a fixed integer grid: longitudinal ±8m, lateral ±4m (1μm steps), yaw
0..359.999° (0.001° steps); vehicle speed1..3m/s and walker0.5..1.8m/s (1μm/s).
Each certification episode independently selects one of32 scheduled query indices
using a different RNG stream before capture. Whole episode is the IID unit.
Integer-grid law is new and differs slightly from the previous continuous grid;
no cross-law or real-traffic conditional claim is made. Class, scene and selector
seeds are in make_plan.py. Audit regenerates every draw. Failed spawn/capture is
retained as refusal, zero emission/score and32 failed-to-authorize queries.
No replacements, label-dependent reordering, retries, threshold repairs or tuning.

The collector retains exactly the prior six scans (steps0/5/10 ×two RSU layouts),
21 physical truth snapshots, semantic-LiDAR stride4, background XYZ frontend and
fixed known actor inventory. Runtime never uses semantic IDs or true center.
Town10 ClearNoon static RSU fixture with independently moving physical actors;
this is NOT a real ego control loop. Actor body extent, speed5m/s and acceleration
3m/s² are declared bounds. Motion/body snapshot checks are diagnostics.

Separate calibration components: two supported score maxima across all source
frames of each full episode, and one shared fallback max body/pose error in μm.
Inactive components are0. Supported expansion remains pose10mm ×Q and circleσ×Q.
Fallback uses its direct μm threshold in joint body/pose geometry. Four controls
joint/ridge/local_mean/local_modes retain their frozen original score/inference.
Empty observations refuse; no unknown-actor guarantee follows from their absence.

Maximum260 calibration episodes/class yields18 component events each at2.5%
exclusion plus24 baseline events at5%. Their simultaneous bad-calibration bound
18(39/40)^260+24(19/20)^260=0.024954427814 ≤0.025. A proposed family's two components
have marginal entire-episode union risk≤5%; this is not support-conditional risk.
Write calibration receipt BEFORE any certification cloud processing. Separately
process/profile certification, write selective policy certificate BEFORE any test
cloud processing, then process/profile test. Receipt hashes enforce ordering.

All6 families ×function/deadline ×20/2Mbit/s ×warm/cold =48 fixed policies. Source
and receiver each profile3 repetitions per packet; method order is deterministic
hash shuffling. Shared necessary registered context and source epochs are paid.
FIFO source/tx/rx,20ms propagation,32 fixed queries,220ms action reserve,500ms cap.
Fees are measured maxima, not WCET. No real wireless, attestation or distribution-
shift guarantee. The certification law includes the specified profiling service;
IID environment/timing is an explicit assumption that measurements cannot prove.

For the single preselected query per certification episode, test two binary losses
conditional on grant: reference-source score exclusion and source-age+action beyond
the oracle (which itself assumes known body/motion).96 exact-binomial tests at
risk5%, familywise confidence error0.025; zero errors require161 selected queries.
Accept a policy only if BOTH tests pass, otherwise refuse deployment. Combining
calibration and policy confidence budgets gives at least95% under their declared
IID laws. This is standard LTT/Bonferroni, not a new statistical result. Entire
certification data, including failures and selected facts, are published.

The held-out test reports every planned episode and all raw/accepted-policy
queries, oracle gaps, exclusions and age overstatements. Neither zero errors nor
passed5% certificates imply road safety. Novelty and MobiCom feasibility still
require convincing mobile bottleneck comparisons and real closed-loop evaluation.

Finite capture timeout9000s, owned CARLA lifetime10800s. Stop only the owned PID
with matching executable and start timestamp. No recurring research automation.
