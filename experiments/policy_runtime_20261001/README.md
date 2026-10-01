# Current-ray proof runtime and policy realization

Read the [Chinese research report](../../research/policy_runtime_result_20261001.md). This finite sheng increment includes three runtime stages (4,176 + 3,132 + 2,088 method/case evaluations), 120 synthetic ray-perturbation cases and 36 new CARLA actuator episodes. All runtime stages reuse the same 1,044 base cases; these are not independent driving scenes.

**Result:** receiver checks become faster while preserving the original conditions. Only two hypothetical stationary cases pass the modeled time budget in one binary run; no moving configuration passes. Actual paired control tests show almost no extra motion from the 50 ms go command after a 100 ms brake hold. Physical safety and useful evidence-guided driving remain unestablished.

## Algorithms and trust

- `incremental.py`: caches cell-to-ray index hints. Every cell is checked against current witnesses/errors; lost coverage triggers the full reference query. Source and receiver hints are separate, never trusted free-space history.
- `local_renew.py`: bounded nearest-neighbor search with full-tree fallback for distance ambiguity/ties, plus the current-ray verifier.
- `binary_proof.py`, `binary_renew.py`: lossless PVX1 integer wire and equivalent geometry; checksum is not authentication. The wire is not byte-identical to JSON; decoded rays and metadata must be identical.
- `proposal.py`: builds an **unverified** current-ray candidate. It may only become a conditional certificate after receiver verification. Rejected proposal bytes are included in communication totals.
- Timing-only helpers require prior verification of the same immutable packet. They do not authorize physical movement, establish physical contracts or provide replay/history management.

Existing bodies, obstacles, projection uncertainties, 120 ms hold budget and 20 ms modeled link are unchanged. Observed actuator counterexamples remain applicable to the conditions where they were measured. Cached verification does not repair uncalibrated physics.

## Frozen protocols

`PROTOCOL.md` defines the four JSON ablations. `BINARY_PROTOCOL.md` defines the three lossless-wire methods. `PROPOSAL_PROTOCOL.md` adds two receiver-only verification baselines. `PERTURBATION_PROTOCOL.md` defines 120 fixed sparse-packet mutations. `EXECUTION_PROTOCOL.md` defines 18 go/brake-only pairs with snapshot-bound samples. Each production manifest hashes the source files present at its execution; subsequent stages add files rather than altering those sources.

## Reproduce

From repository root, Python 3.8+, NumPy and SciPy; Matplotlib is needed only for the plot. New output directories must not exist. The previous artifact remains a required input and is not overwritten.

```bash
python -m unittest discover -s experiments/policy_runtime_20261001
python experiments/policy_runtime_20261001/run_ablation.py --capture results/visibility_certificate_20261001/carla120 --templates results/policy_evidence_20261001/geometry --reference results/policy_evidence_20261001/renewal --out /tmp/runtime-ablation
python experiments/policy_runtime_20261001/run_binary.py --capture results/visibility_certificate_20261001/carla120 --templates results/policy_evidence_20261001/geometry --reference results/policy_evidence_20261001/renewal --out /tmp/runtime-binary
python experiments/policy_runtime_20261001/run_proposal.py --capture results/visibility_certificate_20261001/carla120 --templates results/policy_evidence_20261001/geometry --reference results/policy_evidence_20261001/renewal --out /tmp/runtime-proposal
python experiments/policy_runtime_20261001/run_perturbation.py --template results/policy_evidence_20261001/geometry/packets/dense_0_free_00_v0.5_h0.4.json --out /tmp/runtime-perturbation
python experiments/policy_runtime_20261001/analyze_execution.py --results results/policy_runtime_20261001
python experiments/policy_runtime_20261001/validate.py --results results/policy_runtime_20261001 --capture results/visibility_certificate_20261001/carla120 --previous results/policy_evidence_20261001
python experiments/policy_runtime_20261001/plot_results.py --results results/policy_runtime_20261001
```

For new actual control diagnostics, start an exclusive CARLA 0.9.15 Town10HD_Opt server, then run `capture_execution.py --host HOST --out NEW_DIR`. It owns/destroys its actors and restores world settings. The server process is separately bounded and owned; production cleanup is recorded. No continuing research automation is created.

sheng workdir: `/home/sheng/mobicom2027_visibility_20261001`; Python: `/home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python`. Production output directories are `results/policy_runtime_{ablation,binary,proposal,perturbation,execution}` plus `results/policy_profile`. The committed package groups these as `ablation/`, `binary/`, `proposal/`, `perturbation/`, `execution/`, `profile/`. `dependencies.json`, `SHA256SUMS` and `sheng_validation.json` anchor the reproducibility audit. Raw CSV CRLF and log bytes are preserved.
