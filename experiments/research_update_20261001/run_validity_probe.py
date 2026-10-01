#!/usr/bin/env python3
"""Finite synthetic diagnostic with shared exogenous outcomes; no CARLA claims."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import random
import time
import numpy as np
from validity_scheduler import advance, choose, sufficient, solve

CONFIGS={'uniform':(6,6), 'heterogeneous':(2,6), 'three_regions':(3,4,6), 'impossible':(1,1)}
METHODS=('max_age','edf','myopic_completion','finite_horizon')


def write(path, rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--seeds',type=int,default=200);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False);rows=[];start=time.perf_counter()
    for config,ttl in CONFIGS.items():
        required=tuple(range(len(ttl)))
        for seed in range(a.seeds):
            # Complete outcome table before any policy executes; independent of
            # selected action and message ordering, shared by all policies.
            rng=random.Random(seed)
            outcomes=[[rng.random()<.9 for _ in ttl] for _ in range(30)]
            for method in METHODS:
                ages=tuple(t+1 for t in ttl);reward=sent=invalid=0
                for t in range(30):
                    action=choose(method,ages,ttl,required,horizon=3,success_p=.9)
                    ages=advance(ages,ttl,action,action is not None and outcomes[t][action])
                    valid=sufficient(ages,ttl,required)
                    reward+=valid;sent+=action is not None
                    # Alternative check of a controller that omits action guard.
                    invalid+=sufficient(ages,ttl,required,guard=0) and not valid
                rows.append(dict(config=config,seed=seed,method=method,valid_fraction=reward/30,
                                 sent_messages=sent,unguarded_invalid_opportunities=invalid))
    write(a.out/'per_episode.csv',rows)
    comparisons=[];summary=[];rng=np.random.default_rng(20261001)
    for config in CONFIGS:
        lookup={(r['method'],r['seed']):r for r in rows if r['config']==config}
        for method in METHODS:
            cells=[lookup[method,s] for s in range(a.seeds)]
            summary.append(dict(config=config,method=method,valid_fraction=np.mean([r['valid_fraction'] for r in cells]),
                                sent_messages=np.mean([r['sent_messages'] for r in cells])))
        for baseline in METHODS[:-1]:
            x=np.asarray([lookup['finite_horizon',s]['valid_fraction']-lookup[baseline,s]['valid_fraction'] for s in range(a.seeds)])
            boot=x[rng.integers(0,len(x),(4000,len(x)))].mean(1)
            comparisons.append(dict(config=config,baseline=baseline,seed_clusters=a.seeds,diff=x.mean(),ci_low=np.quantile(boot,.025),ci_high=np.quantile(boot,.975)))
    write(a.out/'summary.csv',summary);write(a.out/'paired_comparisons.csv',comparisons)
    manifest=dict(date='2026-10-01',episodes=len(rows),seeds=a.seeds,slots=30,success_p=.9,action_guard=1,lookahead=3,
                  configs=CONFIGS,elapsed_s=time.perf_counter()-start,cache=solve.cache_info()._asdict(),
                  code_sha256={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['run_validity_probe.py','validity_scheduler.py']},
                  scope='Synthetic all-free evidence with supplied TTLs and fixed required regions. Exact short-horizon oracle; no learned model, geometry, control, or scalability result.',
                  randomness='Pre-generated per-seed per-slot per-region outcomes shared by every policy; no future outcomes visible to scheduler.')
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(manifest=manifest,comparisons=comparisons),indent=2))


if __name__=='__main__':main()
