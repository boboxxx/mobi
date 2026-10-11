"""Fixed post-result observation replay; no counterfactual driving result."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import numpy as np
from kernel import box_prefix

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'experiments/closed_loop_audit_20261011'))
import fast_expiry as fast
R = fast.R

parser = argparse.ArgumentParser()
parser.add_argument('--capture', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
assert not args.out.exists()
freeze_path = Path(__file__).parent/'freeze.json'
freeze = json.loads(freeze_path.read_bytes())
for section in ('sources','inputs'):
    for name, digest in freeze[section].items():
        assert R.sha(ROOT/name) == digest, name
context = json.loads((args.capture/'context.json').read_bytes())
radius = R.A.pose.enclosing_radius_um(context['extent'])
rows = []
for outcome in json.loads((args.capture/'outcomes.json').read_bytes()):
    if outcome['status'] != 'captured':
        continue
    path = args.capture/outcome['file']
    assert R.sha(path) == outcome['sha256']
    raw = gzip.decompress(path.read_bytes())
    assert hashlib.sha256(raw).hexdigest() == outcome['logical_sha256']
    data = json.loads(raw)
    cache, index = None, 0
    for row in data['rows']:
        while index < len(data['sources']) and data['sources'][index]['arrival_us'] <= row['now_us']:
            source = data['sources'][index]
            path = args.capture/'packets'/source['packet']
            assert R.sha(path) == source['packet_sha256']
            cache = R.decode(path.read_bytes(), context)
            index += 1
        if cache is None:
            continue
        state, query = cache['states']['history'], row['query_um']
        before = time.perf_counter_ns()
        old = fast.expiry(state, query, radius, 'history')
        old_fee = (time.perf_counter_ns()-before)/1000
        before = time.perf_counter_ns()
        box = None if old == R.CAP else box_prefix(state, query, radius+R.RADIUS, R.CAP)
        new = old if box is None else max(box, old)
        extra_fee = (time.perf_counter_ns()-before)/1000
        assert old <= new <= R.CAP
        decision = row['now_us']+R.BUDGET
        old_gate = cache['source_us'] <= decision and decision+R.ACTION <= cache['source_us']+old
        new_gate = cache['source_us'] <= decision and decision+R.ACTION <= cache['source_us']+new
        replay_total = math.ceil(old_fee+extra_fee)+row['receiver_fee_us']+row['command_fee_us']
        rows.append(dict(id=outcome['id'],step=row['step'],source_us=cache['source_us'],
            original_prefix_us=old,exact_box_prefix_us=box,combined_prefix_us=new,
            original_shadow_allowed=old_gate,new_shadow_allowed=new_gate,
            original_fast_fee_us=old_fee,additional_exact_fee_us=extra_fee,
            replay_total_with_original_receiver_and_rpc_us=replay_total,
            new_shadow_with_measured_replay_budget=bool(new_gate and replay_total <= R.BUDGET)))
gains = [r['combined_prefix_us']-r['original_prefix_us'] for r in rows]
fees = [r['additional_exact_fee_us'] for r in rows if r['exact_box_prefix_us'] is not None]
result = dict(scope='post-result same-observation algorithm replay; fixed original 20ms reserved shadow clock, no changed actuation, not certification or counterfactual route result',
    freeze_sha256=R.sha(freeze_path), summary=dict(queries=len(rows), exact_box_evaluated=len(fees),
        improved_prefixes=sum(g>0 for g in gains),maximum_prefix_gain_us=max(gains),
        original_shadow_allowed=sum(r['original_shadow_allowed'] for r in rows),
        new_shadow_allowed=sum(r['new_shadow_allowed'] for r in rows),
        shadow_gains=sum(not r['original_shadow_allowed'] and r['new_shadow_allowed'] for r in rows),
        shadow_losses=sum(r['original_shadow_allowed'] and not r['new_shadow_allowed'] for r in rows),
        new_shadow_allowed_with_measured_replay_budget=sum(r['new_shadow_with_measured_replay_budget'] for r in rows),
        replay_total_over_budget=sum(r['replay_total_with_original_receiver_and_rpc_us'] > R.BUDGET for r in rows),
        exact_additional_fee_mean_us=float(np.mean(fees)), exact_additional_fee_p95_us=float(np.quantile(fees,.95)),
        exact_additional_fee_max_us=max(fees)),rows=rows)
args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result['summary'],sort_keys=True))
