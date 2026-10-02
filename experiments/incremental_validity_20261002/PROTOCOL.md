# Incremental uncertainty-checked horizon support: finite protocol

Frozen before measurements. Previous useful-lifetime experiments show full
cover reconstruction is too slow; nominal 4/16-neighbor repair uses many rays
and may fall back when asked to extend an old 400ms template to 475ms.

Keep the original raw-ray, heterogeneity/age, finite-domain, motion, history,
packet cap and strict integer deadline contracts. The old packet is a hint for
CURRENT ray selection only. Receiver history is reconstructed independently
from actually accepted archived packets, and every receiver check is complete.

After the same nearest-template proposal, compute required cells not supported
by its current rays or legitimate history at the new requested horizon. Only
these gaps are searched against ALL current rays with their recomputed error
bins. Add one proven-valid nearest witness per gap (nearest variant), or apply
the previously compiled exact greedy only to the added candidates/gap universe
(gap-greedy variant). Retain the base rays in both variants. Empty observations,
uncovered gaps, invalid ages/history and the ray cap must cause rejection.

Three paired methods: old 4/16-neighbor coverage reuse, uncertainty-checked
nearest gap patch, uncertainty-checked gap greedy. ALL methods use the SAME
compiled full-cover greedy fallback, a stronger baseline than old Python-only
fallback. Include attempted repair and fallback in generation timing. The new
sender checks typed coverage; unchanged full receiver decoding/geometry is
separately measured for every nonempty packet, as for the old reuse sender.

Stage 1: the same six explicitly post-analysis-selected original states, three
targets 400/450/475ms, three repetitions, randomized method order seed 20261003:
162 calls. Include sparse-view and no-history negatives. Verify source
provenance and reference full-domain maximal subset/full-input horizons on all
saved first-repeat packets. This is exploratory paired timing, not independent
scenario generalization or WCET. Common immutable grids may be warm.

Stage 2, if stage 1 completes: replay ALL 384 inputs in the ten October 2 live
runs at their original 475ms target, same three methods, once per input, with
method order rotated. All share the exact original receiver history and old
proposal template. Charge capture acquisition, measured source/receiver costs,
20ms+bytes*8/20Mbps for all methods; separately retain original fixed-link
conditions. Recompute strict 50ms tick-age + 200ms action timing, not actuator
effectiveness. This is a retrospective diagnostic on original histories,
not a new closed loop or an independent driving result.

Compile/load the frozen original cover.cpp before timestamped evidence;
record compiler, flags, compilation/load costs and binary hash. Record all
failures, method branches, fallback use, cost, bytes, rays and correctness.
No free maximum-horizon oracle, same-test calibration guarantee, physical
safety, moving fallback or MobiCom novelty claim may be inferred.
