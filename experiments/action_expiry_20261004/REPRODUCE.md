# Reproduce the finite query-interface verification

Run from the repository root. This is a deterministic historical-fixture replay,
not new calibration, policy certification, ego control or wireless evaluation.
The original fixed-query risk certificate is not transferable.

Restore the parent logical results with
`python experiments/prospective_component_20261004/restore_results.py` and the
older inherited logical inputs with their published restoration helpers if absent.
`freeze.json` lists every required source/input hash; the auditor refuses missing
or altered dependencies. Do not modify historical files to satisfy a hash check.

Build the native geometry on the current host if needed:

```sh
c++ -std=c++17 -O3 -shared -fPIC experiments/body_expiry_20261004/proposer.cpp -o experiments/body_expiry_20261004/proposer.so
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m unittest discover -s experiments/action_expiry_20261004 -p 'test_*.py'
python experiments/action_expiry_20261004/verify_package.py
python experiments/action_expiry_20261004/audit.py --out /tmp/action-query-independent-audit.json
```

Choose a fresh audit output path; `audit.py` refuses overwriting it. Compare its
bytes with `results/action_expiry_20261004/audit_sheng.json`.

The complete 65,472 case-level outputs are published without compression or
discarding refusals. `probe.py` reproduces them in a clean isolated checkout with
the required frozen parent inputs; it deliberately refuses to overwrite existing
`cases_sheng.jsonl` or `probe_sheng.json`. Keep original published outputs intact.
The preregistration records that cases did not exist before the sheng run.

`verify_package.py` is post-result packaging code; it does not tune the kernel or
run new experiments. It checks the pre-replay freeze, all result bytes, dual-host
audit equality, terminal completion, regression counts and the explicit absence
of new policy authorization. The publication manifest additionally pins this
packager, reproduction instructions and final report. Manifest and verification
receipts exclude themselves to avoid circular hashing.
