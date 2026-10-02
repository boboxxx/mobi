# Finite center-exclusion continuity/recovery study

Preliminary diagnosis used c0/view0/reuse warm0/drive18/drive25 raw clouds:
all current rays cover the exterior reachability collar at 475ms once the
class-specific center-exclusion invariant is supplied. This is exploratory
information only; no valid new chain or timing gain has yet been measured.

Question: can a receiver recover a fixed free-region fact after its old action
authority expires, by verifying buffered historical raw observations that
continuously prevent external obstacle centers from entering the region?
Do not assume unobserved vehicle interior free, ignore a temporal gap, relabel
an expired legacy packet as fresh, or infer useful driving from a time check.

Derive class-specific K_c = fixed rectangle dilated by pose margin + r_max,c
ONLY from a complete accepted legacy certificate, including its receiver-owned
valid history. That certificate excludes all centers in K_c over its proved
interval. At each later observation, K_c is known center-free only if its
reference is strictly before the current proved endpoint. Exclude every tile
outside K_c that could reach it before the new endpoint using current raw rays,
their original errors/ages, motion/clock bounds and finite-domain guard.
Conservative tile classification uses center distance + tile radius < K_c's
radius; straddling tiles require actual rays. Continuity prevents entry into K_c
and extends the factual endpoint. Objects cannot teleport or appear inside K_c:
the same persistent continuous obstacle-trajectory model underlying renewal.

New typed wire/receiver path: center-continuity-v1. Legacy Receiver and strict
expiry checks stay frozen. A registered anchor is a verified past fact, never
unrestricted current action authority. All buffered steps are fully decoded
and reverified at their OWN historical references. Receipt/execution must still
precede the FINAL new endpoint. Maximum 32 steps, 8192 rays per raw step and
2.1 MB entire wire bundle; batch size/aggregate rays/bytes/cost are reported.
This is a larger message protocol than one-step proof, NOT equal-size work.

Tests first: invisible-interior positive with real initial rays; temporal gap,
missing collar, unregistered anchor, source schema/clock/profile mismatches,
corruption, replay/late arrival and fixed-region-only limits. Compare the
logical sufficient condition against a small independent interval reachable-set
observer; continuity/history itself is established theory, not a novelty claim.

Archived study: ALL six initialized October 2 runs, recovery drive25 (first
after five dropped attempts) and drive39 (longer lapse): 12 explicitly targeted
cases. Anchor = original receiver's last accepted proof before drive20. Buffer
includes the actual captured scans after that anchor through the target.
No imaginary extra scans; actual reference intervals must be respected.

Four methods, three rotated/randomized repeats (seed20261004), 144 bundle calls:
current-only compiled full cover with expired prior removed; nearest fixed475
continuity; compiled greedy fixed475 continuity; compiled greedy with historical
steps shortened just through the next already-observed reference, final475.
The shortened-step schedule knows only already buffered past references and is
charged for every generation, failed attempt, serialization and full verification.
Same source contracts, compiled kernel and one numerical-library thread.
No free observed frontier oracle or precomputed sender work.

Charge capture acquisition from target, complete on-demand bundle generation,
complete receiver verification and 20ms + all bytes*8/20Mbps. Tick-round total
age upward at 50ms, reserve200ms, require strict final expiry. Analyze rootless,
wrong/missing step, dropped raw scan and late/replay refusals. Archive every
first-repeat bundle and all negative rows. Independently check provenance of
each saved step, registered anchor, intervals and collar geometry. Scope is
original-history retrospective recovery, not new closed loop, physical safety,
real wireless, distribution-independent reliability or MobiCom originality.
