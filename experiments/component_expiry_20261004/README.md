# Separate component expiry development

Read `research/component_expiry_result_20261004.md` and `PROTOCOL.md`.
This is finite post-test development on all prior episodes; zero newly qualified
risk or paid-policy claims. Sources were frozen before execution and are immutable.

```sh
python experiments/prospective_shape_20261004/prepare_archive.py --restore
python experiments/prospective_hypotheses_20261004/prepare_archive.py --restore
c++ -std=c++17 -O3 -shared -fPIC experiments/body_expiry_20261004/proposer.cpp -o experiments/body_expiry_20261004/proposer.so
OPENBLAS_NUM_THREADS=1 python experiments/component_expiry_20261004/audit.py --out /tmp/component-audit.json
python experiments/component_expiry_20261004/test_method.py
python experiments/component_expiry_20261004/verify_package.py
```

No CARLA is needed for reconstruction. The output writer refuses to overwrite
published results. Known class/body/inventory and motion remain parent assumptions.
