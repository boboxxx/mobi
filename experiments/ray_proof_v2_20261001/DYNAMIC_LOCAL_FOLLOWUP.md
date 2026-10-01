# Finite support-local optimization follow-up

The first new 128-frame live dynamic monitor produced 23 geometrically valid packets but only one passed the declared timing budget. Preserve this result. Per-frame source computation increased substantially when the simulator was active.

The next implementation computes nominal crossing eligibility/positions, searches for supports in an expanded bounding box, and computes full uncertainty only for selected raw rays through the unchanged receiver verifier. A local result is used only if its nearest distance is strictly below the expansion margin and it has a unique nearest neighbor; otherwise the algorithm falls back to the reference full nearest-neighbor tree. Points outside the expanded box cannot beat the accepted local neighbor. Future/old-ray rejection remains global and unchanged. No physical bounds or horizons change.

First rerun all 1,392 saved renewal cases against the original packet bytes. Only after exact agreement, repeat the SAME two-layout, 64-frame-per-layout moving-vehicle protocol in DYNAMIC_PROTOCOL.md, with the local backend. These are new runs with simulator timing variability, not an exact paired physical trajectory or a demonstration that all scenes meet real-time deadlines. Cold initialization remains unchanged. No ego controller is added by this optimization.
