# Finite post-replay tightness diagnostic

Specified after seeing the fixed replay's aggregate counts, before running this
search. It changes no message, tree, runtime or action decision. It is not a
pre-registered success metric or a timed controller component.

For each of all108 saved warm cases, retain the current output's possible leaves.
For each leaf form two candidate poses: its midpoint and its midpoint with x/y
clamped toward the query. Sort each list by center-to-query squared distance,
then stable leaf index. Test the first16 of each, deduplicated by exact float bytes.
No actor pose labels seed this search. Use every actual current stride4 ray and
the nested stride16 view to compute the exact frozen terrain score. The C++
independent world-plane implementation screens candidates; any accepted witness
is independently rescored by the Python world-plane reference before use.

A pose passing both score thresholds is a compatible state for the actual current
raw data, hence for the message representing it. Its body-disc first-contact time
under the fixed radial motion model supplies a conditional upper bound on robust
validity. Keep the smaller of that and the existing unknown-boundary upper bound.
Report all unresolved gaps and failed searches; not finding a witness proves
nothing. The body-disc abstraction is not a physical collision witness. Searching
for upper witnesses is offline diagnostic work, not uncharged online inference.
