# Class-specific facts and joint finite permission

This is a conditional set-membership construction, not a claim that physical
bounds have been learned or that the construction is novel. It inherits the
original opaque-core, outer-radius, ray-endpoint/query-error and fixed-body
contracts. Every hidden object satisfies the class speed cap at each actual
selected-ray timestamp and the norm acceleration cap at all intervening times.
There are no unmodeled births. Relative timestamps share a truthful common
phase; the20ms future margin does not validate arbitrary packet clock drift.

Let R be the stationary nominal rectangle, rho its pose margin, r_c the outer
radius of class c, and B_c a receiver-owned displacement budget. The retained
fact is that no class-c center lies in

    F_c(t) = R (+) ball(rho + r_c + B_c).

The complete, revalidated root proof establishes this fact. A packet saying
"no detections" or an unregistered Region object cannot establish it. The
implementation revalidates every accepted parent, including the age/future
cross term, before registering its child. Warm history construction is measured
separately; final-root verification and delivery are charged in the main study.

For a new received reference t+Delta, let V0,V1 be the speed bounds extrapolated
from the last actual observation to each reference. The past displacement is
bounded by

    D_c = integral_0^Delta min(V0+a*s, V1+a*(Delta-s)) ds.

For equal endpoints this is V*Delta+a*Delta^2/4. The implementation integrates
the two pieces; the independent audit uses the closed form. It rounds outward.
Neither endpoint argument is available for an unobserved future interval.

Eroding the known free region by this displacement leaves the sufficient
center-free region R (+) ball(rho+r_c+B_c-D_c), when r_c+B_c-D_c is nonnegative.
The implementation rounds its radius downward and only removes grid cells
whose entire cell is strictly inside. A negative inherited radius removes no
cells. This is stronger than discarding the inherited region whenever D_c>B_c:
the region can shrink while current rays prove the newly exposed annulus.

For a requested class horizon T_c, define the one-sided future budget

    B'_c = V1*(T_c+delta_c) + a*(T_c+delta_c)^2/2.

Every whole cell touching R (+) ball(rho+r_c+B'_c) must be excluded by the
inherited region or by current received rays. A ray excludes a cell only when
its opaque-core margin exceeds endpoint/projection/age uncertainty and the
cell half diagonal, with strict numerical slack. If any required cell is
unproved, the scalar update fails and retains its previous fact reference.
If all classes pass, store every B'_c but authorize only H=min_c T_c.
Thus the next update can use a class fact longer than the joint action grant.

Receiver service, transmission and execution consume the grant. Verification
must finish before use, and the study requires A+200ms<H, with A rounded upward
to a50ms action tick. No action is authorized while checking a packet. After
expiry the old action remains forbidden, even when an old geometric fact can
support a newly verified update. This is a stationary authority interface;
the200ms reserve is not an experimentally validated moving backup controller.

## Why the experiment is diagnostic

The source selects enough additional actual current-scan rays for T_small=525ms
and T_vehicle=475ms. It retains every original ray and does not rewrite their
physical metadata, sequence or timestamps. The scalar packet request remains
475ms; target class horizons are trusted receiver policy and are fully checked.
The augmented fine observer receives the exact same observations. Its gains
therefore test information availability independently of the scalar formula.

Increasing a class fact does not necessarily extend H immediately: another
class may limit the current action. It can nevertheless prevent a future fact
chain from failing. This prospective value is a research hypothesis about
communication decisions; this package implements fixed targets, not an optimal
adaptive scheduler. Classwise reachability, erosion and fact retention are
established ideas and are not claimed as new contributions.

## Conservatism must use the same information

For received observations O and contract C, let H*(O,C) be the earliest possible
task violation among all compatible hidden trajectories/worlds. A conservative
proof gives L<=H*. A fully checked compatible trajectory colliding at U gives
H*<=U. Therefore missed lifetime is at most U-L; for L>0 its relative fraction
is at most1-L/U. A finite search cannot prove that U is minimal.

After adding rays O becomes O'. The original U is not automatically an upper
bound for H*(O',C). The separate fixed84-candidate check reconstructs the full
augmented history and rechecks each complete3D body. Failed robust-clearance
checks are censored, not declared impossibility results. Surviving candidates
still only inhabit the abstract ray/kinematic model, without enforced roads,
walls, terrain or an actual alternative CARLA world. The newly measured lower
bound and surviving upper are both relative to O', not to the old information.

## Limits still open

The data reuse six stationary, repeatedly quantized saved histories. Three
timing repeats are not independent scenes. Links and queues are modeled; CPU
service is measured. Bootstrap41-proof cost is not hidden, but cold online
initialization remains unsolved. The nearest-witness source augmentation is
two-pass and nonminimal, and all its additional measured work is charged.
Its actual utility must be judged by usable action duration after costs, not
geometric success alone. Physical calibration, changing scenes, moving control,
real links and a defensible comparative MobiCom contribution remain required.
