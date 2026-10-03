# Native expiry and current-observation proof revalidation

Finite sheng experiments,2026-10-03. [Chinese findings](../../research/expiry_runtime_result_20261003.md),
[protocol](PROTOCOL.md), [derivation and limits](THEORY.md).

`kernel.cpp` implements the fixed model in C++17 without fast-math. `runtime.py`
validates current packet identities and runs exact additive count updates. The
16k native partition matches all503,118 nodes of the previous audited Python run.
`reference.cpp` is a separate world-halfspace intersection implementation. The
independent audit uses SciPy's KD tree with a more generous cone, checks every
computed cell count, verifies tree partitions and integer ages, and supplements
cone inclusion with deterministic full-cloud scans. It does not import tested
solver/bounds code. Float margins remain engineering bounds.

Requirements: GCC or Clang with C++17 and unsigned `__int128`, Python with NumPy
and SciPy; Matplotlib for plots. Linux/WSL and macOS were tested; MSVC is not supported.
No GPU, installation, new CARLA instance or research loop is needed.

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
c++ -O3 -std=c++17 -ffp-contract=off -shared -fPIC experiments/expiry_runtime_20261003/kernel.cpp -o /tmp/mobi_expiry_runtime.so
MOBI_NATIVE_LIBRARY=/tmp/mobi_expiry_runtime.so python -m unittest discover -s experiments/expiry_runtime_20261003 -v
python experiments/expiry_runtime_20261003/run.py --out /tmp/native16000-new --budget 16000
python experiments/expiry_runtime_20261003/run.py --out /tmp/native64000-new --budget 64000
python experiments/expiry_runtime_20261003/audit.py --results results/expiry_runtime_20261003/native16000 --out /tmp/audit16000.json
python experiments/expiry_runtime_20261003/audit.py --results results/expiry_runtime_20261003/native64000 --out /tmp/audit64000.json
python experiments/expiry_runtime_20261003/check_transport.py --results results/expiry_runtime_20261003/native64000 --out /tmp/transport64000.json
python experiments/expiry_runtime_20261003/costs.py --out /tmp/packet-costs.json
python experiments/expiry_runtime_20261003/summarize.py --results results/expiry_runtime_20261003 --out /tmp/runtime-summary.json
```

New run directories must not exist. Kernel compilation time and binary/source
identity are recorded separately as deployment setup. Raw source captures remain
in earlier packages; packet/current-source hashes link them. Full proof arrays,
reference and delta wires, timings, failures and independent audits are retained.
Proof export/compression is audit logging, not part of the timed authority check;
packet decode, transform, comparison, index construction and count verification
are included in the wrapper timing. Sensor acquisition/callback and real network
latency are unmeasured. Results are conditional offline replays, not driving.

## Sensor-model caveat

The capture code uses `sensor.lidar.ray_cast_semantic`. CARLA's [sensor reference](https://carla.readthedocs.io/en/0.9.16/ref_sensors/)
describes semantic LiDAR separately from the intensity/drop-off/noise model of
ordinary LiDAR. This data cannot establish real-sensor temporal bit coherence.
Our additional bit-change diagnostic explicitly exposes this dependency; it is
not a sensor-calibration experiment or a claim that noise may be ignored.
