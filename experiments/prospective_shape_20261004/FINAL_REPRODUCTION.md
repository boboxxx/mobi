# Reproduce the closed fresh study without changing archived measurements

Run from the repository root with Python, NumPy and SciPy. The native proposer
is not needed for independent archived-data audits. Runtime/unit tests import
the pinned body kernel; if its local library is absent, build it first:

```sh
c++ -std=c++17 -O3 -shared -fPIC experiments/body_expiry_20261004/proposer.cpp -o experiments/body_expiry_20261004/proposer.so
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python experiments/prospective_shape_20261004/prepare_archive.py
python -m unittest discover -s experiments/prospective_shape_20261004 -p 'test_*.py' -v
python -m unittest discover -s experiments/pose_support_20261004 -p 'test_*.py' -v
python experiments/prospective_shape_20261004/audit_portable_v2.py --results results/prospective_shape_20261004 --out /tmp/mobi-fresh-shape-audit.json
cmp /tmp/mobi-fresh-shape-audit.json results/prospective_shape_20261004/audit_v2_sheng.json
python experiments/prospective_shape_20261004/audit_lease_baseline.py --results results/prospective_shape_20261004 --out /tmp/mobi-fresh-lease-audit.json
cmp /tmp/mobi-fresh-lease-audit.json results/prospective_shape_20261004/lease_audit_sheng.json
python experiments/prospective_shape_20261004/compare_results.py --results results/prospective_shape_20261004 --out /tmp/mobi-fresh-comparison.json
cmp /tmp/mobi-fresh-comparison.json results/prospective_shape_20261004/comparison_sheng.json
python experiments/prospective_shape_20261004/failure_diagnostic.py --results results/prospective_shape_20261004 --out /tmp/mobi-fresh-failures.json
cmp /tmp/mobi-fresh-failures.json results/prospective_shape_20261004/diagnostic_sheng.json
python experiments/prospective_shape_20261004/summarize.py --results results/prospective_shape_20261004 --out /tmp/mobi-fresh-summary.json
python experiments/prospective_shape_20261004/normalize_summary.py --input /tmp/mobi-fresh-summary.json --out /tmp/mobi-fresh-summary-normalized.json
cmp /tmp/mobi-fresh-summary-normalized.json results/prospective_shape_20261004/summary_normalized_sheng.json
python experiments/prospective_shape_20261004/verify_package.py
```

The published raw `analysis_sheng.json` is 106136234 bytes. Its lossless
`analysis_sheng.json.gz` is restored and SHA256 checked by `prepare_archive.py`;
the materialized JSON is deliberately Git-ignored to satisfy GitHub's per-file
limit. The artifact manifest covers the archived representation, all other
original capture/packet/results and post-run evidence. Source/analysis hashes
continue to identify the exact uncompressed original producer output.

Original model, primary and lease freezes remain immutable. Read
`AUDIT_REPAIR.md` for the independently recorded NumPy/SciPy portability fixes.
Five deterministic cross-host pairs are v2 geometry/calibration/wire/FIFO audit,
lease audit, exact paired comparison, failure diagnostic and normalized
presentation summary. The two raw summaries are preserved even though their
descriptive confidence bounds differ by a last bit. The v2 audit must retain
all original sheng geometry, membership, packet, fee, trace and physical counters.

Do not rerun capture or paid producers into the closed directory. Archived
processing timings are actual sheng measurements; retiming is a new experiment.
The original runner and both finite resume/audit histories remain inspectable.
The recorded CARLA process was owned, stopped and scene-cleaned. No automation
or scheduled research loop is part of this package. This finite package does
not establish full research completion, unknown-inventory coverage, a continuous
physical/ego guarantee, actual wireless performance or a MobiCom contribution.
