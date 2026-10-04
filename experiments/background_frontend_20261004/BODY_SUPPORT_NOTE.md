# Post-result body-bound support hypothesis

The accepted background producer, its descriptive centroid radii and its10 Sprinter
exclusion episodes remain unchanged. This is a separate post-result diagnostic.

For a known body enclosing disk of radius R centered at its true center x, every
actual target return p obeys |p-x|<=R under the body contract. Quantizing p to1cm
adds an outward8mm allowance. For one component G, a set of possible centers is
 C_G(delta)=intersection over p in G of disk(p,R+8mm+delta).
Use the UNION over all retained components; no nearest-target label selection.
A pure observed target component suffices for coverage at delta0. Purity is not
assumed proven online: the development score is
 min_G max(0,max_p distance(p,true_center)-(R+8mm)),
rounded UP in integer micrometers. Max over current frames and planned episodes
provides a descriptive slack fit on the same reused data. Empty output refuses,
and missing inventory cannot be turned into a free-space assertion.

Unlike a tight observed-box midpoint, these constraints retain the uncertainty
of an incompletely observed body without requiring its centroid to be unbiased.
Whether this set improves expiry after compute/wire cost is a separate question.
An enclosing body disk can make the support very broad. There is no proof that
all supported centers are compatible with original rays or physical meshes.

body_support.py saves complete quantized groups and uses exact binary-rational
true-center coordinates with integer square roots for developmental scores.
A separate body_support_audit.py reconstructs groups with BFS instead of raster
labels and checks scores/membership with Decimal. IDs serve only post-extraction
component purity diagnostics; they never guide grouping or select a component.

The first local float-score helper/output is preserved with suffix at_first_run.
The revised helper computes exact integer slack; this is a post-result arithmetic
clarification, not a revised frozen producer or new risk fit. No changed centroid
results, new capture, message, computed expiry or action authority is claimed.
Future frozen risk validation and paid geometry are required.
