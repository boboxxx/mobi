#!/usr/bin/env python3
import argparse,csv,json
from collections import defaultdict
from pathlib import Path
import numpy as np


def boot(x,rng,n=3000):
 a=np.asarray(x,float);m=np.asarray([a[rng.integers(0,len(a),len(a))].mean() for _ in range(n)]);return float(a.mean()),float(np.percentile(m,2.5)),float(np.percentile(m,97.5))


def main():
 p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args();rows=[]
 with (a.root/'per_episode.csv').open() as f:
  for r in csv.DictReader(f):
   for k in ['seed']:r[k]=int(r[k])
   for k in ['progress_fraction','unsafe_go_fraction','decision_delay_cycles']:r[k]=float(r[k])
   rows.append(r)
 g=defaultdict(list)
 for r in rows:g[(r['config'],r['scenario'],r['noise'],r['method'])].append(r)
 out=[];rng=np.random.default_rng(20260926)
 for config in ('independent','contention'):
  for noise in ('perfect','nominal','conservative_error','false_free_stress'):
   for method in ('coverage_greedy','singleton_voi','set_independent','set_joint'):
    cells=[x for scenario in ('free','hazard_a','hazard_b','both_hazard') for x in g[(config,scenario,noise,method)]]
    out.append(dict(config=config,noise=noise,method=method,n=len(cells),progress_mean=np.mean([x['progress_fraction'] for x in cells]),unsafe_go_mean=np.mean([x['unsafe_go_fraction'] for x in cells]),delay_mean=np.mean([x['decision_delay_cycles'] for x in cells])))
 with (a.root/'aggregate.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
 comparisons=[]
 for config in ('independent','contention'):
  for noise in ('perfect','nominal','conservative_error','false_free_stress'):
   for method,base in [('set_independent','coverage_greedy'),('set_joint','set_independent')]:
    diffs=[];unsafe=[]
    for scenario in ('free','hazard_a','hazard_b','both_hazard'):
     l={x['seed']:x for x in g[(config,scenario,noise,method)]};b={x['seed']:x for x in g[(config,scenario,noise,base)]}
     for seed in set(l)&set(b):diffs.append(l[seed]['progress_fraction']-b[seed]['progress_fraction']);unsafe.append(l[seed]['unsafe_go_fraction']-b[seed]['unsafe_go_fraction'])
    m,lo,hi=boot(diffs,rng);u,ul,uh=boot(unsafe,rng);comparisons.append(dict(config=config,noise=noise,method=method,baseline=base,n=len(diffs),progress_diff=m,progress_ci_low=lo,progress_ci_high=hi,unsafe_diff=u,unsafe_ci_low=ul,unsafe_ci_high=uh))
 with (a.root/'paired_comparisons.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(comparisons[0]));w.writeheader();w.writerows(comparisons)
 with (a.root/'scheduler_latency.csv').open() as f:lat=list(csv.DictReader(f))
 result={'rows':len(rows),'maximum_scheduler_p99_us':max(float(x['p99_us']) for x in lat),'maximum_scheduler_max_us':max(float(x['max_us']) for x in lat),'false_free_stress_unsafe':{x['config']+'__'+x['method']:x['unsafe_go_mean'] for x in out if x['noise']=='false_free_stress'},'comparisons':comparisons}
 (a.root/'analysis.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='comparisons'},indent=2))


if __name__=='__main__':main()
