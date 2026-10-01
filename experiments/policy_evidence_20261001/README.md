# Policy-conditioned evidence validity

Finite sheng experiments: **30 new CARLA own-vehicle episodes, 180 paired geometry checks, 1,044 paired current-ray renewals**. Read the [Chinese report](../../research/policy_evidence_result_20261001.md).

Restricted hold/go/brake occupancy yields 13 cold geometry packets versus 9 checks passing arbitrary-acceleration geometry. Four of 36 scene/speed combinations gain 100 ms on a fixed horizon grid. Renewal yields 87 geometric packets, with all 1,044 reference/optimized outputs byte identical (including shared refusals). **Zero packets satisfy measured computation/acquisition plus the stipulated link/stop budget.** Actual actuator diagnostics also contradict supplied acceleration and stopping parameters. No evidence-guided driving or physically certified action is claimed.

## Files and contract

- `tube.py`: full rectangular body, restricted hold/go/brake policy, direction/rotation uncertainty, finite-horizon residual drift. Traction/braking and sensor contracts remain external premises.
- `policy_proof.py`: measured no-prior raw-ray geometry generator/verifier; it is not a movement authorizer.
- `strict_policy.py`: exact reference-time guard added after the cold measurement; use it for verification. `conditional_stop_gate` remains a conditional timing diagnostic.
- `renew_policy.py`: old support positions select **current** rays; receiver recomputes all bounds. `fast=False` computes all ray bounds first; `fast=True` computes selected-ray bounds after nominal lookup. This does not reuse expired free-space evidence.
- Five frozen protocol files distinguish the three actuator stages, geometry and renewal; `CALIBRATION_PROTOCOL.md` is an attempted diagnostic, not successful calibration.
- `analyze_actuation.py` verifies 30 episodes, manifest hashes, timestamp/state continuity, command readback when present, stopping counterexamples and cleanup.
- `validate.py` checks input/code hashes, all 100 saved packets against original current rays and every recorded conditional stop outcome.
- Nine tests cover simulated trajectory enclosure, strict timestamp boundaries, policy/scope/class binding, forged priors, corrupted packets and monotone geometry.

No trusted history/bootstrap is used. Query vehicle half-extents are 2 m × 1 m, hypothetical speeds are 0/0.5/1 m/s, obstacle classes and raw-ray uncertainty are unchanged from previous studies. Actual Tesla diagnostic dimensions are recorded but are not admitted under that query body. Finite stopping does not imply perpetual safety against incoming traffic. SHA-256 provides artifact integrity, not sensor authentication.

## Reproduce saved-data experiments

Run from repository root with Python 3.8+, NumPy and SciPy. Existing output directories are not overwritten. Plotting additionally needs Matplotlib.

```bash
python -m unittest discover -s experiments/policy_evidence_20261001
python experiments/policy_evidence_20261001/run_geometry.py --capture results/visibility_certificate_20261001/carla120 --out /tmp/policy-geometry
python experiments/policy_evidence_20261001/run_renewal.py --capture results/visibility_certificate_20261001/carla120 --reference /tmp/policy-geometry --out /tmp/policy-renewal
python experiments/policy_evidence_20261001/analyze_actuation.py --results results/policy_evidence_20261001
python experiments/policy_evidence_20261001/validate.py --results results/policy_evidence_20261001 --capture results/visibility_certificate_20261001/carla120
python experiments/policy_evidence_20261001/plot_results.py --results results/policy_evidence_20261001
```

Cold times measure packet construction and receiver checking, excluding direct-geometry screening and acquisition; they already fail. Renewal includes recorded acquisition time, both measured processing stages and a hypothetical 20 ms link. Replay reference stamps and speeds are assigned model inputs. Production uses `/home/sheng/mobicom2027_visibility_20261001` with Python `/home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python`. Production capture input is `results/carla120`; outputs are `results/policy_geometry`, `results/policy_renewal`, `results/policy_actuation`, `results/policy_drivetrain`, `results/policy_sensitivity`. Committed result layout renames those to `geometry/`, `renewal/`, `actuation/`, `drivetrain/`, `sensitivity/`.

For new actuator capture, first start an exclusive CARLA 0.9.15 Town10HD_Opt server. Scripts reject an existing vehicle population, restore settings and destroy their own actors. Each `capture_*.py --host HOST --out NEW_DIR` implements its associated frozen protocol. Dedicated server process lifecycle is managed separately; recorded server cleanup JSON files document the production runs. These scripts do not run a recurring job.

`dependencies.json` hashes reused source and inputs; `SHA256SUMS` hashes committed result files. `sheng_validation.json` records the server-side tests and complete artifact validation. Existing source files named in production manifests were preserved; post-measurement strict guards and analysis have distinct files or final provenance hashes.
