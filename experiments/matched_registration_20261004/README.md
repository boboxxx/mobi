# Shared lightweight registration and actual matched source/receiver costs

Read PROTOCOL.md first. This finite sheng study reuses the closed parent batch
and keeps its geometry, score, registry, source epochs and trust assumptions.
No fresh risk qualification or dynamic-query result follows. Full-background
setup is unnecessary for a hull-only receiver; compare both wire methods using
the same shared lightweight registration before attributing costs to geometry.

The initialized service holds the pinned source code and yaw table. Actual setup
decode hashes these installed files; the setup contains identities/catalog/
registry and parameters, without the map voxels or repeated grid. This is a
matched isolation comparison, not a claim of globally minimal initialization.

From the repo root, first restore the parent's lossless analysis representation:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python experiments/prospective_shape_20261004/prepare_archive.py
# Build pinned runtime only if missing; audit itself does not load native code.
c++ -std=c++17 -O3 -shared -fPIC experiments/body_expiry_20261004/proposer.cpp -o experiments/body_expiry_20261004/proposer.so
python -m unittest discover -s experiments/matched_registration_20261004 -p 'test_*.py' -v
python experiments/matched_registration_20261004/audit.py --results results/matched_registration_20261004 --out /tmp/mobi-matched-audit.json
cmp /tmp/mobi-matched-audit.json results/matched_registration_20261004/audit_sheng.json
```

Do not rerun timed production into the archived output directory; retiming is
a different measurement. All three complete source/receiver jobs are actually
measured; trace maxima are not WCET. Background/XYZ work remains at the source.
Source deadlines are never reset by receiving. Empty/refusal semantics and
all failed planned episodes are retained. No simulator or automation runs.
