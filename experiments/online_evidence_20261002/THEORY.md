# Exactly the same horizon with fewer coverage queries

The fixed-region certificate and physical assumptions are unchanged from
`../expiry_frontier_20261001/THEORY.md`. Let d(x) be a grid-cell center's distance
to the fixed rectangle. All queried future horizons require a prefix of the
cells ordered by d(x), because required inflation is monotone in horizon.

Sort the cells once per domain, step and rectangle. Check their current-ray and
legitimate-history exclusion in increasing distance batches. The first unknown
cell has minimum unknown distance: all unchecked cells are at least as far.
A batch may examine extra cells but its first unknown is exact. If the entire
prefix needed at a capped horizon is excluded, farther unchecked cells cannot
invalidate that capped horizon. Domain failure is separately bounded using the
original strict inequality. Integer binary search then matches the old kernel.

For the joint certificate, after one class limits the horizon to H, another
class only needs to exclude its required prefix at H or identify a smaller
boundary. A zero result terminates the joint search without claiming the other
classes were checked. Returned per-class caps can differ from the old unconstrained
per-class maxima; the JOINT horizon and reported unknown distances agree. The
algorithm does not count all unknown cells, unlike the full-domain diagnostic.

Index construction is included in cold ordered-index measurements. Repeated
calls may reuse only the immutable distance order. Neither ray coverage nor
receiver history decisions are cached across changing observations. Ties keep
the original cell order. This is numerical equivalence to the existing float64
verifier, not a new physical theorem or formal interval-arithmetic proof.

The repaired sender additionally computes projections and gaps once per proposed
ray subset. The old sender verified a failed serialized candidate, recomputed
those same projections to find gaps, then verified another candidate. The new
sender reuses the typed gap result to choose exactly the same next rays. Once
all class gaps are empty it serializes them once. The receiver still fully
decodes and recomputes geometry and strict deadlines. All actual archived inputs
are checked for byte equality with the full sender reference; changed packets
are independently rejected by receiver geometry where coverage is lost.
