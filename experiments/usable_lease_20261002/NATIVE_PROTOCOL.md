# Correct the implementation-cost confound, frozen after the first negative

The first frozen 288-call run completed on sheng. Reverse deletion from all
nearest-cell candidates often costs 0.6–1.1 s and has slightly more packet bytes
than greedy. Keep that result; do not rerun or replace it.

Vectorize construction of the same strict ray-to-required-cell graph and use
an ahead-of-time compiled C++ kernel for BOTH greedy and reverse deletion.
Native greedy must retain the same largest-current-gain choice and minimum-ray
index ties as the established baseline; native deletion retains the reference
cost/coverage order. Both use the same raw-ray/error contracts and complete
Python receiver. C++ speed is an implementation result, not algorithm novelty.

Repeat the same six states/four horizons/three randomized repetitions with
four methods: established greedy, established repair/fallback, native greedy,
native deletion (288 calls). All immutable common geometry is warmed by the
separate full-input frontier diagnostic. Record that cache scope explicitly.
Compile/load the library before any evidence is timestamped; report compiler,
flags, compilation and load time and binary hash. Deployment preparation does
not appear in per-message generation; no first-process/cold WCET claim.

Native greedy/deletion packet bytes must match their Python references on all
same-input/horizon cases from the first study; if a strict boundary causes a
different choice, preserve it, explain it and independently verify geometry.
Add 100 random discrete-cover equivalence cases and malformed CSR tests.
No sensor, expiry, ray limit, parent history, or receiver check is weakened.

The menu oracle and paid-menu audit, packet provenance and full/subset frontier
checks follow PROTOCOL.md. No fresh CARLA or moving-backup claim is made.
