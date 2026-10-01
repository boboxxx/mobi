# Fresh repair integration and strict deadline audit

Eight finite matched runs on sheng: two existing views, two methods, two ordered
repetitions. Four runs create the ego. 260 raw inputs, 2,636 physics ticks and
160 driving-phase decisions are replayed, but **no forward command is issued**.
See the [Chinese report](../../research/live_repair_result_20261001.md).

- `PROTOCOL.md`: frozen eight-run protocol, same cached control for both arms.
- `capture.py`: first attempt fails before the new actor has a snapshot.
- `LIFECYCLE_FIX.md`, `capture_v2.py`: corrected lifecycle; actual archived batch.
- `CACHE_ARGUMENT.md`: separate completed evidence from pending verification.
- `analyze.py`: exact source regeneration, receiver/reference equivalence and
  every applied command with its reconstructed delayed evidence timeline.
- `deadline.py`, `audit_deadlines.py`, `DEADLINE_FIX.md`, `capture_v3.py`: later
  strict integer availability/startup correction. Unit/replay tested, **not a
  new live batch**. Do not analyze v3 using the frozen v2-only replay script.
- `package.py`: source-hash checked packaging on sheng, preserving failed input.

The bundle is `results/live_repair_closed_loop_20261001`. `capture/` is the full
v2 batch; `failed_attempt/` and its log retain the original lifecycle failure;
`frontier/` is the separately frozen post-analysis geometry diagnostic.

```bash
python -m unittest discover -s experiments/live_repair_20261001
python -m unittest discover -s experiments/evidence_loop_20261001
python -m unittest discover -s experiments/expiry_frontier_20261001
python experiments/live_repair_20261001/analyze.py --capture results/live_repair_closed_loop_20261001/capture --out /tmp/live-repair-analysis.json
python experiments/live_repair_20261001/audit_deadlines.py --capture results/live_repair_closed_loop_20261001/capture --out /tmp/live-repair-deadlines.json
(cd results/live_repair_closed_loop_20261001 && sha256sum -c SHA256SUMS)
```

Fresh capture needs exclusive CARLA 0.9.15 Town10HD_Opt and a new output directory.
The archived batch is synchronous measured-delay co-simulation with a fixed
20 ms link model, not wall-clock real-time driving or byte-sensitive wireless.
No moving-vehicle fallback was demonstrated. No adaptive-deployment statistical
coverage or validated physical contracts are claimed. Owned servers were stopped;
no recurring automation was created. Seventeen distinct tests passed on sheng.
