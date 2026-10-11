# Restore and independently reconstruct the finite experiments

Run from the repository root. Python 3.8+ and NumPy are required. CARLA is needed only for a new prospective capture, not the following immutable replay. All CPU measurements used for replay come from sheng logs; replay does not replace them with local timings.

For each unit (`actuator_admission_20261011`, `nominal_route_20261011`, or `actuator_route_40s_20261011`), use a **new** output folder and output JSON filenames:

```sh
python experiments/actuator_admission_audit_20261011/restore.py \
  --archives results/UNIT/raw_archives --out /tmp/NEW_RESTORE
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python experiments/UNIT/analyze.py \
  --capture /tmp/NEW_RESTORE/capture --out /tmp/NEW_ANALYSIS.json
python experiments/closed_loop_audit_20261011/compare.py \
  --sheng results/UNIT/analysis_sheng.json --local /tmp/NEW_ANALYSIS.json \
  --out /tmp/NEW_COMPARE.json
```

Replace UNIT and NEW paths literally. Restoration verifies all archive and individual file SHA256 values, including episode logical payload hashes later verified by the frozen analyzer. Capture sources and prerequisite inputs are validated against each original freeze. The analyzers reconstruct source/control CPU and radio FIFOs, epoch/episode/context admission, physical control, geometry/sample envelopes, collision events, and complete/interrupted braking for both evidence units. Nominal replay reconstructs the physical controller and task endpoint; it makes no evidence claim.

```sh
python experiments/actuator_admission_audit_20261011/verify.py \
  --manifest results/actuator_admission_20261011/publication_manifest.json \
  --out /tmp/NEW_PUBLICATION_CHECK.json
```

The explicit publication verifier also checks every archived raw file, all three freezes and prerequisite hashes, both-host discrete agreement, cleanup, and owned PID/path/start-time stop records. Floating audits use absolute 1e-9 / relative 1e-10 tolerance; original platform-specific values are retained.

Each archive is below 95 MiB. There are no omitted raw observations, synthetic successful episodes, failed-outcome retries, or duplicate uncompressed raw directories in Git. Published reports identify conditional physical and sensor assumptions. No data here establish real-radio latency, native actuator WCET/watchdog, continuous physical bounds, or an independent deployment-risk certificate. The 40s task is a separate development specification, not a replacement for the failed 30s task.
