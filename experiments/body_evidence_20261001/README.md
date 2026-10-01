# Full-body evidence and complete-stop integration gate

This finite sheng study replaces the old 0.5 m query disk with a rectangular body and a conservative swept occupancy envelope. It preserves negative results: **45/1,044 renewal packets are geometrically valid, but zero satisfy the complete stopping budget.** This is saved-data replay with hypothetical ego velocities, not new CARLA driving.

Read the [Chinese report](../../research/body_evidence_result_20261001.md) and [validated outputs](../../results/body_evidence_20261001/analysis.json).

## Interfaces

`body.py` implements the conditional geometric model and an explicit prior-region argument. This low-level argument is a premise, not a claim the sender is allowed to invent. `compress.py` reduces sufficient current-ray candidates with a greedy cover. `renew.py` reuses body-relative support locations but obtains every ray from the current cloud.

**Use `strict.Receiver` as the deployment-facing history interface.** It starts with no trusted free region, accepts only timely no-prior root proofs, derives history from accepted proofs, and rejects unknown prior identities or nonmonotone reference times/sequences. Its action gate checks both the geometric acceleration contract and complete-stop time. Receipt time and execution duration are rounded upward to integer microseconds using exact arithmetic on supplied floats; prior handoff also uses integer deadlines. The original `history.py` is retained as the measured baseline; it has a float-addition expiry boundary defect corrected by `strict.py`.

Current assumptions: half-length 2 m, half-width 1 m, radial pose allowance 3 cm, yaw rate ≤0.2 rad/s, stipulated absolute acceleration ≤8 m/s², traction growth ≤3 m/s², braking speed reduction between 4 and 8 m/s², 50 ms new command, 20 ms reaction. These are hypothetical contracts, not physical calibration. A stopped vehicle is not guaranteed indefinitely safe against incoming traffic. The prior proof system's first-return, opaque inner core, outer extent, error-box and clock assumptions still apply. SHA-256 does not authenticate a sensor.

## Frozen experiment stages

1. `PROTOCOL.md`, `run_probe.py`: 216 initial checks; 24 all-ray geometry successes, no packets because nearest-per-cell assignment exceeds the ray cap. Its 3 m/s² absolute bound conflicts with ≥4 m/s² braking; do not use its stop gate as evidence.
2. `BRAKING_FOLLOWUP.md`, `run_braking_probe.py`: 216 corrected checks, explicit 8 m/s² geometric bound, coverage-preserving compression; 15 geometric packets, no timely complete-stop acceptance. Three conditional positives violate their supplied bootstrap premise in the near-obstacle scene.
3. `RENEWAL_FOLLOWUP.md`, `run_renewal.py`: 1,044 no-prior current-ray renewals including missing templates; 45 geometric positives, zero complete-stop admissions. Fifteen independent hypothetical-timely root checks reject all nine unregistered priors and accept six no-prior roots.
4. `strict.py`, `test_strict.py`: exact deadline follow-up found during artifact review; tests include expired roots, 238 decimal endpoints and a reproduced history handoff at a legacy float boundary. Original timing runs remain unchanged.

The complete suite has sixteen tests. A source-backed conditional packet is NOT a safe certificate when its physical/initial premise is false. The analysis counts these violated-premise cases explicitly.

## Reproduction

Run from repository root with Python, NumPy and SciPy. Production sheng used `/home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python`. New output directories must not exist.

```bash
python -m unittest discover -s experiments/body_evidence_20261001
python experiments/body_evidence_20261001/run_probe.py --capture results/visibility_certificate_20261001/carla120 --out /tmp/body-initial
python experiments/body_evidence_20261001/run_braking_probe.py --capture results/visibility_certificate_20261001/carla120 --out /tmp/body-corrected
python experiments/body_evidence_20261001/run_renewal.py --capture results/visibility_certificate_20261001/carla120 --reference /tmp/body-corrected --out /tmp/body-renewal
python experiments/body_evidence_20261001/analyze.py --results results/body_evidence_20261001 --capture results/visibility_certificate_20261001/carla120
```

Production result folders on sheng are `results/body_probe`, `results/body_braking_probe`, and `results/body_renewal` under `/home/sheng/mobicom2027_visibility_20261001/`. Their committed counterparts are `initial/`, `corrected/`, `renewal/` under `results/body_evidence_20261001/`. `dependencies.json` anchors reused code, all 120 clouds and frame/label metadata. Run `sha256sum -c SHA256SUMS` in the committed result directory for artifact integrity.

Cold probe timing deliberately excludes acquisition to separate geometry/compression failure from an even stricter live requirement. Renewal includes recorded acquisition and measured compute, plus a modeled 20 ms link. None of these are wireless measurements. The unseeded templates prevent repeated invented bootstrapping. Reported speeds are hypothetical inputs to the body model, not measured ego trajectories.

Next integration must bind the occupied set to a specific control and backup policy, establish a legitimate root under self-occlusion, and validate actual tracking and stopping. Enlarging H or shrinking physical error bounds until a gate passes is not a valid fix.
