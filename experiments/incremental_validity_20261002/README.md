# Incremental uncertainty-checked horizon support

Finite sheng studies preserve the existing raw-ray uncertainty, history, full
receiver and strict expiry contracts. The question is whether repairing ONLY
new required-cell gaps can retain usable delivered evidence time, with matched
strong full-cover fallback and full computation/verification/link costs.

- `PROTOCOL.md`: original two-stage frozen protocol.
- `SHARED_PROTOCOL.md`: additional common projection control frozen after the
  original selected study; applied to all methods and their common fallback.
- `patch.py`: error-bin-checked nearest gap support and established greedy on
  the gap universe, preserving base current rays.
- `projection_once.py`, `baseline_shared.py`, `patch_shared.py`,
  `fallback_shared.py`: equivalent class-independent geometric projection,
  with original class motion/error-bin operation order. Full receiver unchanged.
- `bench.py`, `bench_shared.py`: original accepted-history paired replay,
  complete measured receiver work, modeled byte costs and strict action timing.
- `test_patch.py`, `test_shared.py`: eight distinct tests, including unobserved
  holes, uncertainty-invalid nearest rays, expired history, geometry corruption,
  heterogeneous origins/ages, independent output arrays and byte equality.
- `analyze.py`: independent raw-source/history/full-receiver replay, saved
  first-repeat frontier checks, all-row time arithmetic and shared byte matches.
- `THEORY.md`: conditional lifetime, cover-union argument and limits.
- `package.py`: hashes actual loaded modules and all preserved result files.
- `plot.py`: renders the finite timing/count comparison from archived rows.

Stage 1 uses the six old states in `profile_source.SELECT`, three horizons
(400/450/475ms), three repeats, randomized method order: **162 calls**. They
are post-analysis-selected states, not an independent test set. Stage 2 uses
ALL **384 inputs** from ten October 2 runs at 475ms, once for three methods with
rotated order: **1152 calls**. The two stages use DIFFERENT capture directories.
Each method receives the same actual old accepted history and proposal template;
the experimental outputs do not update the teacher history. All four studies
are retrospective and observed timing, not new driving or WCET guarantees.

From repository root, Python 3.8+, NumPy/SciPy and g++ (use fresh output dirs):

```bash
mkdir -p build/incremental_validity_20261002
g++ -std=c++11 -O3 -shared -fPIC experiments/usable_lease_20261002/cover.cpp -o build/incremental_validity_20261002/cover.so
export MOBI_COVER_LIBRARY="$PWD/build/incremental_validity_20261002/cover.so"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH="$PWD/experiments/incremental_validity_20261002:$PWD/experiments/online_evidence_20261002:$PWD/experiments/usable_lease_20261002"
python -m unittest test_patch test_shared -v
python experiments/incremental_validity_20261002/bench.py --mode selected --capture results/live_repair_closed_loop_20261001/capture --out /tmp/mobi-incremental-selected
python experiments/incremental_validity_20261002/bench.py --mode all --capture results/online_evidence_20261002/live --out /tmp/mobi-incremental-all
python experiments/incremental_validity_20261002/bench_shared.py --mode selected --capture results/live_repair_closed_loop_20261001/capture --out /tmp/mobi-incremental-selected-shared
python experiments/incremental_validity_20261002/bench_shared.py --mode all --capture results/online_evidence_20261002/live --out /tmp/mobi-incremental-all-shared
python experiments/incremental_validity_20261002/analyze.py --results results/incremental_validity_20261002 --selected-capture results/live_repair_closed_loop_20261001/capture --capture results/online_evidence_20261002/live --out /tmp/mobi-incremental-audit.json
(cd results/incremental_validity_20261002 && sha256sum -c SHA256SUMS)
```

The reproduction calls above illustrate fresh benchmark outputs. The analyzer
example intentionally targets the archived authoritative study with its build
records; a new study must likewise preserve its build records and group its
four outputs under the expected stage names. Timing will vary by hardware/load.
Common immutable grids may be warm; frontier diagnostics are outside timed
generation. Startup compilation and library load are separately recorded.
Receiver replay independently checks only archived first-repeat bytes; other
repeat rows receive arithmetic checks rather than new packet claims.

The original five-test log, additional eight-test log, both builds, missing
temporary-library failure and wrong selected-capture startup failure are
preserved. The latter produced no measured rows/packets. The first packaging
script and its relative-path failure are also archived; resolving its source
directory fixes only the manifest operation. Both builds use the
same frozen C++ source and yield identical binary hashes on sheng. No CARLA
process or recurring research loop is launched by this package. sheng's plotting
environment lacks `six`; that rendering failure is preserved and the same plot
code renders the archived sheng measurements locally. No shared Python
environment is changed to fix a figure. Independent local replay produces a
byte-identical audit JSON; `local_verification.json` records its command,
source hashes and the local eight-test pass. See the
[research result](../../research/incremental_validity_result_20261002.md) for
the measured comparison and unresolved claims.
