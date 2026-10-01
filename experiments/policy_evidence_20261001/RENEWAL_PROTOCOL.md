# Fixed finite current-ray renewal follow-up

After 180 cold checks yielded 13 conditional policy geometry proofs but zero
compute-budget passes, test current-ray renewal using each layout/density's
free-frame-00 template. Never treat an old template as current free-space proof.
No prior, no bootstrap, no obstacle-label access inside the algorithm.

Use all existing 120 static frames except each free-frame-00 template frame:
116 frames × speeds (0, 0.5, 1) × horizons (0.2, 0.3, 0.4) = 1,044 pairs.
Missing templates are recorded as refusals. Compare full bounded projection
before support lookup against nominal projection before lookup, followed by
identical receiver reconstruction of bounds for selected current raw rays.
Alternate execution order per trial. Record byte equivalence, both times,
measured historical acquisition latency and hypothetical 20 ms link delay.
Check 120 ms hold budget and complete stopping before integer expiry.
Retain both negative and positive outcomes, and save successful fresh packets.

This saved-scan computation comparison uses hypothetical ego speeds and supplied
contracts already contradicted by some actuator diagnostics. Timely conditional
packets do not authorize physical motion or establish a safe ego-driving result.
Temporal reference stamps are assigned for replay, not new sensor timestamps.
