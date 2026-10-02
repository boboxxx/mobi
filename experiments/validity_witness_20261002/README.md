# Received-evidence lifetime brackets and sender-information diagnostic

Finite sheng experiment,2026-10-02. It adds36 sphere,36 ellipsoid and12 independent
contact/heading searches on the same verified received histories. Every search
returns an admissible conditional hidden trajectory. An additional36-case
diagnostic finds one untransmitted current-scan ray per original sphere witness
that refutes that specific candidate. No new CARLA server or scheduled loop.

See [conditional derivation](THEORY.md), [Chinese report](../../research/validity_witness_result_20261002.md)
and [primary reading](READING.md). Original lower bounds come from the frozen
recursive-validity study. Initial36-case protocol was frozen before search;
shape, independent-heading and extra-ray extensions are separately identified
as post-analysis protocols, not disguised as preregistered original comparisons.

The joint lower/upper brackets are475.512–550ms in9 positive c0 queries and
475.551–545ms in6 c2 queries. These bound missed lifetime by at most74.488ms,
or13.5433%, **within the stipulated ray/kinematic task**. Three other queries
remain0–550ms: refusal is not an information-impossibility result. Extra facts
are760–768bytes of typed data and exclude one candidate; they are not complete
action certificates or evidence of a longer TTL. Conditional core/outer/error/
truthful-timestamp assumptions, stationary rectangle, repeated saved geometry,
no road/terrain constraints and modeled prior links limit the result. Search
cost83–239ms for radial families and3.337–4.687s for the heading family is offline
diagnostic work, not an online safety controller or WCET bound.

All252 trusted prefix packets and120 source dictionaries/clouds are independently
revalidated. Chosen84 trajectories undergo13,946,682 full3D segment checks and
exact-rational motion integration. Additional facts pass2304 independent box
corner checks. Fourteen distinct tests pass on both hosts; all three audit JSON
pairs match bytewise. The first search completed its cases but failed at relative
path metadata writing; fixed rerun data are authoritative, and failure log is retained.

## Reproduction

Run at repository root, using a fresh destination for benchmark outputs.
Requirements: C++17 compiler, Python with NumPy/SciPy/Matplotlib. sheng used the
existing Python3.8 CARLA experiment venv. Saved prior source/results directories
must be present and unchanged. Set all three BLAS/OpenMP thread variables to1.

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p build/validity_witness_20261002
g++ -O3 -std=c++17 -shared -fPIC experiments/validity_witness_20261002/segments.cpp -o build/validity_witness_20261002/segments.so
g++ -O3 -std=c++17 -shared -fPIC experiments/validity_witness_20261002/ellipsoid.cpp -o build/validity_witness_20261002/ellipsoid.so
export MOBI_SEGMENT_LIBRARY=$PWD/build/validity_witness_20261002/segments.so
export MOBI_ELLIPSOID_LIBRARY=$PWD/build/validity_witness_20261002/ellipsoid.so
python -m unittest discover -s experiments/validity_witness_20261002 -p 'test_*.py' -v
```

On macOS use `clang++ -O3 -std=c++17 -dynamiclib` and `.dylib` output paths.
Archive compiler command/source/binary SHA in `build.json` and
`ellipsoid_build.json` as the saved run does. Do not replace saved source hashes
with modified code or compare newly measured timing against the old hashes.

```bash
python experiments/validity_witness_20261002/bench.py --out results/validity_witness_new/study
python experiments/validity_witness_20261002/analyze.py --results results/validity_witness_new --out results/validity_witness_new/audit_sheng.json
# Independently audit on the second host and copy audit_local.json back first.
python experiments/validity_witness_20261002/ellipsoid_bench.py --results results/validity_witness_new
python experiments/validity_witness_20261002/heading_bench.py --results results/validity_witness_new
python experiments/validity_witness_20261002/ellipsoid_analyze.py --results results/validity_witness_new --out results/validity_witness_new/extension_audit_sheng.json
python experiments/validity_witness_20261002/extra_ray_bench.py --results results/validity_witness_new
python experiments/validity_witness_20261002/extra_ray_analyze.py --results results/validity_witness_new --out results/validity_witness_new/extra_ray_audit_sheng.json
# Repeat both additional independent audits on the second host.
python experiments/validity_witness_20261002/summarize.py --results results/validity_witness_new
python experiments/validity_witness_20261002/plot.py --results results/validity_witness_new
```

Saved data: [joint_bounds.json](../../results/validity_witness_20261002/joint_bounds.json),
[sphere audit](../../results/validity_witness_20261002/audit_sheng.json),
[shape/heading audit](../../results/validity_witness_20261002/extension_audit_sheng.json),
[extra-ray audit](../../results/validity_witness_20261002/extra_ray_audit_sheng.json).
Only backend-independent audits run locally on the sheng timing data; separate
local unit tests use local native builds. No sheng timing is relabeled local.
