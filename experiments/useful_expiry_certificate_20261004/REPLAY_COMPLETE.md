# Complete offline replay after publication

This supplements the immutable core REPRODUCE.md. It performs no new CARLA run,
model fitting, timing measurement or policy selection. Use the repository root;
choose a fresh temporary output directory so checks cannot overwrite receipts.
The four inherited large JSON inputs are already published as gzip and restored
with hash verification; the two receiver-diagnosis inputs are in their own result
package. No access to the original Windows server is required for offline replay.

Observed runtimes are Python3.8.10 / NumPy1.24.4 / SciPy1.10.1 on sheng's WSL and
Python3.12 / NumPy2.4.4 / SciPy1.17.1 locally. Matplotlib is needed only to redraw a
figure. CARLA's Python API is needed only for physical capture, not these replays.
A C++17 compiler builds the portable source for the current platform; do not copy
another platform's `.so` binary.

```bash
set -eu
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
e=experiments/useful_expiry_certificate_20261004
p=results/useful_expiry_certificate_20261004
work=$(mktemp -d /tmp/mobi-useful-replay.XXXXXXXX)
python "$e/restore_inputs_complete.py" --out "$work/inputs.json"
c++ -std=c++17 -O3 -shared -fPIC experiments/body_expiry_20261004/proposer.cpp -o experiments/body_expiry_20261004/proposer.so
python "$e/restore.py" --restore "$work/raw" --out "$work/storage.json"
python "$e/audit.py" --split certification --capture "$work/raw/certification_capture" --out "$work/certification.json"
python "$e/audit.py" --split test --capture "$work/raw/test_capture" --out "$work/test.json"
python "$e/audit_certificate.py" --out "$work/exact_certificate.json"
python "$e/summarize.py" --out "$work/summary.json"
python "$e/matched.py" --capture "$work/raw/test_capture" --out "$work/matched.json"
python "$e/verify_package_complete.py" --out "$work/package.json"
cmp "$work/inputs.json" "$p/input_verification_sheng.json"
cmp "$work/storage.json" "$p/storage_verification_sheng.json"
cmp "$work/certification.json" "$p/audit_certification_sheng.json"
cmp "$work/test.json" "$p/audit_test_sheng.json"
cmp "$work/exact_certificate.json" "$p/certificate_sheng.json"
cmp "$work/summary.json" "$p/summary_sheng.json"
cmp "$work/matched.json" "$p/matched_sheng.json"
cmp "$work/package.json" "$p/verification_sheng.json"
```

The temporary raw tree needs approximately the raw-byte total stated in
storage_manifest.json, in addition to the compressed repository files. Keep it
until every check has passed. Archive scanning independently verifies every raw
member, rejects unsafe paths/nonregular entries/duplicates and checks compressed
and uncompressed SHA256. Original raw observations remain on sheng; Git stores
lossless per-episode bundles and directly inspectable small trajectory metadata.
Failures and refusals remain part of the planned denominators. A matching replay
confirms recorded computations and byte closure, not continuous-road safety,
execution IID or a superiority claim.
