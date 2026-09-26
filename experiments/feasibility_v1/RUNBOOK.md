# Reproduce the pilot on sheng

Remote project: `/home/sheng/mobicom2027_evidence_pilot_20260926`.
Reachable SSH endpoint used: `sheng@100.94.183.27` (confirmed hostname `DESKTOP-UGDDO8T`). The local `sheng` alias points to an older address that timed out; SSH config was not modified.

Python: `/home/sheng/anaconda3/envs/hst-sched/bin/python`.
Dependencies reused: NumPy, pandas, PyYAML, Shapely, Matplotlib. No package installations, network training, or modifications to existing research projects.

From the remote project directory:

```bash
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MPLBACKEND=Agg
python_exec=/home/sheng/anaconda3/envs/hst-sched/bin/python
"$python_exec" -m unittest discover -s src -p test_pilot.py -v
"$python_exec" src/run_bayes_probe.py --output results/bayes --seeds 20 --cases-per-seed 10
"$python_exec" src/run_opv2v_probe.py --output results/opv2v_self_filtered
"$python_exec" src/analyze.py --root results
```

Use a separate output directory if preserving an earlier run. Timings are machine observations and may differ on repetition, especially when enforcing short deadlines. Statistical results integrate packet-erasure outcomes exactly; they are not estimates from repeatedly sampling the same frames.

Inputs are read-only existing cache and raw YAML, as recorded by each manifest. `input_manifest.json` hashes every source NPZ and corresponding YAML. All candidate filtering and selection are GT-free; GT is used afterwards for static geometric diagnostics only.

Important outputs:

- `results/bayes/`: generated-model exact expectation comparisons.
- `results/opv2v_self_filtered/`: corrected, usable open-loop pilot results.
- `results/analysis/`: paired scene-bootstrap intervals, audits and figures.
- `results/opv2v/`: **invalid preliminary run containing self-obstacles**; retained solely for audit, not final conclusions.
- `logs/`: execution and regression-test logs.

No CARLA server binary was found in the bounded check of research directories, and the installed client could not connect to localhost:2000. This pilot therefore contains no live CARLA closed-loop run.
