# Continuous pose inversion and same-information witnesses

Finite execution on sheng, 2026-10-03. This is a negative feasibility result:
all288 calls have zero lower expiry, and no whole pose cell is excluded within
the2000-node budget. True-box retention is not enough for useful state localization.
This package preserves the complete results instead of narrowing the success claim.

- [Chinese report](../../research/pose_inversion_result_20261003.md)
- [Original frozen protocol](PROTOCOL.md), [tighter-bound follow-up](PROTOCOL_REFINED.md)
- [Derivation and precise scope](THEORY.md), [primary reading](READING.md)
- [Summary](../../results/pose_inversion_20261003/summary.json)

## Reproduction

From repository root, with NumPy and SciPy (Matplotlib for the figure):

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m unittest discover -s experiments/pose_inversion_20261003 -v
python experiments/pose_inversion_20261003/audit.py --results results/pose_inversion_20261003 --out /tmp/pose-audit.json
python experiments/pose_inversion_20261003/witness_bank.py --results results/pose_inversion_20261003 --out /tmp/pose-witness-bank.json
python experiments/pose_inversion_20261003/summarize.py --results results/pose_inversion_20261003 --out /tmp/pose-summary.json
python experiments/pose_inversion_20261003/plot.py --results results/pose_inversion_20261003
```

To rerun the finite computation rather than audit its archived outputs, choose new
output directories. The source scans are already in the previous shape package;
no CARLA server is needed.

```sh
python experiments/pose_inversion_20261003/run.py --out /tmp/pose-replay-new
python experiments/pose_inversion_20261003/run_refined.py --out /tmp/pose-refined-new
```

These commands each execute144 calls, retain all nodes/witnesses and refuse to
overwrite an existing output directory. CPU times naturally vary. The measured
producer code/dependencies are pinned by source_manifest.json and
refinement_manifest.json. Later audit/report additions are separately covered by
the final publication manifest; they do not change the measured algorithms.

## What the receiver uses

`packet.py` sends ordered xyz, pose, time, source frame and calibration identity,
without semantic IDs. `bounds.py` and `refined.py` conservatively bound a fixed
score over continuous cells; `solver.py` retains all unresolved space and unknown
domain boundaries. `run.py` never uses the actor's true position to construct the
posterior. Its declared shape class and catalog are known experimental premises.
`audit.py`, `summarize.py` and `plot.py` use truth ONLY for diagnostics.

The independent audit imports neither solver/bounds nor their point-score module.
It uses a separate six-face intersection reference, elementary rotation matrices,
tree partition verification and a70-digit collision-time calculation. Original
unrounded cross-host truth annotations remain archived; displayed annotations are
canonicalized after domain checks, without changing any geometry decision.

`witness_bank.py` is offline analysis, not a deployable or free-cost selector.
It rescans every distinct pose under every budget and tightens upper bounds from
the same received information. A retained pose is a witness for the calibrated
score/disc abstraction, not an established physical counterfactual. The projected
bbox diagnostic explicitly distinguishes some disc-only overlaps, but even bbox
overlap is not a solid-mesh collision. No physical action gate is opened.

The key unresolved step is a genuinely localizing, calibrated measurement model
and validated direction-aware dynamics. More subdivision or full raw transfer
alone is not supported as a successful solution by these results.

## Additional diagnostics

`transport_and_support.py` verifies raw, zlib and word-XOR/byte-shuffle codecs and
finds18/25 full-budget surviving poses supported exclusively by near-road-height
nonpassing returns, with no true-actor support. Semantic IDs are audit-only.
`reference_codec.py` provides a stronger fixed-design-reference lossless baseline:
full current packets shrink to19,413–53,663 bytes after725,278-byte reference
installation. Current timestamps and all current xyz reconstruct bitwise; missing
or mismatched references refuse decoding. Cached geometry is never current evidence.
Cold setup remains too expensive for the500ms model, while warm bytes fit; this
removes a raw-transfer bottleneck but cannot repair the old score's zero horizons.
The [terrain follow-up](../terrain_score_20261003/README.md) changes and recalibrates
the measurement score separately. Original producer hashes/results stay frozen.
