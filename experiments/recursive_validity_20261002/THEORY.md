# Endpoint constraints tighten past travel, not future permission

For persistent class trajectories with norm acceleration at most a and verified
reference speed caps V0,V1 at times0,Delta, Lipschitz continuity implies
|v(t)| <= min(V0+a t,V1+a(Delta-t)). The path length and therefore displacement
are at most the integral D of that minimum. Set c to the intersection time
(V1-V0+a Delta)/(2a), clipped to [0,Delta]. Then
D=V0 c+a c²/2+V1(Delta-c)+a(Delta-c)²/2.
For a=0 use min(V0,V1)Delta. Equal caps give V Delta+a Delta²/4.
We round the floating implementation outward and retain the grid tolerance.
This is elementary bounded-motion reachability, not a new theoretical result.

The original contract bounds every class member at each actual selected ray
timestamp, including invisible members. At a reference d seconds after the
latest selected ray, V=v+a d. Thus both reference caps are available only after
the second raw observation has arrived and passed validation. This does not
work with visible-object-only caps, arbitrary births, or untrusted timestamps.
Persistent objects outside the local computational window remain UNKNOWN and
are injected at every prediction boundary. The same global class assumptions
were already necessary for the old forward collar and hidden-center bound.

Position posterior P1 conservatively contains (P0 expanded by D) intersected
with the complement of current whole-tile empty-ball witnesses. Fine tiles
reduce representation loss without changing radii, uncertainty or speed.
Forward method replaces D by V0 Delta+a Delta²/2. No measurement of actor
identity is assumed. Current ray quantization and individual ages are checked
in the unchanged original decoder/projection routine.

The stronger fixed-K baseline knows the body enlarged by pose+r_max contains
no class center at the old fact reference. Its previously verified collar
excluded every possible intruder within forward travel budget
B=V0(h+clock)+a(h+clock)²/2. If the newly justified past path bound D<=B,
continuous trajectories cannot enter K before the new reference, even if the
old declared action expiry has passed. Fully checking the new forward collar
then renews the fact and constructs a NEW expiry. This uses no free new prior,
no unverifiable sender checkpoint and no restoration of expired permission.
The known initial K comes only from the complete original accepted prefix.
Current fixed body region/motion and scope are immutable within each stream.

Future travel always remains V1(h+clock)+a(h+clock)²/2. Applying a future
unreceived terminal speed cap would be unsound. Validity is the greatest
integer h whose entire future required region avoids the possible-center
posterior and stays inside the computational domain. Zero frontier is a
conservative certificate failure, not proof of information impossibility.

Fact update and finite action authorization are separate. Verification must
finish before any new certificate can be used; action reserve must fit
strictly before expiry. A compatible old certificate may still apply when a
later overapproximated posterior has h=0. Positive frame admissions do not
imply continuous action coverage or actual useful vehicle control.

These conditional proofs do not calibrate opaque cores, outer radii, sensor
errors, timing authenticity, road behavior or actuator dynamics. Computational
caching can be exact and still offer no performance benefit under changing
geometry. Finite replay is an algorithm diagnostic, not MobiCom-level validation.
