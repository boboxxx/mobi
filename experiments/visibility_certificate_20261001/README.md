# Evidence validity from incomplete ray observations

Finite sheng implementation and measurements, 2026-10-01. [Scientific report](../../research/visibility_certificate_result_20261001.md), [validated results](../../results/visibility_certificate_20261001/analysis.json), [figure](../../results/visibility_certificate_20261001/findings.png).

The implementation derives a **conditional lower bound** on the time during which a declared disk stays free of the stipulated obstacle classes. It does not interpolate empty polygons between LiDAR rays. It excludes impossible obstacle-center locations, keeps every unresolved tile and the outside domain, and propagates those possible centers under bounded motion. This is not a full vehicle planner or a guarantee for arbitrary objects.

## Files and interface

- `geometry.py`: fixed physical profile, first-return plane witnesses, conservative tile exclusion and kinematic validity.
- `proof_packet.py`: quantized sparse witness proof, independently checked against receiver-selected profile/scope/time. SHA-256 detects corruption, **not authenticity**.
- `renewal.py`: reuse support locations, find **current** witness points, recheck cover; `verify_all` requires every receiver-required class.
- `run_study.py`: 2,000 analytic scenes and four archived CARLA clouds.
- `capture_carla.py`: 120 new, frame-matched CARLA scans, without a driving controller.
- `run_renewal.py`: per-class timing diagnostic; profile mismatch can cause refusal.
- `run_bundle.py`: fixed template profiles, both classes, serial CPU accounting, 200 ms validity, 232 finite attempts.
- `analyze.py`: source/protocol hashes, raw frame IDs, actual current-ray provenance, serialized receiver proofs, plots.

Read the conditional contract in [PROTOCOL.md](PROTOCOL.md). The [pre-production addendum](ADDENDUM.md) and [post-diagnostic timing follow-up](TIMING_FOLLOWUP.md) preserve changes to the finite experimental scope.

`Profile.error` bounds the **resulting planar witness** error, including pose, map, ray and projection effects. It is not automatically the LiDAR range error. A trusted upstream bound is required. A `scope` must resolve to an immutable receiver-known query geometry, reference frame, probe plane, physical contract, and action occupancy; the string alone does not establish these facts. `produced_at` is the actual scan time in a bounded-error common clock, never the packet-generation or template time. Current replay uses relative time zero plus recorded/modelled age, not a deployed clock protocol.

When no valid proof is available, the API returns `None` or `False`. A safety controller must supply its independently validated fallback. Simply braking is not proven safe by this code. If templates need a cold rebuild, do not execute an action on an already expired initialization packet.

## Reproduce from the repository root

Measured environment: sheng WSL Ubuntu-20.04, Python 3.8.10, NumPy 1.24.4, SciPy 1.10.1; acquisition uses CARLA client/server 0.9.15 on the Windows host and RTX 4090. Plots additionally use Matplotlib. Existing sheng interpreter: `/home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python`. No daemon or recurring research job is needed.

```bash
python -m unittest discover -s experiments/visibility_certificate_20261001 -p 'test_*.py'
python experiments/visibility_certificate_20261001/analyze.py \
  --results results/visibility_certificate_20261001
```

Add `--no-plots` if Matplotlib is unavailable. This verifies the published artifacts, including 76 serialized class proofs against their **current** raw scan witnesses.

For new finite runs, use empty output directories (scripts refuse overwrites):

```bash
python experiments/visibility_certificate_20261001/run_study.py \
  --archive results/renewal_sheng_20261001/carla_coverage_v4 \
  --scenes 2000 --out /tmp/visibility-study-new

# Requires an otherwise idle CARLA 0.9.15 instance at HOST:2000.
python experiments/visibility_certificate_20261001/capture_carla.py \
  --host HOST --out /tmp/visibility-capture-new

python experiments/visibility_certificate_20261001/run_renewal.py \
  --capture /tmp/visibility-capture-new --out /tmp/visibility-renewal-new
python experiments/visibility_certificate_20261001/run_bundle.py \
  --capture /tmp/visibility-capture-new --out /tmp/visibility-bundle-new
```

Source-hash manifests record the exact versions used; changing frozen source will intentionally fail artifact validation. Reported timings are hardware/run-specific. `analyze.py` checks the published finite protocol counts; it is not a validator for arbitrary different experiment sizes.

## Results and costs

2,000 analytic scenes: 417 positive certificates, zero detected false center exclusions or expiry overestimates **under the disk model**. 120 new CARLA scans: no stale frames. All twelve tests passed locally and on sheng. Two-class 200 ms renewal: 38 successful free/far frames, 20 eligible near frames rejected; across all settings, 38/232 attempts succeeded, 174 lacked both initialization templates. Repeated static frames are not independent scene trials.

Accepted bundles are 9,148–9,794 bytes, including JSON framing/profile/scope/checksum; communication authentication, real link overhead, and retransmission costs are not measured. Measured acquisition and serial processing plus modeled 20 ms transport give 104.05–137.97 ms age. Adding the stipulated 50 ms action stays below 200 ms in those 38 frames. The original 100 ms and cold-start failures remain in the dataset.

Capture cleanup recorded one vehicle and one sensor before destruction had fully become visible to the actor listing. The separately recorded `server_cleanup.json` confirms the specifically launched experiment server was stopped; do not present the earlier actor snapshot as zero residual actors. No other CARLA process was terminated.
