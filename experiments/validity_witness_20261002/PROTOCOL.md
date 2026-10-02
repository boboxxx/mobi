# Frozen finite ray-consistent adversary diagnostic

Purpose: test whether zero or short conditional validity could be caused by a
feasible hidden trajectory, rather than merely the positional grid/caching.
This is a kinematic finite counterexample search, NOT a new planner, true
CARLA counterfactual, physical calibration or a complete impossibility proof.

Use all six verified histories from recursive_validity_20261002, targets22,25,39,
and both physical classes:36 cases. Each uses the COMPLETE42 accepted prefix
raw dictionaries plus source20 through its target, with original world-frame
origins/endpoints/actual ray timestamps. No future frame or dropped-source
oracle is used. These are standard-link histories, not blackout histories.

Search720 directions at0.5degree spacing and nominal dangerous times0:50:1500ms.
If a time has any passing candidate, refine the preceding50ms interval on a
5ms grid for all720 directions and retain the lowest passing candidate. Search
failure means only no witness in this finite family, never impossibility.
Compare to each original fine-terminal class horizon and the joint horizon.

Candidate is an opaque3D sphere with radius the class r_min, contained within
the permitted r_max, with center on the fixed task plane. It moves straight
inward, at speed5 at EVERY actually selected timestamp. Between consecutive
timestamps, inward speed increases at3m/s² for the first half and decreases
at3 for the second half; speed is continuous and acceleration norm≤3 a.e.
Before the first timestamp use constant5; after the last use acceleration3.
This attains the elementary equal-endpoint past travel bound; reference-time
age is handled exactly on the integer-microsecond time axis.

At the chosen dangerous time the sphere penetrates the SAME nominal stationary
rectangle (half dimensions2.3/1.3m) by a1mm radial allowance. This is an upper
bound on the formal rectangle-occupancy certificate task under the specified
kinematic class, not on actual Audi body collision or road-feasible motion.
No road/lane/wall-avoidance constraints are assumed by the original class model.
Persistent objects may originate outside the finite computational grid.

Require the sphere to miss EVERY selected3D ray segment (including endpoints)
at that ray's actual timestamp by r_min +sqrt(3)*max(point_error+.0005,
origin_error+.0005)+1e-8. This is stronger than simply avoiding sampled planar
witnesses: it remains clear under every allowed componentwise endpoint/origin
perturbation. The entire sphere is opaque; no transparent appendage or shape
oracle is used. Other selected source geometry is retained unchanged.

Search in compiled C++ for speed; independently audit chosen trajectories with
vectorized NumPy projection onto all actual segments, separate cumulative
travel derivation, endpoint speed/acceleration, collision penetration and all
source/cloud provenance plus complete trusted-prefix verification. Archive all
36 searches, failures, chosen controls and minimum clearances. Run tests and
independent audit on sheng and locally. Count measured search costs separately;
this does not produce an online algorithm/WCET guarantee.

If a witness intersects the formal action rectangle before the stipulated
200ms action reserve even with zero delivery age, it rules out that requested
rectangle certificate on the SAME received information/kinematic assumptions.
It does not rule out another footprint, controller, risk criterion, extra
sensor observations, tighter physical class or physically constrained model.
