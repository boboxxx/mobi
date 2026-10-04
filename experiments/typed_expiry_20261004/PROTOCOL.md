# Finite typed-fallback development probe

The earlier balanced probe improved motorcycles and worsened five classes by
loosening supported pose geometry. This candidate retains the supported pose
unit10mm and the existing local circle unitσ(X). Supported score is
max(pose_violation/10000, center_error/σ); its pose/circle expansions are
ceil(Q10000) and ceil(Qσ), identical to the original local rule at the SAME Q.

Only fallback normalization changes: both body/pose error units are the known
3D body radius b (minimum50mm), with fallback score
max(body_violation,pose_violation)/max(b,50000). Its runtime is joint body/pose
with ceil(Q max(b,50000)) slack. Empty observation refuses. Models, guards,
features, learned scales, queries, motion/cap and body bounds stay unchanged.
Each family still has one entire-episode maximum score across both types.
There is no group-conditional or query-conditional coverage claim.

All prior capture data including earlier test outcomes are development for
this candidate. Freeze its two families, code and dependencies BEFORE executing
this finite probe on sheng. Do not adjust any rule based on outputs during the
probe. Preserve all planned125/60 episodes/class, failed captures, excluded
centers, age overstatements and worse source queries. No new qualification,
profiling, radio measurement, live ego or MobiCom novelty is claimed here.

Shared predictor replay is checked against pinned parent data. Independent
audit reconstructs rational scores, both unit systems, supported pose/circle
distance and containment, fallback exact sphere certificates, max registry
and all source oracle-gap totals. Successful development alone cannot certify
deployment. Independent score calibration, conditional-policy certification
and test must follow before those claims.
