# Finite development probe: retained negative result

The [report](../../research/balanced_expiry_result_20261004.md) describes a
candidate that improves motorcycle expiry gaps and worsens all other classes.
It is not a validated global replacement. Previously read data are development
only; original scientific sources, models and results remain unchanged.

`370c6b4ce6ef818b5844650eb458771e83680f00` published the candidate and independent
audit before execution on sheng. `freeze.json` pins sources and prior inputs.
`PROTOCOL.md` describes the two units and one episode score event. `READING.md`
records established statistical methods and rejected alternatives.

From repository root, with Python, NumPy, SciPy and a C++17 compiler:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
c++ -std=c++17 -O3 -shared -fPIC experiments/body_expiry_20261004/proposer.cpp -o experiments/body_expiry_20261004/proposer.so
python experiments/prospective_shape_20261004/prepare_archive.py --restore
python experiments/prospective_hypotheses_20261004/prepare_archive.py --restore
python experiments/balanced_expiry_20261004/audit.py --out /tmp/balanced-geometry-audit.json
python experiments/balanced_expiry_20261004/check_conditional.py --out /tmp/balanced-conditional-check.json
python experiments/balanced_expiry_20261004/verify_package.py
```

The native library is host-specific; its frozen source is portable. Geometry
and conditional checks reproduce saved artifacts without CARLA or a new fit.
Frozen predictor replay is shared, while rational scores, sets, age bounds and
old policy selected-episode counts are independently reconstructed. Raw input
verification is inherited from the pinned, already cross-audited parent batch.
`develop.py` is the single original sheng producer and refuses to overwrite its
output. Optional `report.py` requires matplotlib.

The conditional diagnostic concerns the OLD measured policies. It does not
invent measured costs for the new candidate. Its unit is one complete episode
conditional on any authorization; it is not a per-query or collision guarantee.
No cell reaches the 5% target. New independent score/policy/test stages are
required before deployment claims.
