# Finite exact-runtime ablation, fixed before execution

Keep the preceding physical, sensor, obstacle, hold-time, horizon and body
contracts unchanged. They remain unvalidated physical premises. No CARLA
vehicle control or new sensor capture is performed in this runtime study.

Use the same 116 non-template saved frames, 3 speeds (0/0.5/1 m/s) and 3 horizons
(0.2/0.3/0.4 s): 1,044 cases per method, including missing-template refusals.
Four methods: reference nominal lookup/full verifier; bounded local lookup/full
verifier; full lookup/incremental cell checks; local lookup/incremental checks.
The two cached verifiers in each pipeline are logically separate at source and
receiver. No receiver free-space history is used. All required cells must be
checked using current reconstructed witnesses and errors, whether a hint works
or a full fallback query is needed. Stale, corrupt, future and expired packets
are rejected before any hints can establish coverage.

Rotate method order by trial ordinal. Each method emits the same wire schema
and is required to match the original frozen renewal bytes or refusal on every
case. Save SHA-256 of every emitted packet and exact expected-byte comparisons;
the identical packet files are already in the previous artifact and need not
be duplicated. Missing templates remain in the denominator.

Measure source generation and receiver verification. Include historical measured
acquisition latency and a hypothetical 20 ms link. Also include the elapsed
first computation of the timing predicate in an updated age; this final timing
predicate is a lightweight diagnostic, not physical authorization. Report
deadline sensitivity with an additional 1 ms bookkeeping allowance. No second
full geometry validation is hidden after the measured receiver stage. Report
source and receiver hint-hit counters, local/fallback counts and all failures.

Correctness must also hold on changed or removed witnesses, changed errors,
permuted ray indices, tied nearest neighbors and strict expiry boundaries.
The 120 saved clouds are mostly repeated stationary geometry; performance on
them alone must not be called a dynamic-driving gain. Added cold/warm perturbation
tests will distinguish repeated-data acceleration from robustness to movement.
