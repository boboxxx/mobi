# Finite physical ego expiry chain

Freeze all code, twelve-run plan and analysis before new capture. No model,
calibration threshold, query policy or failed episode replacement after outcomes.
This is an unqualified controlled-simulation integration. All deployment/risk
authorization flags remain false. The simulator alone may exercise geometric
eligibility to diagnose physical behavior; production decision gates stay intact.

CARLA0.9.15/Town10HD_Opt/ClearNoon,50ms ticks/10ms substeps, standard Audi A2 ego,
one parked registered target (Audi/bicycle/walker), existing fixed RSU view0,
first-straight25m anchor of the frozen background. Two modeled propagation delays
20/80ms,20Mbps, paired function/direct-deadline. Reverse method order for bicycle.
Inventory contains exactly these constructed actors; this does not solve unknown
objects or multi-object completeness. Target semantic ID/truth is offline only.

Ego begins12m behind anchor. Forty brake ticks settle actors; three sensor warm
ticks.160 driving decisions plus40 full-brake decisions. Every driving tick
produce fresh XYZ evidence.256-channel2M/20Hz semantic LiDAR, retained stride4;
runtime reads only XYZ. Remove own-body returns using current own odometry and
known full3D bounding box +30mm; no target-ID mask. Retain raw labels for offline
mask/coverage audits. Static background, models and old calibration thresholds
are fixed proposals, not statistical guarantees in this new ego distribution.

Manual first-gear own-speed relay: target.3m/s, throttle.8 below target otherwise0,
proportional brake above target+.05 as in prior fixed feedback. Own speed>.6m/s
or ego outside longitudinal[-14,-6]m /abs(lateral)>.5m forces full brake. Declared
sampled ego speed cap.75m/s and300ms action reserve. Query center is own bounding
box center rounded to integer micrometers; radius=ceil(full3D body radius)+
225000+20000um, enclosing body plus.75*.3 motion and20mm margin CONDITIONALLY.
Neither the speed cap nor300ms braking is a certified continuous physical bound.

Function packets contain source hulls/hypothesis, source epoch and context hash;
RX compiles/query-caches the same frozen Evidence for current ego query. Direct
deadline computes at source current ego center, radius additionally enlarged by
150mm, sends its scalar proposal. RX independently requires current-action disk
containment in that source disk. Own pose is locally available to both in this
simulation; no uplink fee is charged. This favors direct deadline and is NOT a
distributed radio comparison. Same context, source model and body/motion law.

Actual source acquisition/copy/frontend/predict/encoding and RX decoding/compile
fees are measured once per actual packet. Source acquisition is the preceding
world-tick and matched-sensor wall duration. Link FIFO charges actual packet bytes
at20Mbps plus declared propagation. Decode runs only after arrival; its measured
cost rounds availability upward to a50ms tick. Query cost is additionally paid
in gate now_us. Source age is never reset. RX never exposes a future/pending
packet. Drops at driving source indices30..49 consume serialization but skip RX.
Cached evidence may be reused until source expiry, then geometric gate brakes.

Record every source raw cloud/actual packet, all source/RX/query fees, source and
arrival times, own masks/hulls/predictions/proposals, cache selections, controls,
actual body and target trajectories. Failures remain. Verify mask without ID use
at runtime, source-time nonrenewal, FIFO/drop/ready times, each control/gate,
actual forward progress, body enclosure over300ms sampled future, and sampled
stop confirmation after each go-to-brake transition. Check full-model frontend
replay and independent exact geometry on coverage-qualified states offline.

Synchronous measured-delay co-simulation, not wall-clock real-time/WCET, actual
V2V wireless, continuous collision avoidance or new selective risk certification.
No tuned winner selection, recurring job or indefinite experimental loop. Restore
settings/weather, actors zero, stop only exact owned server PID/path/start time.
