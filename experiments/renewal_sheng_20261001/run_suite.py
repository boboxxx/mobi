#!/usr/bin/env python3
"""Bounded, seed-paired reference experiment. All timing measured on run host."""
import argparse
import csv
import hashlib
import json
import platform
from pathlib import Path
import random
import socket
import sys
import time
import numpy as np
from scheduler import advance, choose, solve, valid
from certificate import lifetime, supports

METHODS = ('edf', 'normalized_age', 'long_first_cycle', 'group_refresh',
           'deterministic_mpc3', 'stochastic_mpc3', 'stochastic_mpc6')
CONFIGS = {
    'uniform': dict(ttl=(6,6)),
    'heterogeneous': dict(ttl=(2,6)),
    'three_regions': dict(ttl=(3,4,6)),
    'impossible': dict(ttl=(1,1)),
    'lossy': dict(ttl=(2,6), p=.7),
    'reliable': dict(ttl=(2,6), p=1.),
    'guard_two': dict(ttl=(3,7), guard=2),
    'service_two': dict(ttl=(3,7), service=2),
    'switch_required': dict(ttl=(3,4,6), switching=True),
    'ttl_overestimate_one': dict(ttl=(3,7), true_ttl=(2,6)),
    'ttl_conservative_one': dict(ttl=(2,6), true_ttl=(3,7)),
}


def write(path, rows):
    with path.open('w', newline='') as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader(); w.writerows(rows)


def episode(method, config, seed, decisions):
    ttl=config['ttl']; true_ttl=config.get('true_ttl',ttl)
    p=config.get('p',.9); guard=config.get('guard',1); service=config.get('service',1)
    rng=random.Random(seed)
    outcomes=[[rng.random()<p for _ in ttl] for _ in range(decisions)]
    # Keep uncapped evaluation ages separately, so shorter/longer true validity
    # does not get accidentally concealed by the scheduler state cap.
    ages=tuple(t+1 for t in ttl); actual_ages=[1000]*len(ttl)
    claims=good=false=missed=sent=0; durations=[]
    for step in range(decisions):
        required=tuple(range(len(ttl)))
        if config.get('switching'):
            required=(0,1) if (step//10)%2==0 else (1,2)
        begin=time.perf_counter_ns()
        action=choose(method,ages,ttl,required,guard,service,p,step)
        durations.append((time.perf_counter_ns()-begin)/1e6)
        success=action is not None and outcomes[step][action]
        ages=advance(ages,ttl,action,success,service)
        actual_ages=[a+service for a in actual_ages]
        if success: actual_ages[action]=service
        claim=valid(ages,ttl,required,guard)
        truth=valid(actual_ages,true_ttl,required,guard)
        claims+=claim; good+=claim and truth; false+=claim and not truth; missed+=truth and not claim
        sent+=action is not None
    return dict(method=method,seed=seed,valid_fraction=good/decisions,claimed_fraction=claims/decisions,
                false_valid_fraction=false/decisions,missed_valid_fraction=missed/decisions,sent_messages=sent,
                # Model 48B payload+16B header/request metadata, 8B ACK/attempt.
                modeled_bytes=sent*72,simulated_slots=decisions*service,
                scheduling_p50_ms=float(np.percentile(durations,50)),
                scheduling_p99_ms=float(np.percentile(durations,99)),scheduling_max_ms=max(durations))


def stress(n=10000):
    rng=random.Random(20261002); violations=optimistic=0
    for _ in range(n):
        d=rng.uniform(1,60); e=rng.uniform(0,.8); v=rng.uniform(.1,20); a=rng.uniform(0,4); clock=.05
        bound=lifetime(d,e,v,a,clock)
        t=bound*rng.uniform(0,1)
        # Actual unseen entrant starts no nearer than d-e; actual dynamics obey bounds.
        distance=d-rng.uniform(0,e); speed=rng.uniform(0,v); acc=rng.uniform(0,a)
        tau=t+clock
        violations+=speed*tau+.5*acc*tau*tau >= distance and bound>0
        # Deliberately underestimated speed/acceleration: same fastest entrant.
        wrong=lifetime(d,e,v*.5,a*.5,clock)
        tau=wrong+clock
        optimistic+=v*tau+.5*a*tau*tau > d-e+1e-9
    return dict(samples=n,bounded_model_violations=violations,underestimated_dynamics_violations=optimistic,
                scope='Analytic 1D model stress only; not detector calibration or vehicle collisions.')


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--seeds',type=int,default=500); parser.add_argument('--decisions',type=int,default=60)
    args=parser.parse_args(); args.out.mkdir(parents=True,exist_ok=False)
    rows=[]; start=time.perf_counter(); cold=[]
    for name,config in CONFIGS.items():
        for method in METHODS:
            solve.cache_clear()
            # Explicit cold first call. Subsequent calls include cache hits.
            t=time.perf_counter_ns()
            choose(method,tuple(t+1 for t in config['ttl']),config['ttl'],tuple(range(len(config['ttl']))),
                   config.get('guard',1),config.get('service',1),config.get('p',.9))
            cold.append(dict(config=name,method=method,cold_ms=(time.perf_counter_ns()-t)/1e6))
            for seed in range(args.seeds):
                rows.append(dict(config=name,**episode(method,config,seed,args.decisions)))
        print(json.dumps(dict(completed_config=name,episodes=len(rows),elapsed_s=time.perf_counter()-start)),flush=True)
    write(args.out/'per_episode.csv',rows);write(args.out/'cold_latency.csv',cold)
    rng=np.random.default_rng(20261001); summary=[]; comparisons=[]
    for name in CONFIGS:
        lookup={(r['method'],r['seed']):r for r in rows if r['config']==name}
        for method in METHODS:
            cells=[lookup[method,s] for s in range(args.seeds)]
            summary.append(dict(config=name,method=method,**{metric:float(np.mean([r[metric] for r in cells])) for metric in
                                ['valid_fraction','false_valid_fraction','claimed_fraction','sent_messages','modeled_bytes','scheduling_p99_ms']}))
        for baseline in METHODS:
            if baseline=='stochastic_mpc3': continue
            for metric in ['valid_fraction','false_valid_fraction']:
                x=np.array([lookup['stochastic_mpc3',s][metric]-lookup[baseline,s][metric] for s in range(args.seeds)])
                boot=x[rng.integers(0,len(x),(4000,len(x)))].mean(1)
                comparisons.append(dict(config=name,baseline=baseline,metric=metric,seeds=args.seeds,diff=x.mean(),ci_low=np.quantile(boot,.025),ci_high=np.quantile(boot,.975)))
    write(args.out/'summary.csv',summary);write(args.out/'comparisons.csv',comparisons)
    (args.out/'reachability_stress.json').write_text(json.dumps(stress(),indent=2)+'\n')
    manifest=dict(date='2026-10-01',host=socket.gethostname(),platform=platform.platform(),python=sys.version,
                  numpy=np.__version__,configs=CONFIGS,methods=METHODS,seeds=args.seeds,decisions=args.decisions,
                  episodes=len(rows),elapsed_s=time.perf_counter()-start,
                  code_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')},
                  protocol_sha256=hashlib.sha256(Path(__file__).with_name('PROTOCOL.md').read_bytes()).hexdigest(),
                  scope='Synthetic correct-free evidence; supplied TTLs; not a driving experiment. Latency has cold/warm-cache distinctions.')
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(done=True,episodes=len(rows),elapsed_s=manifest['elapsed_s'])),flush=True)


if __name__=='__main__':main()
