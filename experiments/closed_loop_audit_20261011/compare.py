"""Cross-host audit outputs: exact discrete values, explicit float tolerance."""
import argparse
import json
import math
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--sheng', type=Path, required=True)
parser.add_argument('--local', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
assert not args.out.exists()
differences = []
def compare(a, b, path=''):
    assert type(a) is type(b), path
    if isinstance(a, dict):
        assert a.keys() == b.keys(), path
        for key in a:
            compare(a[key], b[key], path+'/'+key)
    elif isinstance(a, list):
        assert len(a) == len(b), path
        for i, (x, y) in enumerate(zip(a, b)):
            compare(x, y, path+'/'+str(i))
    elif isinstance(a, float):
        assert math.isfinite(a) and math.isfinite(b), path
        assert math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-9), (path, a, b)
        if a != b:
            differences.append(dict(path=path, sheng=a, local=b, absolute_difference=abs(a-b)))
    else:
        assert a == b, (path, a, b)
compare(json.loads(args.sheng.read_bytes()), json.loads(args.local.read_bytes()))
result = dict(status='PASS', all_discrete_values_identical=True,
    float_abs_tolerance=1e-9, float_rel_tolerance=1e-10,
    float_differences= differences, byte_identical=args.sheng.read_bytes()==args.local.read_bytes())
args.out.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps(dict(status='PASS', float_differences=len(differences), byte_identical=result['byte_identical']), sort_keys=True))
