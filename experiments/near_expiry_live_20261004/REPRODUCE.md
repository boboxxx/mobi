# Finite near-hazard diagnostic

Read PROTOCOL.md before interpreting results. Restore the inherited logical inputs
using parent restoration helpers, and build the native body kernel on your host.
From the repository root, choose fresh output files:

```sh
c++ -std=c++17 -O3 -shared -fPIC experiments/body_expiry_20261004/proposer.cpp -o experiments/body_expiry_20261004/proposer.so
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python experiments/near_expiry_live_20261004/audit.py --capture results/near_expiry_live_20261004/capture --out /tmp/near-ego-independent-audit.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python experiments/near_expiry_live_20261004/analyze_complete.py --capture results/near_expiry_live_20261004/capture --out /tmp/near-ego-independent-analysis.json
python experiments/near_expiry_live_20261004/verify_package.py
```

Compare both fresh JSON byte sequences with the published sheng files. All original
scans, actual compact/function wire bytes, fees, decisions, control responses,
trajectories, failure records and original gzip logical hashes are retained.
The numeric scalar reconstruction tolerance was frozen before these new captures;
integer geometry, source times, packet bytes, gate choices remain exact.

Same-source historical model TTL comparison is offline and not a historical model
physical driving experiment. Model thresholds were calibrated for a previous
observation law; endogenous160-frame ego episodes have no transferred risk law.
The package validates provenance/implementation, not road safety, WCET, unseen
actor completeness or actual wireless. No recurring job is created.

IMPORT_CORRECTION.md records the preserved initial generic-module import failure.
The explicit-path correction was separately frozen before successful analysis.
The second kernel export error and its unchanged-algorithm correction are in SCALAR_CORRECTION.md.
