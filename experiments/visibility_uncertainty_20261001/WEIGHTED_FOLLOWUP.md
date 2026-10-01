# Post-diagnostic finite heterogeneous-error comparison

The completed first audit found zero certificates for all tested 50 ms scan phases after discarding rays whose aligned error exceeds 0.05 m. That observation motivates this follow-up, not an undisclosed change to the original protocol.

Use the same twelve static source clouds, input componentwise error 0.002 m, two modeled scan periods and four phases. Give every ray its own conservative projection-plus-motion bound. Group errors in 0.01 m bins, rounded upward, and union the safely excluded center tiles. No ray obtains a smaller bound than the projection/time computation. Keep r_min, r_max, v, a, query, clock and spatial grids unchanged. For comparison, old fixed-cap results retain their original numbers. Profile.error is explicitly set to zero in the heterogeneous-error API because the supplied per-ray bounds already include the full error; this is not a zero-noise assumption.

Compute primary 0.1 m and small-core 0.05 m results separately for all cases. Save computation cost and both positive and zero outcomes. Tests additionally sample one hundred sets of asynchronous empty witnesses around a continuously moving opaque disk; the current center must never be excluded. Production checks use actual placed actor centers only as evaluation labels.

Before production, add a stronger matched baseline: choose the best common error budget over the same 0.01 m error-bin endpoints, retaining all rays below that budget. It uses the same observations, timestamps, model and grids, without evaluation labels. Report this baseline even if it explains all apparent heterogeneous-error gains. Do not equate beating a fixed 0.05 m cutoff with establishing novelty.

This implements a more faithful sufficient bound, not a novel weighted-Voronoi or reachability theorem. It does not yet modify the deployed proof-packet format or demonstrate rolling-sensor hardware/closed-loop driving. Any advantage must be described under identical supplied error contracts and hypothetical per-ray times.
