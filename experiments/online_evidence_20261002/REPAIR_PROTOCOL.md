# Finite paired coverage-reuse validation, frozen before timings

Use the same six post-analysis cases selected in PROTOCOL.md. Reconstruct actual
receiver history and prior validity from the archived run. Evaluate both the
original repair generalized only to the requested horizon and the coverage-reuse
repair at 400, 450 and 475 ms; three alternating-order paired repeats each.
Cold fallback is unchanged full compression, invoked equally when renewal fails.
The generalized 400 ms reference must match the original archived algorithm
byte-for-byte; optimized output must match the generalized reference byte-for-byte
at every horizon, including None. All nonempty outputs independently undergo the
unchanged complete body.verify and every selected ray must come from that saved
XYZ input. Record bytes, timing and full geometry; do not claim independent
scenarios or a deployment time bound. Both methods use one-thread libraries.
