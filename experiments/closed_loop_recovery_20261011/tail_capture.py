"""Run ONLY the four never-attempted frozen requests after storage failure.

The frozen implementation, parameters, and hashes remain untouched. This
explicit adapter changes execution scope, not algorithms or scene parameters.
The attempted failed closed_07 is not run again.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
E = ROOT/'experiments/closed_loop_motion_20261011'
assert hashlib.sha256((E/'freeze.json').read_bytes()).hexdigest() == '8254fe6c30a1f7dacbfb78191659efeea1158a987eea1fec3cdd1ccacb67354e'
original_plan_bytes = (E/'plan.json').read_bytes()
original_plan = json.loads(original_plan_bytes)
assert [r['id'] for r in original_plan[8:]] == ['closed_08', 'closed_09', 'closed_10', 'closed_11']
P = ROOT/'results/closed_loop_motion_20261011'
completed = json.loads((P/'capture/outcomes.json').read_bytes())
assert [r['id'] for r in completed] == [r['id'] for r in original_plan[:7]]
assert (P/'capture/episodes/closed_07.json.gz').exists()
assert P.is_symlink() and str(P.resolve()) == '/mnt/c/Users/Administrator/mobi-closed-loop-motion-data-20261011'
assert not (P/'tail_capture').exists()


class JsonScopeAdapter:
    @staticmethod
    def loads(data, *args, **kwargs):
        if data == original_plan_bytes:
            return json.loads(original_plan_bytes)[8:]
        return json.loads(data, *args, **kwargs)

    @staticmethod
    def dumps(*args, **kwargs):
        return json.dumps(*args, **kwargs)


sys.path.insert(0, str(E))
spec = importlib.util.spec_from_file_location('frozen_closed_capture', E/'capture.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.json = JsonScopeAdapter
sys.argv = [str(E/'capture.py'), '--out', str(P/'tail_capture')]
module.main()
