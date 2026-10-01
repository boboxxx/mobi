# Free-region leases and conditional control handoff

Finite sheng work for the question: how can incomplete observations provide
credible evidence validity without unnecessary conservatism?

**Result:** unchanged current-ray proofs can be exposed as verified free regions
with fixed expiry, then checked against a complete maneuver from the current
state. On 1,044 saved-data cases, same-time conditional admissions increase from
2 to 19, including five hypothetical 0.5 m/s cases. Twelve separate actual CARLA
continuous-control episodes make progress but all violate the supplied 3 m/s²
traction bound. These results do not authorize physical movement or establish
evidence-guided driving, a calibrated contract, or research novelty.

- [Chinese result and interpretation](../../research/lease_handoff_result_20261001.md)
- [Conditional definitions, sufficient proof and external obligations](THEORY.md)
- `lease.py`: verified rounded free regions, current-state command/backup tube,
  containment, monotone packet acceptance, finite handoff and watchdog interface.
- `CONTROL_PROTOCOL.md`, `capture_control.py`: fixed 12-run continuous controller
  comparison, world-snapshot-bound measurements and owned actor cleanup.
- `REPLAY_PROTOCOL.md`, `run_replay.py`: 1,044-case hybrid timing and 43,587 paired
  age-grid checks, retaining all failed geometry cases.
- `analyze_control.py`, `validate.py`: raw control continuity, command readback,
  source/protocol hashes, current raw-ray provenance, independent full geometry,
  deadline and containment recomputation.

The Reader must receive trusted profiles, measurement bounds and coordinate/
episode scope from the application. Reading those values from a received packet
alone does not establish them. The replay uses previously pinned/hash-validated
fixtures; production use needs independently justified configuration.

## Reproduce from repository root

Python 3.8+, NumPy, SciPy; Matplotlib only for plotting. A fresh output directory
is mandatory for replay; the production output should not be overwritten.

```bash
python -m unittest discover -s experiments/lease_handoff_20261001
python experiments/lease_handoff_20261001/run_replay.py --previous results/policy_runtime_20261001/binary --out /tmp/lease-replay-new
python experiments/lease_handoff_20261001/analyze_control.py --results results/lease_handoff_20261001
python experiments/lease_handoff_20261001/validate.py --results results/lease_handoff_20261001 --previous results/policy_runtime_20261001/binary --capture results/visibility_certificate_20261001/carla120
python experiments/lease_handoff_20261001/plot_results.py --results results/lease_handoff_20261001
```

Production sheng workdir: `/home/sheng/mobicom2027_visibility_20261001`.
Python: `/home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python`.
The executed replay used `results/policy_runtime_binary`; the repository groups
that identical input as `results/policy_runtime_20261001/binary`. New outputs use
`results/lease_handoff_20261001` on both machines. The 12 actual captures were
initially written to `results/handoff_control` and then archived under `control`.

To collect new actual diagnostics, start an exclusive CARLA 0.9.15 server on
Town10HD_Opt and run `capture_control.py --host HOST --out NEW_DIR` from sheng.
The script restores world settings and destroys its actors; server ownership
and stop are separately recorded. No continuing research automation was created.

`replay/manifest.json` pins the source files that existed at replay execution;
later auditing/plotting files are additional files, not alterations of the
measured implementation. `dependencies.json` and `SHA256SUMS` pin final code,
required input hashes and archived results. Timing is machine dependent and is
not expected to reproduce bit for bit; decision validation reuses measured ages.
