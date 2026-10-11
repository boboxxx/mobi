"""All observed history queries; exact equivalence and actual replay costs.

This post-result computation ablation cannot establish changed-route success.
Each case uses two measurements in alternating order; no fastest-run selection.
"""
import argparse
import gzip
import json
from pathlib import Path
import time
import numpy as np
import fast_expiry as fast
R = fast.R

parser = argparse.ArgumentParser()
parser.add_argument('--capture', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
assert not args.out.exists()
context = json.loads((args.capture/'context.json').read_bytes())
radius = R.A.pose.enclosing_radius_um(context['extent'])
costs = [[], []]
cases = 0
capped = 0
for outcome in json.loads((args.capture/'outcomes.json').read_bytes()):
    if outcome['status'] != 'captured':
        continue
    data = json.loads(gzip.decompress((args.capture/outcome['file']).read_bytes()))
    cache = None
    next_source = 0
    for row in data['rows']:
        while next_source < len(data['sources']) and data['sources'][next_source]['arrival_us'] <= row['now_us']:
            source = data['sources'][next_source]
            cache = R.decode((args.capture/'packets'/source['packet']).read_bytes(), context)
            next_source += 1
        if cache is None:
            continue
        state, query = cache['states']['history'], row['query_um']
        answers = []
        samples = [[], []]
        for repeat in range(2):
            order = (0, 1) if (cases+repeat)%2 == 0 else (1, 0)
            for index in order:
                begin = time.perf_counter_ns()
                value = (R.expiry if index == 0 else fast.expiry)(state, query, radius, 'history')
                samples[index].append((time.perf_counter_ns()-begin)/1000)
                answers.append(value)
        assert len(set(answers)) == 1, (outcome['id'], row['step'], answers)
        for index in (0, 1):
            costs[index].append(sum(samples[index])/2)
        cases += 1
        capped += int(answers[0] == R.CAP)
def statistics(values):
    return dict(mean_us=float(np.mean(values)), p50_us=float(np.quantile(values, .5)),
                p95_us=float(np.quantile(values, .95)), max_us=float(np.max(values)))
result = dict(scope='post-result algorithm replay, both methods on identical observed states and queries; measured host costs, no new physical rollout and no WCET claim',
    cases=cases, exact_expiry_mismatches=0, capped_cases=capped,
    original=statistics(costs[0]), fast=statistics(costs[1]),
    mean_speedup=float(np.mean(costs[0])/np.mean(costs[1])),
    original_us=costs[0], fast_us=costs[1])
args.out.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('original_us','fast_us')}, sort_keys=True))
