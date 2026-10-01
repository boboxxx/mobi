# Actual-ego integration: preserve rejected initialization and renewal

Three finite four-run batches were executed on sheng. Only three runs reached
actual ego creation, with 120 driving-phase decisions and 1,813 recorded physics
ticks. No forward command was admitted. This is an integration failure and
rejection audit, not successful evidence-guided driving. See the
[Chinese report](../../research/evidence_loop_result_20261001.md).

- `PROTOCOL.md`: pre-ego raw-ray initialization, 20 warm / 40 driving decisions,
  fixed contracts, one-tick control, measured-delay synchronous co-simulation.
- `capture.py`: initial implementation; selected raw rays exceeded wire capacity
  in view 0, while view 1 lacked geometry. All roots rejected.
- `INTEGRATION_FIX.md`, `capture_v2.py`: existing compression/current-ray renewal
  and correctly ordered receiver check time; late proofs still fail.
- `FAST_PATH_FOLLOWUP.md`, `capture_v3.py`, `fast_path.py`: exact nominal proposal,
  one complete receiver verification, stricter initial remaining-time check.
- `control.py`: a finite tick driver, with per-tick actual-control/body checks.
  It is not an independent wall-clock actuator watchdog.
- `analyze.py`: regenerates every encoded packet from archived XYZ; checks all
  executed ticks, and compares optimized receiver/proposals with full references.
- `diagnose_shadow.py`, `diagnose_transition.py`: distinguish missing observations
  from a failing support proposal when valid receiver history exists.
- `lazy_compress.py`, `profile_compression.py`: byte-identical lazy greedy and
  paired timing; its speedup is insufficient for this 400 ms lifetime.
- `repair_renew.py`, `profile_repair.py`: post-analysis proposal repair for an
  identified transition, followed by complete geometric verification. Fresh
  closed-loop validation of this repair remains outstanding.

The output package is `results/evidence_loop_integration_20261001`, with
`initial/`, `compressed/`, `fast/` preserving all three batches, plus audit,
shadow/transition diagnostics and post-analysis profiles. The initial empty
scene is sensed BEFORE creating the registered ego, and no external obstacle
is subsequently spawned. This controlled initialization is not a method for
assuming a real road is initially clear. The physical sensing/shape contracts
remain conditional; the previous iid actuation calibration cannot be reused
as a risk guarantee for these adaptive states.

## Reproduce from archived data

Use Python 3.8+, NumPy 1.24 and SciPy 1.10 (the sheng capture environment). From
repository root:

```bash
python -m unittest discover -s experiments/evidence_loop_20261001
python experiments/evidence_loop_20261001/analyze.py --first results/evidence_loop_integration_20261001/initial --corrected results/evidence_loop_integration_20261001/compressed --fast results/evidence_loop_integration_20261001/fast --out /tmp/evidence-loop-analysis.json
python experiments/evidence_loop_20261001/diagnose_transition.py --capture results/evidence_loop_integration_20261001/fast --out /tmp/evidence-loop-transition
python experiments/evidence_loop_20261001/profile_repair.py --capture results/evidence_loop_integration_20261001/fast --out /tmp/evidence-loop-repair
(cd results/evidence_loop_integration_20261001 && sha256sum -c SHA256SUMS)
```

Fresh capture requires an exclusive CARLA 0.9.15 Town10HD_Opt server and a new
output directory. `start_carla.ps1` refuses an existing server and enforces a
30-minute lifetime. The actual server for the archived three batches was PID
58232 and is confirmed stopped. No background research loop was created.

The link is modeled as 20 ms, not measured wireless transport or a byte-sensitive
channel model. Logging is instrumentation; timing includes acquisition,
generation and verification as stated in the protocol, not an end-to-end WCET.
Drop flags during unsuccessful driving phases do not constitute a demonstrated
moving-vehicle fallback: no usable driving packet existed to drop. Unit tests
exercise the nonempty one-tick commitment separately; do not mix those scopes.
