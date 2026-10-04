# Cross-version float reconstruction supplement

The frozen strict auditor passed on source Python3.8. Its local Python3.12 run
stopped at exact equality of the recomputed scalar relay brake. All102 nonidentical
relay reconstructions differ by at most4.163336342344337e-17; preserve the initial
failure log and every mismatch in float_replay_diagnostic.json.

Python's official math.hypot documentation records improved accuracy in3.10:
https://docs.python.org/3/library/math.html#math.hypot
This change is consistent with the measured last-bit difference; no claim that
it changes source physics or risk follows. The separate audit_portable.py differs
from frozen audit.py in exactly one assertion: requested scalar throttle/brake
reconstruction accepts absolute1e-15 error. Actual CARLA float32 control matching
still uses its existing1e-6 check. All geometry, integer ages, packet bytes, gates,
domain selection, source epochs, input hashes and physical diagnostics are intact.

Freeze this separate auditor, explanation and the mismatch evidence before using
it. Compare its local and sheng results with the original strict sheng output.
Do not rewrite the source controller, historical logs, requested commands or
statistical thresholds. A portable pass does not hide the initial strict failure.
