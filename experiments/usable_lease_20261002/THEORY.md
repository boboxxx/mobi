# Useful lifetime is a property of evidence AND its delivery

Keep the existing conditional sensor, opaque-core, footprint, uncertainty and
motion contracts. For required obstacle class c, observation i excludes a disk
in center space whose radius is `r_min(c) - error(i,c)`. The error includes the
ray's age and is recomputed from raw geometry. A grid cell of half diagonal q
is certified by one ray only when its center distance is strictly less than
`r_min(c) - error(i,c) - q - 1e-9`. Legitimate receiver-owned history may certify
other cells. Uncovered cells remain possible obstacles.

For proposed horizon h, U(h) is the disjoint union of the required cells across
all classes which are NOT already covered by valid history. Every candidate
ray has a subset C_i(h) of U(h) which it excludes under the same strict rule.
An admissible packet satisfies union(C_i(h) for sent i) = U(h), includes only
observed raw rays, respects the wire cap and passes the unchanged full receiver.

Reverse deletion starts with the existing nearest-ray support cover. It deletes
i only if every cell in C_i(h) has coverage count at least two. Therefore every
deletion retains complete coverage by induction. In the terminal set each
remaining ray is essential for at least one cell. This is inclusion minimality,
not globally optimal bytes, and it is restricted to the initial candidate set.
It need not preserve the packet's frontier BEYOND h; this distinction is checked
and logged separately, rather than extending expiry without new geometry.

Greedy cover picks the largest number of currently uncovered cells, with
deterministic original-ray-index ties. The native implementation keeps stale
heap entries as upper bounds: before selecting a top entry it recomputes that
ray's gain. If unchanged, no other current gain can exceed it; stale tied entries
are processed in index order. Thus it retains the established greedy choices
on the same strict graph. This is an implementation equivalence argument, not
a new approximation bound. The Python baseline used an inclusive graph search;
native graph construction applies the original receiver's strict comparison.
Actual packets and boundary issues must be checked, not assumed equivalent.

For a selected packet S with SENT horizon H, meaningful delivered lifetime is

    R = H - acquisition - sender_computation - receiver_computation - transport(S).

Any action and finite backup require an additional T and full containment of
the realized action envelope. The integer deadline check is `ceil(arrival_us)
+ T_us < reference_us + H_us`; a packet does not become younger after loss,
queueing or selecting it late. The study models transport as 20ms + bytes*8/R_bps.
Packet checks at stamp+20ms establish geometry only; the separately reported
remaining-time/tick test accounts for all modeled delays.

Maximizing H alone can lose: extra evidence may raise H less than its encoding,
verification or wire costs. Conversely minimizing bytes may delete evidence
that determines a larger H. The grid oracle scores a single chosen candidate;
a procedure which tries four candidates must charge all attempted computation.
The study reports both and never interprets an unpaid oracle as deployment.

These costs are observations on controlled archived inputs, not upper bounds.
Only an actual receiver's arrival-time and geometry checks decide admission.
Neither this cover heuristic nor C++ compilation solves sensor calibration,
continuous-time physical safety, actuator effectiveness or self-occlusion
recovery after history expires. Those remain separate project requirements.
