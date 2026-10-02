# Same-observation position-set baseline and precision diagnostic

The frozen main study has 72 measured calls: 6 histories × 2 targets ×
2 methods × 3 randomized-order repeats on sheng. Both methods have the same
available raw observations and the same previously paid sender FIFO pipeline.
Fixed-K suppresses invalid chains; observation bundles can carry those same
available raw records after a temporal gap. Their transmitted information is
therefore not identical when fixed-K refuses. All assembly, decompression,
full receiver reconstruction/frontier and actual byte-dependent modeled link
cost is charged; original-prefix registration is separately measured.

Fixed-K and the coarse established position-set observer each prove 6/12
target geometries. Their timely modeled calls are respectively 1/36 and0/36.
A post-baseline, once-per-target factor2 internal grid diagnostic restores
10/12 target geometries using unchanged source/physical contracts, but0/12
are timely. Four strict-gap failures were representation losses, not evidence
of fundamental non-identifiability. This does not establish an optimal
continuous-state expiry or a novel MobiCom algorithm.

See `PROTOCOL.md`, `REFINEMENT_PROTOCOL.md`, `THEORY.md`, `READING.md` and the
[Chinese result](../../research/set_observer_result_20261002.md).
`observer.py` propagates unknown centers, injects unknown boundary arrivals,
then removes only whole tiles excluded by actual raw-ray balls.
`refined.py` changes internal tile width, not sensor/obstacle metadata.

The two independent analyzers do not import the observer/native mask/EDT:
they rebuild raw-source individual-ball masks and vertex-distance reachability
with KD trees. The coarse audit revalidates all252 old prefix packets and
120 selected source records, checks240 class transitions/36 masks/18 saved
packets/72 costs and18 horizon boundaries. Fine audit rebuilds another240
transitions/36 masks/12 packets/12 costs and22 horizon boundaries, using the
separately fully audited roots. Eight distinct unit tests pass on both hosts.
An additional exact comparison checks12 byte-identical coarse/fine transport
pairs and24 fine possible masks contained in their lifted coarse counterparts.

## Reproduce from repository root

Use Python with NumPy/SciPy and the previous cover/raster builds. Rebuild native
kernels locally; Linux `.so` bytes differ from macOS `.dylib`, while independent
audits of the archived sheng data require no native libraries.

```bash
mkdir -p build/incremental_validity_20261002 build/streaming_recovery_20261002 build/set_observer_20261002
g++ -O3 -std=c++17 -ffp-contract=off -shared -fPIC experiments/usable_lease_20261002/cover.cpp -o build/incremental_validity_20261002/cover.so
g++ -O3 -std=c++17 -ffp-contract=off -shared -fPIC experiments/streaming_recovery_20261002/raster.cpp -o build/streaming_recovery_20261002/raster.so
g++ -O3 -std=c++17 -ffp-contract=off -shared -fPIC experiments/set_observer_20261002/mask.cpp -o build/set_observer_20261002/mask.so
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export MOBI_COVER_LIBRARY="$PWD/build/incremental_validity_20261002/cover.so"
export MOBI_RASTER_LIBRARY="$PWD/build/streaming_recovery_20261002/raster.so"
export MOBI_MASK_LIBRARY="$PWD/build/set_observer_20261002/mask.so"
python -m unittest discover -s experiments/set_observer_20261002 -v
python experiments/set_observer_20261002/bench.py --capture results/online_evidence_20261002/live --source results/streaming_recovery_20261002 --out /tmp/mobi-new-set-study
python experiments/set_observer_20261002/refine_study.py --capture results/online_evidence_20261002/live --source results/streaming_recovery_20261002 --baseline /tmp/mobi-new-set-study/analysis.json --out /tmp/mobi-new-fine-study
```

Fresh studies use new output directories and need their corresponding kernel
build metadata for sealing/auditing; the following commands reproduce archived
audits without altering measurements:

```bash
python experiments/set_observer_20261002/analyze.py --results results/set_observer_20261002 --capture results/online_evidence_20261002/live --source results/streaming_recovery_20261002 --out /tmp/mobi-set-audit.json
python experiments/set_observer_20261002/analyze_refined.py --results results/set_observer_20261002 --capture results/online_evidence_20261002/live --source results/streaming_recovery_20261002 --out /tmp/mobi-fine-audit.json
python experiments/set_observer_20261002/geometry_diagnostic.py --source results/streaming_recovery_20261002 --out /tmp/mobi-source-geometry.json
python experiments/set_observer_20261002/compare_representation.py --results results/set_observer_20261002 --out /tmp/mobi-representation-comparison.json
python experiments/set_observer_20261002/package.py --results results/set_observer_20261002
```

`geometry_diagnostic.py` only checks exact quantized geometry/relative ages in
all120 archived sources. Repeated geometry motivates a possible exact cache or
dictionary; it does not measure a new optimization or verify changing scenes.
Source authenticity, persistent-object and common-clock conditions remain
upstream promises. This is fixed-region timestamped replay with a modeled link,
not a new synchronous CARLA driving run, real wireless or WCET. No recurring
research loop was created.

The first post-measurement packaging helper used a relative source directory
with an absolute repository root and failed before sealing. Its original code
and failure log are preserved in `packaging_failure`; resolving the helper's
directory fixes only packaging and changes no measured algorithm/data.
