# Separately frozen shape-uncertainty extension

After the sphere study, test the SAME36 received histories with opaque
ellipsoids having longitudinal semiaxis r_max, transverse/vertical semiaxes
r_min. Each contains its stipulated opaque core and is contained in the
stipulated outer sphere. Its long axis is the fixed inward/outward motion axis.
This changes the candidate family, not the received observations, core/outer
contract, past speed controls, action footprint, lower bound or200ms reserve.

Use the original720 direction/50ms coarse/5ms refinement grid. Compute exact
ellipsoid/nominal-rectangle contact by whitening each rectangle edge and
point-to-segment projection. Check all3D ray segments in ellipsoid coordinates.
If epsilon is the Euclidean endpoint Hausdorff-error bound, transformed error
is at most epsilon/r_min. Require normalized segment distance strictly greater
than1+epsilon/r_min+1e-8/r_min. This suffices for every permitted endpoint error;
the real ellipsoid has the ORIGINAL semiaxes, not these inflated bounds.

Independently audit normalized segment distances using a quadratic form and
rectangle collision by four clamped quadratic edge minimizations. Reuse all
original raw-source/prefix revalidation in the separately archived sphere audit;
extension audit checks that exact audit/source/study input hash and the bytewise
local/sheng equality, every shared history and all motion controls again.
Finite no-witness results are censored; this search establishes neither globally
minimal collision time nor road/terrain feasible alternative CARLA worlds.
