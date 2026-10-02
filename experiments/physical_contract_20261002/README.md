# Finite CARLA physical-contract falsification

New48-frame capture on sheng, six actual actor blueprints, four orientations and
two sensor mounts. This package tests the premise behind conditional evidence
lifetimes. See [protocol](PROTOCOL.md), [theory](THEORY.md), [primary API reading](READING.md)
and [Chinese result](../../research/physical_contract_result_20261002.md).

Use the existing CARLA0.9.15 environment and only an otherwise idle server.
`start_carla.ps1` refuses an existing CARLA process and limits its own lifetime
to30minutes. `capture.py` restores settings and destroys only actors it creates.
The actual run ended with zero vehicles/walkers/sensors, asynchronous settings
restored and its owned server process stopped. No scheduled loop exists.

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python experiments/physical_contract_20261002/capture.py --out /tmp/new-physical-capture
python experiments/physical_contract_20261002/analyze.py --capture results/physical_contract_20261002/capture --out /tmp/physical-analysis.json
python experiments/physical_contract_20261002/audit.py --results results/physical_contract_20261002 --out /tmp/physical-audit.json
python -m unittest discover -s experiments/physical_contract_20261002 -p test_contract.py -v
```

The authoritative Python on sheng is
`/home/sheng/mobicom2027_carla_smoke_20260926/venv/bin/python`.
Only capture needs CARLA; offline analysis uses NumPy/SciPy and the frozen legacy
projection modules. `audit.py` imports no tested geometric module and checks raw
semantic bytes, independent Euler transforms, source rays, occupied tiles and
256 perturbation corners per decisive ray. Own-return diameters give a separate
center-independent necessary outer-radius check. The displayed geometry is a
physical-model falsification, not an unsafe action issued by the verifier.

`eligibility.py` is an explicit separation boundary: conditional mathematical
horizons remain available, but this finite negative registry authorizes no
physical action. `unverified` is distinct from `refuted`. A locally configured
allowed population includes unseen/occluded actors; detected labels cannot narrow
it. An observed lack of contradictions is not a calibration certificate. This
boundary does not claim to solve the required shape/pose model or useful driving.

The initial analysis path-recording error occurred before reading pointclouds;
its log is preserved as `analysis_path_failure.log`. No frames were replaced or
resampled after looking at outcomes. Do not tune radii on these data and describe
the same frames as independent validation.
