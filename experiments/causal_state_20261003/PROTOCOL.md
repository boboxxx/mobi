# Frozen finite dynamic single-frame evidence experiment

Freeze before new capture. Prior static data are development only. Six known
CARLA0.9.15 blueprints, Town10HD_Opt/ClearNoon, inherited known extents/road/sensors.
Each class has95 calibration and60 independent test episode draws. Seeds
2026101100+class and2026101200+class. Position U[-8,8]x[-4,4]m, heading U[0,360).
Target speed vehicles U[1,3]m/s; pedestrian U[.5,1.8]m/s along its random heading.
Set target velocity each tick for physical vehicles, WalkerControl for walker.
No physics freeze during motion. Retain spawn failures without replacements.
Two fixed RSU sensors are simultaneously active; steps0,5,10 at50ms ticks retain
scans (every fourth return) and all steps0..20 retain actor-truth snapshots.
Allow30 settling ticks and3 sensor warmup ticks. Known actor count/class is part
of this controlled experiment; it is not an inferred scene inventory.

Use exactly the earlier frozen XYZ component detector, unchanged; labels never
enter extraction. EACH frame emits all candidate centers or refuses if none.
No output waits for or consults any other view or future frame. Calibration score
is maximum true-center distance to nearest proposal over the six sampled frames
of an episode, with refused/missing individual frames contributing0 since their
output is full-plane/no authority. Wrong nonempty proposals contribute actual
error, not0. Max of95 episode scores gives q per class; add outward micrometer
rounding and8mm for1cm center quantization. This max tolerance statistic gives,
under iid complete episodes and a fixed frontend, probability at least
1-6*(.95**95)>95% over calibration that ALL six class episode-exclusion risks are
<=5%. It is not conditional on availability, not unknown-scene or indefinite
stream coverage. Calibration-family membership involves six observed snapshots,
not continuous future trajectories. Distribution drift/control interaction
invalidates the iid premise; no theorem is asserted for such deployment.

Packets use pinned contract/calibration/frame/time and prior PCS1 codec. Receiver
uses only delivered current/past messages. Expiry queries(-6,0),(6,0), R=.75m,
body ceil(norm(extent)), v=5m/s, a=3m/s^2, cap500ms. Full model geometry unchanged.
Observed callback and complete processing costs are measured;20Mbps and2Mbps
wire presets,20ms propagation,20ms clock and200ms action reserve. FIFO causal
trace replay uses original simulation timestamps plus measured observed costs
as modeled duration, not wall-clock live real-link authority.

Compare (1) all frame union packets FIFO; (2) all-frame unquantized-center lossless
packets using same radius and outward quantum protection (strong same-state
baseline, no artificial full-point-cloud requirement); (3) zlib full sampled XYZ
source transform packets whose receiver recomputes EXACTLY the same union;
(4) fixed200ms lifetime on same union, truncated by500ms cap (diagnostic may exceed
geometric expiry and must report violations). Query-grant validity requires the
receiver's absolute source-age deadline exceed NOW plus220ms clock/action reserve;
propagation and observed pipeline/serialization/queue costs are paid on arrival.
No free transport/compute/sensor schedule. Reject stale/reordered identities.
The sender does not use labels, future observations or ideal recipient knowledge.
No policy hyperparameters may be selected using fresh tests. Same-state baselines
may tie or beat the compact packet; report it. No SOTA/novelty claim from these alone.

Check episode-any coverage over all scheduled60 tests/class, calibration risk
confidence, per-frame availability, class and scheduled query denominators,
all queues/bytes/ages/deadlines, and truth-center modeled contact at entire grant
interval end. Also check captured physical center displacement against D(dt),
actor bbox extent/corners and sampled query occupancy. Those are finite snapshot
audits, not continuous physical safety or driving closed-loop proof.
Independent reconstruction/audit and targeted causal prefix/queue tests required.
Preserve all samples, spawn failures, output hashes, timing and cleanup receipts.
Own CARLA process is finite, exclusive, cleaned and stopped after this batch.
No automatic recurring research job. Full original research objective persists.
