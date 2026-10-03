# Finite timing-completeness follow-up

After inspecting the first evaluation implementation, raw XYZ array assembly was
found outside its timed interval. Keep every initial output and timing unchanged.
Rerun processing only, without new capture or changing any centers, radius,
availability decision, packet or horizon. Load archived raw arrays before timing
as stand-ins for already received sensor buffers, then include XYZ assembly,
world transformation, component extraction, center quantization, encoding,
verification and both query calculations in three whole-pipeline measurements.

Assert byte-identical messages and identical horizons against the frozen initial
analysis. Record XYZ assembly time separately. Final conservative accounting uses
the maximum of the new complete-pipeline observations and the old pipeline maximum
plus the new maximum assembly time. Charge the same observed capture callback and
modeled link/clock/action terms. This is a sum/max of observations, not WCET.

NPZ disk replay, logging and capture startup/settling remain outside the modeled
online interval. The frozen entire-episode availability decision still requires
both sequential static views; this measurement does not establish a causal live
family-completion schedule or authorize driving. Preserve the initial705 positive
query outcomes separately; only the follow-up's charged outcomes are final.
