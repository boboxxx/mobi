# Finite online-cost diagnosis and follow-up (2026-10-02)

Stage 1 is explicitly post-analysis, selected from the previous failed batch:
view0_repair_r1 root000, root001, warm000, warm001, plus view1_repair_r0 root000
and view0_original_r0 warm000 as missing-coverage/history controls. Reconstruct
only the actual receiver history of that original run. Compare the unchanged
source generation under inherited numerical-library threads versus one thread,
four repeats each. One root and one warm call are additionally cProfile traced.
Environment changes apply to acquisition/source/receiver together in any fresh
follow-up; do not attribute thread tuning as a new algorithm or novelty.

Stage 2 implements an exact horizon search that visits cells in increasing
region distance and stops at the first unexcluded shell. Compare horizon and
boundary cell distance with the previous full-domain reference for ALL 37
archived full-ray/subset cases, including zero cases, and measured wall cost.
Costs include creation of indexes; cold and warm caches are reported separately.
No geometry contract, expiry inequality, ray-count cap or body bound is weakened.

A fresh finite controlled batch is permitted only after the observed generation
and verification cost makes its original action/expiry budget plausible. Freeze
the precise packet-selection protocol before that capture. Preserve failures,
use original and improved source algorithms at equal thread configuration, and
retain strict integer availability. No continuing research loop is created.
