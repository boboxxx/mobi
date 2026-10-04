# Fixed finite actual-ego episode risk certificate

Prior far/near driving and all earlier fixed-observer data are development data.
This new controller and complete plan are fixed before fresh certification scans.
No model, registry threshold, feature, sensor, body or target-motion retuning.

## Three candidates and observation law

Function geometry, a direct single-pack compact scalar deadline, and a compact Lipschitz-cone distance lower bound. All perform
one identicalXYZ frontend/model pass and one wire compression; deadline/cone additionally
computes its source query, function computes that query at RX. Registered target
classes are Audi/Bicycle/Walker. Standard Audi ego, full3D body, same RSU view0,
Town10HD_Opt/ClearNoon. All targets are parked. Actual single-pack payload length,
source acquisition/copy/encoding, RX compilation and query fees are charged in the
20Mbps FIFO+20ms propagation synchronous co-simulation. No uplink fee; source has
current ego odometry.50ms physics/10ms substeps; unpaced, no actual wireless/WCET.
The scalar source query has150005μm extra radius, covering0.75m/s*200ms plus outward
coordinate-rounding margin under that declared speed condition.

Each new episode:40 settle+3 sensor warm steps,60 drive steps and40 final full-brake
steps. A fresh source is emitted every third drive step:20 sources over3s,6.67Hz,
with20Hz ego control. Source/control steps30..49 are dropped (7 emitted sources).
This is a NEW finite3s observation/controller law, not certification of the older
160-source episodes or indefinite driving.0.3m/s manual feedback,0.75m/s declared
ego cap,300ms action budget and x[-10,-3]/±0.5m corridor unchanged. Empty sets refuse;
epoch is the original source physics timestamp, never arrival time. All production
road-authorization flags remainfalse.

## Independent plan and no outcome reuse

SCENE_LAW.json specifies243 finite scenario cells: three classes, ego distances6/7/8m,
target lateral/longitudinal offsets{-10,0,10}cm, target yaw offsets{-10,0,10}deg.
Each coordinate is sampled uniformly with replacement by SystemRandom; complete
612-request plan is saved before capture. For each of the three methods,180 certification and24
held-out test episodes. Method order rotates; scenario draws are independent,
not matched pairs. No failed replacement or threshold tuning. All raw scans,
actual packets, profiles, attempts, complete/partial trajectories and failures
retained. Model input usesXYZ/own odometry/registered class only; scenario target
parameters and semantic IDs/labels/truth remain outside the runtime features.

## Statistical unit, event and acceptance gate

One sample is a complete planned episode. G means at least one experimental
geometry/control authorization was attempted. F on an accepted episode means any
used source set excludes true source center, any used source age+query fee+300ms
exceeds the same-body/motion true-center oracle, any recorded sampled operational
boundary/collision occurs, or capture is incomplete. An incomplete accepted episode
is conservativelyfailed, not removed. Incomplete unaccepted episodes stay as
refusals in the complete plan. Related sources and decisions are not independent
samples; all their failure indicators are combined inside F.

No old six-frame calibration confidence is inherited. Registry/model outputs are
fixed proposals. For each fixed method independently apply the exact conditional
binomial test on the n selected episodes and k failures. Risk target5%, three methods,
joint error budget5% with Bonferroni δ_method=1/60. Zero-failure acceptance needs80
selected episodes; all180 planned episodes remain visible. A method failing the
test refuses all engineering actions in the held-out test; no retry/extra sampling.
Certificate is frozen before test_capture exists and checked by an independently
implemented rational binomial recurrence. Test geometry eligibility and refusals,
progress, fees and losses are reported for all72 planned episodes.

The confidence statement REQUIRES joint IID episodes including actual profiling/
service behavior. Random scene draws do not prove timing IID. Consequently this
is a conditionally valid finite constructed-scenario certificate, not a certified
physical collision probability, continuous braking guarantee, arbitrary actor/query
law, unknown obstacle completeness, density shift or actual radio certificate.
Neither sampled boundaries nor3s horizon justify indefinite driving.

Server owner identity is checked on cleanup; all actors removed and sync restored.
This is one fixed finite batch, not a continuous research or recurring automation.

Cone wire carries only anchor/query center and center-distance lower bound L0.
At a receiver query q, the lower bound is max(0,L0−ceil(||q−q0||)), then the same
integer body/radius/motion horizon. This follows from1-Lipschitz distance and
source center membership, not a new theorem. Source epoch is unchanged; no
fixed source query-radius containment refusal is needed. This strong compact
queryable comparator prevents attributing scalar padding overhead to an inherent
advantage of transmitting complete geometry. Its changed selector is separately
certified, without borrowing the function/scalar certificates.
