# Finite receiver scheduling diagnosis,36 complete planned episodes

The previous612-episode batch is development evidence: its conditional risk test
passed while all test progress was practically zero. This new batch investigates
one specific implementation hypothesis, not a new certified driving policy.
No old six-frame or whole-episode certificate is transferred. All production flags
remain false; no recurring job, replacement, extra sampling or outcome retuning.

Four fixed variants: source period150/100ms × deferred/immediate receiver use;
3 methods ×3 registered parked classes at8m =36 episodes, each3s driving+2s
final brake. No offsets/yaw perturbations in this finite development diagnostic.
All variants have one identical source frontend/model and one pack, actual
20Mbps FIFO/20ms modeled propagation, identical20Hz control and frozen model/
registry. Source capture/copy/encode, decoder and query fees are measured and
retained; no uplink fee. Old source epoch remains unchanged.

Immediate mode decodes delivered packets in the current control step and pays
all current receiver fees plus query fees in the decision timestamp before
applying the command; it does not round submillisecond receiver work up to an
extra50ms control step. Deferred mode retains that additional step. All current
decoder fees are charged in BOTH variants, including decode of a packet not yet
selected. Reject if total receiver/query processing exceeds20ms. Full3D ego radius
has260000μm extra: .75m/s*(300+20)ms+20mm margin, covering processing plus the same
300ms action bound. This changes the observation/controller law, hence no old
risk certificate applies. Actual profiling, q/source integer gates, packet/data
hashes and sampled future body enclosure are replayed independently.

Period100ms increases source traffic from20 to30 packets per episode; that cost
is reported, not attributed to a free expiry improvement. Pair scenario cells
are fixed but timing and live observations differ; all36 raw/failed trajectories
are retained. The goal is useful physical progress and whether gratuitous
receiver scheduling destroys a short evidence lifetime, not a MobiCom novelty
claim or continuous/road/unknown-target/radio/WCET safety guarantee. Source
acquisition fees remain charged exactly as before; they are not removed to obtain
an apparent benefit. CARLA is unpaced synchronous Windows0.9.15; algorithm is
Ubuntu20.04 WSL on the same online Tailscale peer advertised as sheng.
