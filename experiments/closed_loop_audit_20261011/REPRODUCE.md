# Reproduce the frozen physical batch audit

The physical development batch was preregistered in commit `56892e43dead348cbb095b0ebbf21f1ab7a9451b`. A terminal storage failure was retained, and only the four never-attempted requests were run after separately preregistering storage recovery in `5ad2473e89e3b77aada1d1507dad127e2529e687`. No failed attempted episode was rerun. This directory contains post-result audit/packaging and an exact computation optimization; it does not replace the frozen controller.

From the repository root, using Python with NumPy:

```bash
python experiments/closed_loop_audit_20261011/verify_package.py --out /tmp/closed_loop_package_check.json
python experiments/closed_loop_audit_20261011/restore.py --archives results/closed_loop_motion_20261011/raw_archives --out /tmp/closed_loop_restore_fresh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/closed_loop_motion_20261011/analyze.py --capture /tmp/closed_loop_restore_fresh/combined --out /tmp/closed_loop_analysis_fresh.json
python experiments/closed_loop_audit_20261011/compare.py --sheng results/closed_loop_motion_20261011/analysis_sheng.json --local /tmp/closed_loop_analysis_fresh.json --out /tmp/closed_loop_compare_fresh.json
python experiments/closed_loop_audit_20261011/timing_diagnostic.py --capture /tmp/closed_loop_restore_fresh/combined --out /tmp/closed_loop_timing_fresh.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/closed_loop_audit_20261011/benchmark.py --capture /tmp/closed_loop_restore_fresh/combined --out /tmp/closed_loop_benchmark_fresh.json
```

Use fresh output paths; tools deliberately refuse overwrites. Mathematical runtime tests: `python -m unittest discover -s experiments/closed_loop_motion_20261011 -p test_runtime.py`. Full capture needs the original dependent source files, frozen context, CARLA 0.9.15 API and matching Windows server. Restoring/auditing this publication does not start CARLA. Source and capture/processing clocks and modeled radio costs must not be presented as an actual wall-clock realtime or wireless certificate.

`restore.py` verifies archive hashes, validates each archived path and every original file's hash/length, and reconstructs combined hardlinks from captured outcome records. It preserves the original zero-byte `capture/episodes/closed_07.json.gz` and partial raw files. The combined storage-failure descriptor has no physical trajectory; excluding that unknown outcome from a zero-collision assertion is mandatory. Published averages and speedups in `benchmark_sheng.json` are post-result replay timings, not a changed rollout or WCET.

Publication verifier receipts themselves are excluded from the self-referential manifest. The original controller and recovery freezes remain unchanged. The publication is development evidence, including route failure, not an independent risk certification set.
