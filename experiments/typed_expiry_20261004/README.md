# Typed fallback expiry development

Results: `research/typed_expiry_result_20261004.md`. This is development on
previously examined data, not a fresh qualification. Frozen source/inference
is immutable. The failure is retained, including all decreased fallback queries.

From the repository root, restore the two parent logical datasets with:

```sh
python experiments/prospective_shape_20261004/prepare_archive.py --restore
python experiments/prospective_hypotheses_20261004/prepare_archive.py --restore
c++ -std=c++17 -O3 -shared -fPIC experiments/body_expiry_20261004/proposer.cpp -o experiments/body_expiry_20261004/proposer.so
OPENBLAS_NUM_THREADS=1 python experiments/typed_expiry_20261004/audit.py --out /tmp/typed-audit.json
python experiments/typed_expiry_20261004/verify_package.py
```

The result writer intentionally refuses to overwrite the published output.
No CARLA server is needed for reconstruction. Runtime inference accepts observed
hulls, known extent, frozen prediction and frozen thresholds; truth enters only
the offline score/audit. The motion/body/inventory assumptions remain those of
the parent fixture and do not certify arbitrary traffic scenes.
