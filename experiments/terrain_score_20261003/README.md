# Terrain-clipped evidence score: finite repair and continuous inversion

Executed on sheng on2026-10-03. [Chinese result](../../research/terrain_score_result_20261003.md).
This separate follow-up preserves the previous score, calibration and inversion.
The fixed15cm clip removes near-road-height support from hypothetical boxes while
retaining observed ground rays as evidence of the above-ground free segment.
The score is recalibrated jointly across the prescribed views/budgets.

- [Frozen score protocol](PROTOCOL.md)
- [Finite inversion/budget follow-up](PROTOCOL_INVERSION.md)
- [Derivation, statistical and physical limits](THEORY.md)

From the repository root with NumPy/SciPy, run separate Python processes:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m unittest discover -s experiments/terrain_score_20261003 -v
python experiments/terrain_score_20261003/run.py --out /tmp/terrain-analysis.json --timings /tmp/terrain-timings.json
python experiments/terrain_score_20261003/audit.py --analysis /tmp/terrain-analysis.json --out /tmp/terrain-audit.json
python experiments/terrain_score_20261003/invert.py --analysis results/terrain_score_20261003/analysis_sheng.json --out /tmp/terrain-inversion-new --max-nodes 2000
python experiments/terrain_score_20261003/audit_inversion.py --results results/terrain_score_20261003 --variant inversion --out /tmp/terrain-inversion-audit.json
python experiments/terrain_score_20261003/audit_inversion.py --results results/terrain_score_20261003 --variant inversion16000 --out /tmp/terrain-inversion16000-audit.json
```

`run.py` imports the local changed score before adding historical modules to its
search path. `invert.py` loads it by an explicit path and intentionally substitutes
it in the frozen solver. Packet calibration identities refer to the new analysis.
Calibration uses true poses; receiver inversion uses only received xyz, public
road frame and declared class. Independent world-plane auditing imports neither
tested score nor tested cell-bound code. Original raw observations, masks and
failed episode records remain in the earlier shape package.

These are old-data engineering diagnostics. A fresh calibration/test design,
validated terrain/shape/dynamic contracts, computational efficiency and positive
net closed-loop validity remain required. No recurring loop or CARLA server is
started by these commands.
