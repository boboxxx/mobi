# Action-query source-expiry interface

`query_kernel.py` compiles frozen geometry and answers arbitrary disk queries without
renewing its source timestamp. Exact supported-set contradiction checks and verified
fallback feasibility witnesses precede conditional proposals. `decision` reports
geometric eligibility separately from deployment authorization: this new query and
control law is not covered by the historical fixed-query policy certificate.

Read PROTOCOL.md for the finite replay and limits. This is a required interface for
ego integration; it is not yet an ego controller or an independent safety certificate.
The previous models/calibration stay unchanged and no recurring research job exists.

From the repository root, build the native source geometry if needed, then run:

```sh
c++ -std=c++17 -O3 -shared -fPIC experiments/body_expiry_20261004/proposer.cpp -o experiments/body_expiry_20261004/proposer.so
OPENBLAS_NUM_THREADS=1 python -m unittest discover -s experiments/action_expiry_20261004 -p 'test_*.py'
```

Before replay, restore the published parent JSON with
`experiments/prospective_component_20261004/restore_results.py`. The replay fixture
is prior held-out data used for deterministic implementation checks, not new
calibration or evaluation. Published original qualification claims are not enlarged.
