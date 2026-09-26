#!/usr/bin/env python3
import argparse,csv,json,pathlib,time
import numpy as np
from core import CONFIGS, run_episode, select_messages


NOISE={
 'perfect':(0,0),
 'nominal':(.01,.03),
 'conservative_error':(.01,.10),
 'false_free_stress':(.05,.03),
}
METHODS=('coverage_greedy','singleton_voi','set_independent','set_joint')
SCENARIOS=('free','hazard_a','hazard_b','both_hazard')


def main():
 p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=500);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);rows=[];start=time.perf_counter()
 for config in ('independent','contention'):
  for scenario in SCENARIOS:
   for noise,(ff,fo) in NOISE.items():
    for seed in range(a.seeds):
     for method in METHODS:
      r=run_episode(method,config,scenario,seed*1000003+SCENARIOS.index(scenario)*101+list(NOISE).index(noise)*17,false_free=ff,false_occupied=fo);r['noise']=noise;rows.append(r)
 with (a.out/'per_episode.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 summary=[]
 for config in ('independent','contention'):
  for scenario in SCENARIOS:
   for noise in NOISE:
    for method in METHODS:
     x=[r for r in rows if (r['config'],r['scenario'],r['noise'],r['method'])==(config,scenario,noise,method)]
     summary.append(dict(config=config,scenario=scenario,noise=noise,method=method,n=len(x),progress_mean=np.mean([q['progress_fraction'] for q in x]),unsafe_go_mean=np.mean([q['unsafe_go_fraction'] for q in x]),delay_mean=np.mean([q['decision_delay_cycles'] for q in x]),bytes_mean=np.mean([q['bytes_sent'] for q in x])))
 with (a.out/'summary.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
 # Fixed-input scheduler microbenchmark; excludes networking and sensor work.
 evidence_states=[{}, {'A':('free',0,'A0')},{'B':('free',0,'B0')},{'A':('free',0,'A0'),'B':('free',0,'B0')}]
 bench=[]
 for method in METHODS:
  samples=[]
  for i in range(20000):
   e=evidence_states[i%len(evidence_states)];t=time.perf_counter_ns();select_messages(method,e,i%6,CONFIGS['contention']);samples.append((time.perf_counter_ns()-t)/1000)
  bench.append(dict(method=method,calls=len(samples),mean_us=np.mean(samples),p95_us=np.percentile(samples,95),p99_us=np.percentile(samples,99),max_us=np.max(samples)))
 with (a.out/'scheduler_latency.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(bench[0]));w.writeheader();w.writerows(bench)
 manifest={'rows':len(rows),'seeds':a.seeds,'noise':NOISE,'methods':METHODS,'scenarios':SCENARIOS,'configs':['independent','contention'],'elapsed_seconds':time.perf_counter()-start}
 (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest))


if __name__=='__main__':main()
