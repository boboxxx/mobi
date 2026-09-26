#!/usr/bin/env python3
import argparse, csv, hashlib, json, pathlib, time
from core import CONFIGS, METHODS, run_episode

SCENARIOS=("free","hazard_a","hazard_b","both_hazard","permanent_block")


def main():
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=1000);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    rows=[];start=time.perf_counter()
    for config in CONFIGS:
        for scenario in SCENARIOS:
            for seed in range(a.seeds):
                for method in METHODS:
                    paired_seed=10_000_019*seed+101*list(CONFIGS).index(config)+17*SCENARIOS.index(scenario)
                    rows.append(run_episode(method,config,scenario,paired_seed))
    with (a.out/'per_episode.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    manifest={'seeds':a.seeds,'rows':len(rows),'configs':list(CONFIGS),'scenarios':list(SCENARIOS),'methods':list(METHODS),'elapsed_seconds':time.perf_counter()-start,'script_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'core_sha256':hashlib.sha256(pathlib.Path(__file__).with_name('core.py').read_bytes()).hexdigest()}
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest))


if __name__=='__main__':main()
