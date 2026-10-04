# Reproduce the finite whole-ego episode certificate

Restore inherited logical inputs using parent published restoration helpers, and
build the native body geometry kernel from its frozen source. From the repository
root, choose fresh audit output filenames:

```sh
c++ -std=c++17 -O3 -shared -fPIC experiments/body_expiry_20261004/proposer.cpp -o experiments/body_expiry_20261004/proposer.so
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m unittest discover -s experiments/ego_policy_certificate_20261004 -p 'test_*.py'
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python experiments/ego_policy_certificate_20261004/audit.py --split certification --capture results/ego_policy_certificate_20261004/certification_capture --out /tmp/ego-episode-independent-certification-audit.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python experiments/ego_policy_certificate_20261004/audit.py --split test --capture results/ego_policy_certificate_20261004/test_capture --out /tmp/ego-episode-independent-test-audit.json
python experiments/ego_policy_certificate_20261004/audit_certificate.py --out /tmp/ego-episode-independent-statistical-audit.json
OPENBLAS_NUM_THREADS=1 python experiments/ego_policy_certificate_20261004/summarize.py --out /tmp/ego-episode-independent-test-summary.json
```

Compare audit/summary byte sequences with their sheng artifacts. All planned failed
and refused episodes, partial attempts, original strided clouds, packets, measured
fees and lossless trajectories are retained. CI audit uses an independent rational
recurrence; model/frontend replay uses shared frozen code. Same-source epochs and
integer gates remain strict. The previously explained1e-15 feedback-scalar portability
check was fixed before these captures.

Read PROTOCOL.md, RISK_ARGUMENT.md and RUN_ENVIRONMENT.md for the required joint
IID and body/motion assumptions. This certificate is for this fixed finite3s,
20-source, registered parked-target episode law; it does not transfer to previous
160-source or indefinite driving, new geometry/controllers, true wireless, unseen
actors, or continuous physical collision probability. No old six-frame calibration
confidence is inherited. Every method uses one source serialization; cone is a
strong compact queryable comparator based on the standard distance triangle bound.
No recurring automation or continuous research batch exists.

After plotting and generating the publication manifests, run
`python experiments/ego_policy_certificate_20261004/verify_package.py --out /tmp/ego-episode-package-verification.json`
to verify the byte closure, original failed episodes, plan denominators, server
ownership/cleanup, all three methods and exact local/sheng replay agreement.
`analysis_freeze.json` pins the summary/plot/packaging helpers before held-out
capture; `analysis_preregistration.json` records their deployment conditions.
Summary quantiles use rational linear interpolation over the recorded binary64
values to avoid different NumPy versions changing the interpolation arithmetic.
