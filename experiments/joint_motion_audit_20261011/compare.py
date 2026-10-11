"""Check exact cross-host decisions, retaining floating audit values unchanged."""
import hashlib
import json
from pathlib import Path

P = Path('results/joint_motion_expiry_20261011')
remote = P/'sheng/scientific.json'
local = P/'local/scientific.json'
a, b = [json.loads(path.read_bytes()) for path in (remote, local)]
differences = []


def compare(x, y, path=''):
    if isinstance(x, dict):
        assert isinstance(y, dict) and set(x) == set(y)
        for key in x:
            compare(x[key], y[key], path+'/'+key)
    elif isinstance(x, list):
        assert isinstance(y, list) and len(x) == len(y)
        for i, (left, right) in enumerate(zip(x, y)):
            compare(left, right, path+'/'+str(i))
    elif x != y:
        assert path.endswith('/sampled_prefix_min_gap_um')
        assert isinstance(x, float) and isinstance(y, float) and abs(x-y) <= 1e-8
        differences.append(dict(path=path, sheng=x, local=y))


compare(a, b)
receipt = dict(status='PASS', all_decisions_packets_prefixes_fees_bounds_counts_identical=True,
    scientific_files_byte_identical=remote.read_bytes() == local.read_bytes(),
    different_float_fields=len(differences),
    max_abs_float_difference_um=max((abs(d['sheng']-d['local']) for d in differences), default=0),
    float_field='sampled_prefix_min_gap_um', float_comparison_tolerance_um=1e-8,
    science_sheng_sha256=hashlib.sha256(remote.read_bytes()).hexdigest(),
    science_local_sha256=hashlib.sha256(local.read_bytes()).hexdigest(), differences=differences)
print(json.dumps(receipt, sort_keys=True))
