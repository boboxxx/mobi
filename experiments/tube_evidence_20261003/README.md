# Bounded current returns and conditional evidence validity

Finite sheng replay, 2026-10-03. [Derivation and scope](THEORY.md),
[frozen runtime protocol](PROTOCOL.md), [literature constraints](../../research/tube_evidence_reading_20261003.md).

The sender reads all current returns, represents in-ball coordinates by endpoint
balls around a paid reference, and sends out-of-ball coordinates exactly. The
receiver's count bounds hold across every represented endpoint, not merely its
old coordinate. Existing leaf proofs are rechecked; invalid exclusions are revoked.
Counts computed by subtracting/replacing exceptions must equal a full check of
the identical mixed message. Unknown points contribute unknown counts, not zeros.

The saved-data matrix has six actor classes, two queries, three radii and three
synthetic perturbation levels: 36 old-only proof builds and108 warm cases, each
with three timing repeats. The reference is test00 and current observation test10,
20.5 simulated seconds apart; these are independent saved cases, not a continuous
trajectory. Each query/radius is accounted as a separate task. No oracle radius
selection, simultaneous scheduling claim, new CARLA capture or research loop.

Dependencies: Python3.8+, NumPy, SciPy; GCC/Clang C++17 with unsigned `__int128`;
Matplotlib for plots (set `MPLCONFIGDIR` to a writable directory if needed). Tested on sheng WSL and local macOS. No GPU used. MSVC is not
supported. Run from the repository root and retain the previous data packages.

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
c++ -O3 -std=c++17 -ffp-contract=off -shared -fPIC experiments/tube_evidence_20261003/kernel.cpp -o /tmp/mobi_tube_kernel.so
MOBI_TUBE_LIBRARY=/tmp/mobi_tube_kernel.so python -m unittest discover -s experiments/tube_evidence_20261003 -v
python experiments/tube_evidence_20261003/run.py --out /tmp/tube-replay-new --budget 64000
python experiments/tube_evidence_20261003/audit.py --results results/tube_evidence_20261003/replay --out /tmp/tube-audit.json
python experiments/tube_evidence_20261003/costs.py --results results/tube_evidence_20261003/replay --out /tmp/tube-costs.json
python experiments/tube_evidence_20261003/witnesses.py --results results/tube_evidence_20261003/replay --out /tmp/tube-witnesses.json
python experiments/tube_evidence_20261003/summarize.py --results results/tube_evidence_20261003 --out /tmp/tube-summary.json
python experiments/tube_evidence_20261003/plot.py --summary results/tube_evidence_20261003/summary_sheng.json --out /tmp/tube-tradeoffs
```

Timestamp/frame compatibility is checked against the fixed reference. The repeated
benchmark calls are independent replay measurements; this module is not a deployed
stream session or receive-clock/action gate. A live caller must use the preserved
source time, charge actual age and reject expired evidence, including duplicates.

The new runtime output directory must not exist. `summarize.py` uses the saved
sheng audit and cold coding costs so that the cost table reproduces the same
measurements on either host. Its output is deterministic; runtime measurements
need not reproduce bitwise across machines or runs.

## Verification and diagnostic scope

`audit.py` uses a separate world-halfspace C++ intersection routine and independent
pose enclosure code. It checks every computed cold count, complete tree coverage,
70-digit Decimal contact times, every warm exclusion, current packet provenance,
actual in-ball endpoint membership and domination of raw current counts. Its
SciPy cone prefilter is broader than the tested implementation and has deterministic
full-cloud crosschecks. This is not an unconditional full-cloud scan of every cell.
`same_partition_tightness` compares each bounded-message lower horizon with a
full-current-data recheck under the exact same inherited revalidation rule: only
old excluded leaves can be re-excluded; old unresolved leaves stay possible. It
does not evaluate all old unresolved leaves with raw data, nor measure the
uncertainty already paid in the cold tree or total error relative to optimal
scene inference.

Five tests cover1840 random pose/endpoint combinations, clipping, empty eroded
inner boxes and codec/reference/time failures. All100 endpoint-only fixtures
have strictly positive bounds, preventing a vacuous all-zero comparison.
Numerical guards are engineering checks, not formal directed rounding.

`witnesses.py` is a separate post-replay search; its [protocol](WITNESS_PROTOCOL.md)
was written after inspecting runtime aggregates. It does not alter timed results.
Search failures remain recorded. The upper bounds refer to the abstract body-disc
model and accepted raw-score set, not physical mesh collisions.

Sensor error, unknown object inventory, moving sensor transforms, real dropout,
terrain/motion contracts and repeated-time risk require further validation. The
receiver's missing coordinates and the sensor's unknown physical error are distinct.
The synthetic Gaussian inputs do not establish a calibrated physical noise model.
The sender's membership assertion is not remotely authenticated by a checksum.

After both host audits and the deterministic local cost summary are available,
`python experiments/tube_evidence_20261003/verify_package.py` checks the recorded
pairs and freezes source/result manifests. It requires a Git checkout to record
the base commit. The checked publication contains three byte-identical host pairs;
all five tests pass on each host.
