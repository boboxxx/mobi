# Reproduce the finite physical evidence chain

Restore inherited logical inputs using the published parent restoration helpers.
Build the native body geometry on the current host if needed. The full pre-capture
source and input closure is freeze.json; do not alter historical files to make a
hash check pass. From the repository root:

```sh
c++ -std=c++17 -O3 -shared -fPIC experiments/body_expiry_20261004/proposer.cpp -o experiments/body_expiry_20261004/proposer.so
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m unittest discover -s experiments/ego_expiry_live_20261004 -p 'test_*.py'
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python experiments/ego_expiry_live_20261004/audit_portable.py --capture results/ego_expiry_live_20261004/capture --out /tmp/ego-expiry-independent-audit.json
python experiments/ego_expiry_live_20261004/verify_package.py
```

Choose a fresh audit filename; it refuses overwriting. Compare its bytes with
audit_sheng.json. Raw strided LiDAR clouds, actual compressed packets and complete
episode/control/fee trajectories are all retained. Each episode JSON is lossless
gzip with compressed and original logical SHA-256 and original byte length.

The original strict audit.py passed on sheng Python3.8. PORTABLE_AUDIT.md explains
the preserved local exact-float failure and the separately frozen1e-15 scalar
control reconstruction check for newer Python. Integer/geometry/gates remain
strict; compare all portable results with the original strict sheng audit.

The shared frozen frontend/model is replayed byte-for-byte. Exact geometry and
3D body reconstruction use independent auditors. Violations and source-set
exclusions are counted and reported, never converted into certification. A green
package check means byte closure and protocol execution; it does not mean a safe
or better controller. The post-result packaging/report files are pinned separately
from the immutable pre-capture experiment.

The service is measured-delay synchronous co-simulation, with a modeled20Mbps
link, declared propagation, shared own odometry and no uplink fee. It is not actual
V2V wireless, wall-clock/WCET driving or independently calibrated ego-policy risk.
All production deployment flags remain false; experimental geometric driving is
explicitly restricted to this constructed simulator. No recurring task exists.
