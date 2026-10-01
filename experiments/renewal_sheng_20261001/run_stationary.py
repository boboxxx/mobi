#!/usr/bin/env python3
"""Post-diagnostic reference supplement; keeps the original run unchanged."""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import time
import numpy as np
import run_suite
import stationary_reference


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seeds',type=int,default=500);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    original=run_suite.choose
    def choose(method,ages,ttl,required,guard,service,p,step):
        if method=='stationary_discounted':return stationary_reference.choose(ages,ttl,required,guard,service,p)
        return original(method,ages,ttl,required,guard,service,p,step)
    run_suite.choose=choose;rows=[];models=[];start=time.perf_counter()
    try:
        for name,config in run_suite.CONFIGS.items():
            ttl=config['ttl'];required=tuple(range(len(ttl)))
            begin=time.perf_counter()
            _,diagnostic=stationary_reference.build(ttl,required,config.get('guard',1),config.get('service',1),config.get('p',.9))
            models.append(dict(config=name,cold_s=time.perf_counter()-begin,**diagnostic))
            for seed in range(a.seeds):
                rows.append(dict(config=name,**run_suite.episode('stationary_discounted',config,seed,60)))
            print(json.dumps(dict(config=name,episodes=len(rows))),flush=True)
    finally:run_suite.choose=original
    run_suite.write(a.out/'per_episode.csv',rows);run_suite.write(a.out/'models.csv',models)
    manifest=dict(host=socket.gethostname(),seeds=a.seeds,decisions=60,episodes=len(rows),elapsed_s=time.perf_counter()-start,
                  status='Supplement added after observing finite-horizon end-effect; not part of initial frozen comparison.',
                  scope='Discounted stationary optimum of the small supplied-TTL model only; current required set held fixed in planning.',
                  source_sha256={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['run_stationary.py','stationary_reference.py','run_suite.py','scheduler.py']})
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
