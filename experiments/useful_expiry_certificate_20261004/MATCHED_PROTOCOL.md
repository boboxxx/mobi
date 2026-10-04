# Fixed all-held-out same-input representation diagnostic

This supplement is frozen before policy certification and before held-out test
capture. It evaluates all available raw sources and cached driving queries in
all72 planned held-out episodes. Incomplete cases and missing cache counts remain
explicit. Each source is encoded using function, deadline and compact cone with
the identical XYZ, odometry, body, fixed model, registry and source epoch. The
actual method packet must reproduce byte for byte. Source geometry and query
bounds are independently checked; no assertion assumes the approximate function
bound always exceeds a valid transported cone bound.

Report every source wire size and query age, aggregate signed function-minus-cone
age, both directions of differences, equality counts and static-domain misses.
No timing/selector/action is counterfactually rewritten. This is an offline
representation diagnostic, not a fresh driving comparison, alternative runtime
certificate, proof of minimum conservatism or radio benchmark. No samples are
chosen by result and no deployment thresholds change. Raw capture can be supplied
from a separately verified lossless restore tree. No extra physical episodes.
