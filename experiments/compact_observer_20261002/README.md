# Finite exact transport/cache and local posterior computation

The frozen108-call study gives the same available raw inputs and previously
paid source FIFO pipeline to three methods, targets25/39, all six histories,
three randomized-order repeats. All new encoding/decoding/key/miss/rebuild/
frontier work and actual byte-dependent modeled transport is paid. Roots are
fully revalidated; setup of all three receivers is separately measured.

Each method gets lossless temporal dictionary transport and exact geometry
reuse, starting with an empty cache at EACH target. The original checksum,
physical/time/sequence checks remain required for every reconstructed raw step.
Both positional methods additionally use the same conservative computation
windows and established native squared distance transform. Everything outside
the window remains unknown and is injected at every transition; original
physical wire metadata stays unchanged. The windows are9m/11.5m half-domains,
and internal small/vehicle tiles are .05/.1m or .025/.05m.

fixed-K and coarse position each support6/12 geometries, with9/36 timely modeled
calls. Fine position supports10/12 with1/36 timely. Coarse/fixed benefit more
from the common engineering optimization; the one fine timing pass is fragile
and not evidence of stable real-time deployment. These are established-method
optimizations on repeated saved geometry, not an established MobiCom novelty.

Six new distinct tests cover exact native/brute/previous-EDT agreement, changed
ray/age dictionary equivalence, malformed transport/count/IDs, unknown arrivals,
geometry cache invalidation and full uncached changed-input reconstruction.
The independent audit imports no compact implementation/native/EDT and rebuilds
all local-domain states from the complete verified prefixes and original rays.
It checks252 prefixes,120 source steps,480 class transitions,72 masks,30 packets,
108 cost rows and40 horizon boundaries. Exact comparison additionally checks
30 reconstructed original packet bytes,72 conservative local crop relations
and24 unchanged positional target horizons.
Frozen predecessor source/data/audits are preserved.

See `PROTOCOL.md`, `THEORY.md` and the
[Chinese report](../../research/compact_observer_result_20261002.md).

## Reproduce from repository root

Build the existing cover/raster/mask dependencies as described in
`../set_observer_20261002/README.md`, then:

```bash
mkdir -p build/compact_observer_20261002
g++ -O3 -std=c++17 -ffp-contract=off -shared -fPIC experiments/compact_observer_20261002/propagate.cpp -o build/compact_observer_20261002/propagate.so
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export MOBI_COVER_LIBRARY="$PWD/build/incremental_validity_20261002/cover.so"
export MOBI_RASTER_LIBRARY="$PWD/build/streaming_recovery_20261002/raster.so"
export MOBI_MASK_LIBRARY="$PWD/build/set_observer_20261002/mask.so"
export MOBI_PROPAGATE_LIBRARY="$PWD/build/compact_observer_20261002/propagate.so"
python -m unittest discover -s experiments/compact_observer_20261002 -v
python experiments/compact_observer_20261002/bench.py --capture results/online_evidence_20261002/live --source results/streaming_recovery_20261002 --baseline results/set_observer_20261002 --out /tmp/mobi-new-compact-study
python experiments/compact_observer_20261002/analyze.py --results results/compact_observer_20261002 --capture results/online_evidence_20261002/live --source results/streaming_recovery_20261002 --baseline results/set_observer_20261002 --out /tmp/mobi-compact-audit.json
python experiments/compact_observer_20261002/compare.py --results results/compact_observer_20261002 --baseline results/set_observer_20261002 --out /tmp/mobi-compact-equivalence.json
python experiments/compact_observer_20261002/package.py --results results/compact_observer_20261002
```

New study outputs need their corresponding build record before sealing/audit.
The auditor reproduces the archived full layout with no native library.
This is timestamped fixed-region replay under persistent-object/common-clock
and uncalibrated physical/source conditions, not wall-clock CARLA, moving
control, real wireless, WCET or certified physical safety. No continuing
research loop or new CARLA server was created.
