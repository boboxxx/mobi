# Receiver-recomputable ray evidence, version 2

Finite sheng experiments: selected **current raw rays**, receiver-side uncertainty/time recomputation, exact renewal acceleration, and two fresh dynamic CARLA receiver-monitor runs. Read the [Chinese research report](../../research/ray_proof_v2_result_20261001.md) for claims and failures.

This is a conditional geometric certificate, not sensor authentication or a complete autonomous driving controller. Input error boxes and opaque-core/outer-radius contracts are stipulated. Protected occupancy is a 0.5 m disk. The fixed requested horizon is 200 ms, not a maximum-lifetime estimate. The preceding `visibility_uncertainty_20261001/weighted.py` computes lifetime from complete observations.

## Files and frozen stages

- `proof.py`: pack, decode, and independently verify a joint two-class raw-ray proof. Same receiver for every optimization.
- `run_replay.py`, `PROTOCOL.md`: 144 cold / 1,392 renewal static replay configurations, both successful and refused.
- `optimized.py`, `run_fast.py`, `FAST_FOLLOWUP.md`: shared pose encoding, validated support cache, exact packet comparison.
- `capture_dynamic.py`, `DYNAMIC_PROTOCOL.md`: first 128-frame moving-obstacle receiver monitor, without ego control.
- `optimized_local.py`, `run_local.py`, `DYNAMIC_LOCAL_FOLLOWUP.md`: bounded local lookup with exact full-tree fallback; 1,392 packet comparisons.
- `capture_dynamic_local.py`: repeat the same live protocol with local lookup, new raw data.
- `test_*.py`: thirteen tests, including malformed/future/expired/scope/class rejection, fresh renewal, duplicated-ray ties and lookup equivalence.
- `analyze.py`: source/protocol/input hash validation, ray provenance, every positive receiver check and expiry refusal, frame alignment and future center diagnostics. Does not infer real-world safety from zero violations.

Each production manifest records its source/protocol hashes. Earlier unsuccessful implementations remain frozen. The manifests and SHA256SUMS make accidental changes detectable; they are not third-party attestations.

## Reproduce without a simulator

Python 3 with NumPy and SciPy; plotting additionally requires Matplotlib. Production sheng Python is `/home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python`. Run from repository root. Output folders must not already exist. Exact byte comparisons are checked on the saved inputs; wall-clock timing varies by machine/load.

```bash
python -m unittest discover -s experiments/ray_proof_v2_20261001
python experiments/ray_proof_v2_20261001/run_replay.py --capture results/visibility_certificate_20261001/carla120 --out /tmp/ray-v2-reference
python experiments/ray_proof_v2_20261001/run_fast.py --capture results/visibility_certificate_20261001/carla120 --reference /tmp/ray-v2-reference --out /tmp/ray-v2-fast
python experiments/ray_proof_v2_20261001/run_local.py --capture results/visibility_certificate_20261001/carla120 --reference /tmp/ray-v2-reference --out /tmp/ray-v2-local
python experiments/ray_proof_v2_20261001/analyze.py --results results/ray_proof_v2_20261001 --capture results/visibility_certificate_20261001/carla120
```

For the committed artifact, `analyze.py` validates the preserved production manifests and raw clouds. `--no-plots` avoids Matplotlib. Run `sha256sum -c SHA256SUMS` from the result directory to check all preserved outputs.

## Fresh simulator acquisition

Requires matching CARLA 0.9.15 Python API and an **exclusive, empty** Town10HD_Opt server. sheng's WSL client connects to its Windows server. The acquisition restores prior world settings and destroys its own actors in `finally`. Do not point it at a shared simulation. Set `--host` to the server IP if different.

```bash
python experiments/ray_proof_v2_20261001/capture_dynamic.py --host 100.109.48.32 --out /tmp/ray-v2-dynamic
python experiments/ray_proof_v2_20261001/capture_dynamic_local.py --host 100.109.48.32 --out /tmp/ray-v2-dynamic-local
```

Production server flags: `Town10HD_Opt -RenderOffScreen -nosound -unattended -quality-level=Low -carla-rpc-port=2000`. Each run has two mounts, 64 frames each, 50 ms simulation steps and one Audi A2 commanded toward the query at 4 m/s. Each measurement's rays share CARLA's frame timestamp. Offline azimuth-based 20/50 ms timestamps are a distinct hypothetical scan diagnostic.

Latency is measured acquisition plus computation, with **modeled** 20 ms transport and 50 ms action. Synchronous simulation pauses during computation. Neither script drives an ego vehicle or measures an actual wireless link. Vehicle state labels are evaluation-only. Future-center checks linearly interpolate recorded centers, not continuous mesh collisions.

## Result mapping

Committed root: `results/ray_proof_v2_20261001/`.

| Local artifact | sheng path under `/home/sheng/mobicom2027_visibility_20261001/` | Geometry / timing |
|---|---|---|
| `cold.csv`, `renewal.csv`, packets | `results/proof_v2` | 32/0 cold; 299/0 renewal |
| `fast/` | `results/proof_v2_fast` | 299/266 |
| `local/` | `results/proof_v2_local` | 299/288 |
| `dynamic/` | `results/proof_v2_dynamic` | 23/1 |
| `dynamic_local/` | `results/proof_v2_dynamic_local` | 22/9 |

No template failures are dropped. Sparse/near/old evidence can refuse. Cold-start latency remains a failure. A compressed complete-ray representation is byte accounting only; it exceeds the compact proof ray-count cap and is not an implemented full competitor. The uniform selector uses the first sufficient common threshold, not a globally optimal compression policy.
