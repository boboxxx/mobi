# Causal maintenance and bounded raw-proof delivery

`stream.py` preserves the corrected center-continuity-v1 fact and strict expiry.
`raster.cpp` enumerates each individual strict witness ball on the same grid,
then uses the established greedy from `usable_lease_20261002/cover.cpp`.
The sender uses all actual crossing rays as candidates; receiver independently
decodes source/error contracts and covers every required tile. A bounded zlib
envelope reconstructs the original typed JSON exactly, with a 2.1MB decompressed
cap and refusal of truncated, trailing or oversized transport.

The frozen follow-up has 360 source maintenance calls and 72 target evaluations
over the same six histories, targets25/39 and three repeats. A single FIFO worker
charges actual archived acquisition and measured generation at every observation.
Targets wait for required cached source proofs, then pay assembly/compression,
full verification, 20ms plus actual compressed bytes/20Mbps and upward50ms ticks.
They retain the 475ms final proof horizon and 200ms action budget. Observed queue
wait is zero. Eighteen of36 backfill repetitions recover geometry; just two pass
the modeled time gate. Cold same-kernel/compressed proofs recover zero. Positive
results are small and fragile; long chains remain late. No useful driving claim.

The native kernel and stream test path have 16 distinct final tests, including
ten continuity tests, strict-ball agreement with independent queries, malformed
transport, expired/gapped/replayed history and corrected frontier boundaries.
The server pre-measurement log contains14 tests; the final frontier log adds2.
Failed startup import and initial audit diagnostic interpretation are retained,
along with their original code. The latter corrects only a negative-case log
fallback, not the measured data. A failed schedule records target ID instead
of the incomplete path; auditors explicitly reconstruct and reject that gap.

From repository root, fresh study output directories:

```bash
mkdir -p build/streaming_recovery_20261002
g++ -O3 -std=c++17 -ffp-contract=off -shared -fPIC experiments/streaming_recovery_20261002/raster.cpp -o build/streaming_recovery_20261002/raster.so
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export MOBI_COVER_LIBRARY="$PWD/build/incremental_validity_20261002/cover.so"
export MOBI_RASTER_LIBRARY="$PWD/build/streaming_recovery_20261002/raster.so"
export PYTHONPATH="$PWD/experiments/streaming_recovery_20261002:$PWD/experiments/continuity_recovery_20261002"
python -m unittest discover -s experiments/streaming_recovery_20261002 -v
python experiments/streaming_recovery_20261002/bench.py --capture results/online_evidence_20261002/live --previous results/continuity_recovery_20261002/study/analysis.json --out /tmp/mobi-new-stream-study
python experiments/streaming_recovery_20261002/analyze.py --results results/streaming_recovery_20261002 --capture results/online_evidence_20261002/live --previous results/continuity_recovery_20261002/study/analysis.json --out /tmp/mobi-stream-audit.json
python experiments/streaming_recovery_20261002/frontier_study.py --results results/streaming_recovery_20261002 --capture results/online_evidence_20261002/live --out /tmp/mobi-corrected-frontier.json
```

The analyzer targets the archived complete results/build layout. New studies
need their corresponding build record. The frontier diagnostic is post-analysis:
compute maximum integer H for each saved target step under corrected age/future
and K conditions, check native full coverage at H and refusal at H+1. It does not
change the frozen timed rows or authorize an invalid/gapped historical chain.
No free frontier oracle or future next-frame reference enters maintenance.

Both kernels can keep immutable grids warm. Generation includes selecting,
serializing every source step; target receiver time includes decompression and
complete recomputation. Old-prefix initialization is separately measured. This
timestamped replay is not wall-clock synchronous CARLA, actual wireless, WCET,
moving-region control, physical calibration or a new theory of reachability.
Package hashes cover executable dependencies and preserved failures/results;
independent KD-tree audits do not import the raster/sender implementation.

One final macOS tar upload added AppleDouble metadata files on sheng. Their
magic bytes and hashes were recorded before removing only those task-generated
metadata files. Measurement/source bytes were unchanged. The packaging tool
excludes AppleDouble and the final upload disables macOS copyfile metadata;
both hosts regenerate identical canonical result/source manifests.
