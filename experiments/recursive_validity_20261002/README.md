# Recursive conditional evidence validity

Read `THEORY.md` for the proof and `PROTOCOL.md` for frozen scope. This finite
study separately maintains timestamped facts and finite action authority. It
compares strong fixed-region and position-set methods with identical two-end
past-travel improvements, typed original rays and paid computation/link queues.
No prior measured file is edited. No continuous research automation is created.

Requires Python3.8+, NumPy/SciPy and the existing four native libraries. Set
OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1. The environment variables
MOBI_COVER_LIBRARY, MOBI_RASTER_LIBRARY, MOBI_MASK_LIBRARY,
MOBI_PROPAGATE_LIBRARY point to the prior compiled libraries (build provenance
and binary SHA in the results package).

```sh
python -m unittest discover -s experiments/recursive_validity_20261002 -p test_flow.py -v
python experiments/recursive_validity_20261002/bench.py --capture results/online_evidence_20261002/live --source results/streaming_recovery_20261002 --baseline results/compact_observer_20261002 --out results/recursive_validity_20261002/study
python experiments/recursive_validity_20261002/analyze.py --capture results/online_evidence_20261002/live --source results/streaming_recovery_20261002 --baseline results/compact_observer_20261002 --results results/recursive_validity_20261002 --out /tmp/recursive-audit.json
python experiments/recursive_validity_20261002/package.py --results results/recursive_validity_20261002
```

The bench output must not exist before a fresh invocation. Independent audit
requires the committed measured outputs, frozen input studies and build.json.
Identical saved geometry can enable exact caches; moving-scene speedups, real
wireless, physical calibration and a novel final MobiCom contribution are not
established by this experiment.

The post-analysis finite transport extension is frozen separately in
`DICTIONARY_PROTOCOL.md`. Run `test_dictionary.py`, `dictionary_bench.py` with
the same inputs and `--out results/recursive_validity_20261002/dictionary_study`,
then `dictionary_analyze.py` with the same audit arguments. It reconstructs
references solely from actually received verified templates, and charges
expansion/reencoding. Periodic full refreshes use no free ACK; lost templates
fail closed. Both studies must exist before the final package.py invocation.
