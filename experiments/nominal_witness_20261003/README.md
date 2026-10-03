# Receiver-only feasible witnesses and raw-data diagnosis

This finite sheng study follows `proof_repair_20261003`. It fills the missing
upper-witness path without changing a score, threshold, message, lower proof or
motion assumption. Read [PROTOCOL.md](PROTOCOL.md), the explicitly post-search
[TRANSFER_PROTOCOL.md](TRANSFER_PROTOCOL.md), [THEORY.md](THEORY.md), and the
[Chinese findings](../../research/nominal_witness_result_20261003.md).

## Results

All36 tasks have independently verified accepted poses and tighter upper bounds.
The search stores294912 evaluated poses and549 successive-best witnesses. A finite
same-class pool contains545 distinct proposals; transfer tightens24 upper bounds
further. The closest Tesla(+6,0) raw-compatible witness gives35.083ms in all three
perturbation conditions. Seven raw-data tasks cannot cover the fixed240ms reserve
under the frozen model even if all remaining costs were zero. Eighteen closest
nominal witnesses fail actual-raw rescoring, showing specific removable message
ambiguities. Neither fact establishes physical collisions or full compression loss.

Pooled lower/upper gaps remain32.075–430.799ms; none meets10ms. The lower endpoints
are the prior4096-visit proofs, all of whose modeled online remainders were zero.
No new online success or independent risk-validation claim is made.

## Reproduce

From repository root, using Python3.8+, NumPy, SciPy1.10.1 and a C++17 compiler:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
c++ -O3 -std=c++17 -ffp-contract=off -shared -fPIC experiments/nominal_witness_20261003/scorer.cpp -o /tmp/mobi_nominal_scorer.so
export MOBI_NOMINAL_LIBRARY=/tmp/mobi_nominal_scorer.so
python -m unittest discover -s experiments/nominal_witness_20261003 -p 'test_*.py' -v

# New directory only; do not overwrite the published measurements.
python experiments/nominal_witness_20261003/run.py --out /tmp/mobi-nominal-search-new

# Independently verify the published sheng outputs.
python experiments/nominal_witness_20261003/audit.py --results results/nominal_witness_20261003/search --out /tmp/mobi-nominal-audit.json
python experiments/nominal_witness_20261003/transfer.py --results results/nominal_witness_20261003 --out /tmp/mobi-nominal-transfer.json
python experiments/nominal_witness_20261003/summarize.py --results results/nominal_witness_20261003 --out /tmp/mobi-nominal-summary.json
MPLCONFIGDIR=/tmp/mobi-nominal-mpl python experiments/nominal_witness_20261003/plot.py --summary /tmp/mobi-nominal-summary.json --out /tmp/mobi-nominal-figures
python experiments/nominal_witness_20261003/verify_package.py
```

Repository dependencies are the committed tube-evidence, proof-repair,
pose-inversion and terrain-score artifacts. No CARLA service, GPU or new capture
is used. Measured search times include per-task decoding, initialization, ray
indexing and optimization, but exclude compilation and offline output/audits.
Their summed25.980s is a sum of measured search intervals, not end-to-end live
latency. Seeded optimizer output can vary across SciPy/platform versions; the
cross-host equality claim concerns audits of the same saved sheng outputs.

## Independent checks and audit correction

Three tests pass on each host. The initial audit checks all549 successive-best
poses plus32 spread evaluations per task:1696 distinct all-ray pose checks,
45,817,440 ray checks. Transfer checks every pooled pose on both nominal and raw
clouds:6540 pose checks,176,678,100 ray checks. Initial audit, transfer and summary
JSON match bytewise across hosts. Unselected optimizer evaluations are retained
but not all independently rescored; they support no exclusion claim.

The first audit version incorrectly required the first evaluated population to
equal the supplied initial population bit-for-bit. SciPy rescales through unit
coordinates, producing observed differences up to1.3323e-15 in the first task.
Only this initializer comparison was changed to absolute tolerance1e-14 with
zero relative tolerance. Actual evaluated poses are checked strictly against
the prior, and all selected witness counts/contact bounds remain independently
verified. The search data and producer code were not rerun or modified.

`verify_package.py` verifies immutable hashes by default; `--freeze` is only for
publication maintenance. No recurring automation or research loop is created.
