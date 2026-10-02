# Class-specific evidence guards: finite sheng experiment

This package tests retaining different class facts while joint action authority
expires at the shortest horizon. It keeps the strong original fixed/fine
baselines and gives the same augmented rays to a fine set observer. It records
all5400 measured-service, modeled-queue rows, original/augmented roots,120
augmented packets,600 distinct wire packets and14 distinct state arrays.
Read the [Chinese result](../../research/class_guard_result_20261002.md),
[theory](THEORY.md), [frozen protocol](PROTOCOL.md), [root FIFO correction](FIFO_CORRECTION.md),
[fixed-candidate upper-bound protocol](WITNESS_PROTOCOL.md) and [primary reading](READING.md).

The authoritative timing file is
`results/class_guard_20261002/fifo_corrected.json`.
`study/analysis.json` is the unchanged CPU measurement and original-model record.
It erroneously initialized source/link queues without root occupancy; the
deterministic correction changes402 slow-link rows and no standard/blackout
rows. Do not report its initial slow-link counts as final results.

## Reproduce on sheng

Run from repository root with Python3.8+, NumPy, SciPy and Matplotlib. The
recorded host uses `/home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python`.
Four previously built native libraries are reused; exact source/binary hashes
are in `build_dependencies.json`. To build on a new Linux checkout:

```sh
mkdir -p build/class_guard_20261002
c++ -O3 -std=c++17 -shared -fPIC experiments/usable_lease_20261002/cover.cpp -o build/class_guard_20261002/cover.so
c++ -O3 -std=c++17 -shared -fPIC experiments/streaming_recovery_20261002/raster.cpp -o build/class_guard_20261002/raster.so
c++ -O3 -std=c++17 -shared -fPIC experiments/set_observer_20261002/mask.cpp -o build/class_guard_20261002/mask.so
c++ -O3 -std=c++17 -shared -fPIC experiments/compact_observer_20261002/propagate.cpp -o build/class_guard_20261002/propagate.so
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export MOBI_COVER_LIBRARY="$PWD/build/class_guard_20261002/cover.so"
export MOBI_RASTER_LIBRARY="$PWD/build/class_guard_20261002/raster.so"
export MOBI_MASK_LIBRARY="$PWD/build/class_guard_20261002/mask.so"
export MOBI_PROPAGATE_LIBRARY="$PWD/build/class_guard_20261002/propagate.so"
python -m unittest discover -s experiments/class_guard_20261002 -p 'test_*.py' -v
```

To reproduce the experiment, choose a fresh output directory; do not overwrite
the published measurement record. Both original and augmented conditions pay
captured source generation, new selection, encoding, serialized wire service
and measured receiver checking. Warm41-packet history cost is reported apart.

```sh
mkdir -p results/class_guard_replication
python experiments/class_guard_20261002/bench.py --out results/class_guard_replication/study
python experiments/class_guard_20261002/replay_fifo.py --results results/class_guard_replication
python experiments/class_guard_20261002/analyze.py --results results/class_guard_replication --corrected --out results/class_guard_replication/audit.json
```

The parent output directory must already exist. Geometry is reproducible;
measured CPU durations depend on hardware/load, so timing rows are not expected
to match a new run byte for byte. Frozen inputs also depend on earlier published
online_evidence, streaming_recovery and recursive_validity packages.

For independent verification of the published run, no native library is loaded:

```sh
python experiments/class_guard_20261002/analyze.py --results results/class_guard_20261002 --corrected --out /tmp/class_guard_audit.json
python experiments/class_guard_20261002/witness_check.py --results results/class_guard_20261002 --out /tmp/class_guard_witness.json
```

The second command rechecks all84 already-published candidate trajectories
against the augmented received information; it does not search for new ones.
Both outputs are byte-identical between sheng and the local host. The timing
sidecar from the witness checker is intentionally host-dependent.

`summarize.py` creates the corrected descriptive tables and exportable figures;
`package.py` freezes inherited/current sources and every result. Eleven distinct
tests cover actual accepted roots, expiry/replay/missing-template checks,
superset observations and initial FIFO occupancy. Initial registration failure,
the first path-setup error and the superseded queue-model audit are retained.

This is not new CARLA driving or real radio execution. Core/shape/error/motion/
aligned-time bounds are stipulated, the task body is stationary, the geometry
is repeatedly saved, and the source selection is nonminimal. No MobiCom
firstness, universal safety or near-optimal lifetime is established by this run.
