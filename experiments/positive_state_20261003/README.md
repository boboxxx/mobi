# Finite positive-observation state-set experiment

Sheng ran one frozen 594-episode CARLA0.9.15 schedule (39 calibration +60 test
per each of six classes), with two sequential static views. No recurring loop.
42 failed spawns remain; 552 episodes yield 1104 scans. Every fourth original
return is archived: 24,367,488 stored of 97,467,744 sensor-reported returns.
The XYZ estimator never reads semantic tags or actor IDs. Calibration/evaluation
labels are retained for audit. Own actors were removed, synchronous mode reset,
and owned server PID75592 stopped; receipts are in results.

Read PROTOCOL.md (frozen before capture), THEORY.md (conditional guarantee and
limits), TIMING_AUDIT.md (preserved timing repair) and the
[Chinese report](../../research/positive_state_result_20261003.md).
Authoritative final results are summary_sheng.json and expiry_sheng.json under
results/positive_state_20261003; initial analysis and failures remain intact.

## Reproduce without launching CARLA

From the repository root, Python3.8+, NumPy, SciPy (sheng used1.24.4/1.10.1):

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m unittest discover -s experiments/positive_state_20261003 -p 'test_*.py' -v
python experiments/positive_state_20261003/verify_package.py
python experiments/positive_state_20261003/audit.py --results results/positive_state_20261003 --out /tmp/positive-audit.json
python experiments/positive_state_20261003/diagnose.py --results results/positive_state_20261003 --out /tmp/positive-diagnosis.json
python experiments/positive_state_20261003/summarize.py --results results/positive_state_20261003 --out /tmp/positive-summary.json
python experiments/positive_state_20261003/check_expiry.py --results results/positive_state_20261003 --out /tmp/positive-expiry.json
```

Compare the four deterministic outputs against their *_sheng.json counterparts.
The audit independently reconstructs grid components with scipy.ndimage.label,
checks all stored XYZ, 1104 packets, quantiles/coverage, and 6624 analytic ages.
Ten targeted tests passed on each host. Initial beta.ppf results differed by
2.78e-17 across SciPy versions; the first failed audit log is preserved. The
independent auditor now inverts the binomial CDF at 80-digit precision and
rounds its reported bound to15 digits; labels/coverage/geometry were unchanged.

To remeasure, evaluate.py --results results/positive_state_20261003 --label NEW
writes new messages/analysis; use a NEW label and never overwrite sheng artifacts.
timed_replay.py --results ... --out /tmp/new-timing.json repeats full processing
against the published messages and bounds. Timing varies with hardware/load and
is not expected to match bytewise. Plot with plot.py and Matplotlib. Package
freezing is a publication operation, not part of routine verification.

capture.py/start_carla.ps1/stop_carla.ps1 preserve the finite collection procedure.
Do not silently restart it or call a reused plan independent fresh evidence.
The capture freeze hashes establish the exact preregistered detector/protocol/
plan sources. No post-test threshold tuning was performed. The 545 old pose
candidates are a regression set only, not fresh test coverage or a SOTA baseline.

## Meaning of the outcome

17/360 scheduled tests exclude the true center in at least one view; 29 refuse.
705/1440 scheduled test query outcomes have positive modeled remainder; median
211.871ms among positives, median full processing2.543ms and available packet152B.
The positive range starts at11us, which is not robust to unmodeled latency.
Forty positives belong to excluded episodes. Zero posthoc true-center reachability
violations at either interval endpoint concern the same abstract motion model,
not actual collision experiments. Queries within an episode are correlated.
The <=1us gap is only the solver's precision inside the declared center-union/
body-disc model; it does not establish optimal full-raw or physical expiry.
Whole-family availability is offline, from both completed static views. No
causal live schedule, full inventory, physical sensor/motion validation, dynamic
closed loop or MobiCom novelty is established by this batch.
