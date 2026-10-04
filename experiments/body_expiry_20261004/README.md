# Body-support expiry development package

This is a finite sheng experiment on the unchanged prospective corpus. It fits no new thresholds and establishes no fresh risk qualification. See [PROTOCOL.md](PROTOCOL.md) for the frozen scope and [THEORY.md](THEORY.md) for the conditional proof and conservatism boundary. Strong exact-hull transport is a primary baseline, not raw-cloud-only compression.

On sheng, repository root `/home/sheng/mobicom2027_visibility_20261001`:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
TASK_PY=/home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python
c++ -std=c++17 -O3 -shared -fPIC experiments/body_expiry_20261004/proposer.cpp -o experiments/body_expiry_20261004/proposer.so
"$TASK_PY" -m unittest discover -s experiments/body_expiry_20261004 -p 'test_*.py' -v
# Fresh output directory; never overwrite archived measured timings.
"$TASK_PY" experiments/body_expiry_20261004/evaluate.py --results $PWD/results/body_expiry_reproduction
"$TASK_PY" experiments/body_expiry_20261004/audit.py --results $PWD/results/body_expiry_reproduction --out $PWD/results/body_expiry_reproduction/audit_sheng.json
"$TASK_PY" experiments/body_expiry_20261004/summarize.py --results $PWD/results/body_expiry_reproduction --out $PWD/results/body_expiry_reproduction/summary_sheng.json
```

The producer records repository-relative new packet paths; reproduction output must be a fresh directory **inside the repository**. Rerunning timed production need not give identical timings or grants; replay and independent audit of the archived measurements should agree deterministically. Read native compiler/binary receipt before treating a rebuilt proposal library as the recorded sheng library.

Raw wires are immutable files in `results/prospective_expiry_20261003/messages`. They are actually reencoded byte-identically and then decoded by the NEW body-support frontend, rather than duplicated into this package. New actual active/hull/point messages and the charged common setup are archived here. Dependency hashes close over those raw wires and source NPZ files.

The first attempt failed immediately on relative output paths before any complete frame result. `evaluate_at_first_run.py`, `freeze_at_first_run.json` and `results/body_expiry_20261004/at_first_run/` retain the exact original source, freeze, partial setup/message and logs. The only repair before the second freeze resolves output paths to the repository root. No model parameter, score, query, method or threshold changes.
