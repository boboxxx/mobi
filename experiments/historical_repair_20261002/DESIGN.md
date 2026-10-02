# Implementation contract

This extends the published frozen class_guard code. `backward.py` currently
implements the first geometry primitive. Do not import it as `geometry`: that
name is owned by a legacy module in the dependency graph.

For each class, compute required current475ms tiles. Remove tiles wholly inside
the eroded owned old free region and tiles excluded by current received rays.
Let M be the remaining whole tiles. Every previous center capable of entering M
lies in M (+) ball(D), with D the already available two-endpoint past bound.
Enumerate predecessor grid cells through minimum distances between grid-cell
vertices (SciPy EDT for generation, independent KD/brute check for audit).
Reject if M can be reached from outside the finite historical domain. Remove
whole old tiles inside the owned old region and those excluded by old received
rays. The remaining cells are the only historical ray demand. A source-selected
fragment must cover ALL these cells; it is never independently a full safety
certificate. Future travel stays one-sided. Current and old references/caps
remain distinct, avoiding treating old rays as fresh.

The planned receiver wrapper retains last positive fact/raw, bounded actually
received raw history and, for fine observers, the corresponding saved state.
A normal packet uses the existing bounded F/R transport and replay guards.
A proof failure can create one request naming immutable parent and failed
target digests. Positive owned permission is clipped to475ms for common demand
construction. Replies supply missing original source packets and optional
fragments bound to a parent/child transition. No fragment can seed a new root.

For repair, operate on a shadow of the owned parent state. Merge only received
history and supplied missing packets, in increasing reference/sequence order,
up to the actually available target. Verify each partial predecessor cover.
For scalar mode this proves the requested current475ms fact directly. For fine
mode apply the extra negative mask to its owned past positional state and replay
the received steps with native conservative propagation. All supplied fragments
and state transitions are checked before installing facts or granting actions.
Restore the global anti-replay maximum after shadow replay; never roll it back.
The live receiver clock and grant availability advance only at measured check
completion. Repairs completing after expiry retain facts but no expired action.

Requests can be smaller than cell lists: the sender already caches the matching
selected parent/current packets and can construct a proposal from the named
contract/budget. Receiver recomputation remains authoritative and charged.
Backfill-only is mandatory: recovering dropped already-selected packets is an
established explanation and must not be credited to new ray selection. For
one550ms gap with both original packets received, backfill cannot create the
missing information; a new historical fragment is necessary for this method.

The event loop must schedule actual source arrivals, source CPU jobs, two link
directions, receiver arrivals and serial checking. Queue availability starts
after the root work/transmission. Cache insertion occurs only when a source
record has completed generation; cache eviction is chronological and bounded8.
Source reply construction sees only this cache, not an unrestricted file lookup.
Full scan paths may be known to the driver but must be accessed through eligible
cache records. A request target bounds reply content even if newer data exist.
Receiver replay can include newer normal packets only if already decoded.

Record every enqueue/start/end, request/reply byte count and packet digest,
source-cache identities at request service, supplied original/extra observations,
state/authority changes, failed/stale/cancelled requests and CPU busy intervals.
Report normal admissions and repair-generated grants separately, plus the union
of actionable intervals minus receiver-unavailable intervals. Cache-hit speedups
on repeated saved geometry remain conditional; no new driving is implied.
