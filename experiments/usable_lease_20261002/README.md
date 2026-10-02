# Useful-lifetime selection: finite negative and implementation-cost audit

Two frozen 288-call matched archived-input studies on sheng. The first keeps
nearest support, original greedy, original repair/fallback and reverse deletion.
The second gives BOTH greedy and deletion an equivalent C++ selection kernel
and vectorized graph; original greedy/repair remain measured controls. No
sensor, motion, expiry or receiver guard is relaxed. No new CARLA runs are
claimed by this package.

- `PROTOCOL.md`, `NATIVE_PROTOCOL.md`: pre-execution scopes and timing accounting.
- `thin.py`: strict coverage-preserving inclusion-minimal cover, not global optimum.
- `cover.cpp`, `native_pack.py`: checked CSR, exact lazy greedy and reverse deletion.
- `bench.py`, `bench_native.py`: unchanged archived receiver history, raw provenance,
  four sent horizons, three randomized method-order repetitions per case.
- `analyze.py`: independent original-input replay and full-frontier comparison;
  unpaid candidate oracle versus charged all-candidate menu diagnostic.
- `THEORY.md`: correctness argument, useful-time objective and contribution limits.
- `package.py`: source/result hashes and verified provenance archive.

The compiled library is deployment preparation; compile/load costs are recorded
separately. Immutable common grids are warmed by the full-input frontier check.
All per-message generation includes source quantization, projections, graph,
selection, serialization and a full sender geometry check; the receiver check
is separately charged. Observed timing is not WCET. Acquisition comes from the
unchanged archived input, and transport is modeled, not measured wireless.

From repository root (Python 3.8+, NumPy/SciPy, g++), separate outputs:

```bash
g++ -std=c++11 -O3 -shared -fPIC experiments/usable_lease_20261002/cover.cpp -o /tmp/mobi-cover.so
export MOBI_COVER_LIBRARY=/tmp/mobi-cover.so OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m unittest discover -s experiments/usable_lease_20261002
python experiments/usable_lease_20261002/bench.py --capture results/live_repair_closed_loop_20261001/capture --out /tmp/mobi-usable-matched
python experiments/usable_lease_20261002/bench_native.py --capture results/live_repair_closed_loop_20261001/capture --out /tmp/mobi-usable-native
python experiments/usable_lease_20261002/analyze.py --results results/usable_lease_20261002 --capture results/live_repair_closed_loop_20261001/capture --out /tmp/mobi-usable-audit.json
(cd results/usable_lease_20261002 && sha256sum -c SHA256SUMS)
```

Eight distinct tests, including 100 random discrete-cover equivalence cases.
All 112 saved packets pass independent full geometry/provenance/frontier checks;
64 second-stage packets match their first-stage references byte for byte. All
576 modeled action tests and all paid-menu action tests fail. Faster compilation
does not turn this heuristic into a successful validity-selection or driving
algorithm. The report preserves the failed first audit import and its correction.
Old server directories contain AppleDouble `._*.py` files that incidentally
matched the original benchmark's dependency glob. Original manifests are kept;
their bytes are preserved in `archived_metadata`, classified separately from
executable source, and verified during independent replay on other machines.
