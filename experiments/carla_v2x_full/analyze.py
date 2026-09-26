#!/usr/bin/env python3
import argparse, csv, json
from collections import defaultdict
from pathlib import Path
import numpy as np


def ci(x, rng, n=2000):
    x=np.asarray(x,float)
    if not len(x): return (float('nan'),)*3
    means=np.empty(n)
    for i in range(n):means[i]=x[rng.integers(0,len(x),len(x))].mean()
    return float(x.mean()),float(np.percentile(means,2.5)),float(np.percentile(means,97.5))


def main():
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True);rows=[]
    with a.input.open() as f:
        for r in csv.DictReader(f):
            for k in ['seed','horizon_cycles','scheduled_messages','delivered_messages','useful_messages','dropped_or_late_messages','bytes_sent','valid_go_cycles']:
                r[k]=int(r[k])
            for k in ['progress_fraction','decision_delay_cycles','unsafe_go_fraction','useful_bytes_per_go']:
                r[k]=float(r[k])
            rows.append(r)
    groups=defaultdict(list)
    for r in rows:groups[(r['config'],r['scenario'],r['method'])].append(r)
    summaries=[]
    for key,items in sorted(groups.items()):
        config,scenario,method=key
        summaries.append(dict(config=config,scenario=scenario,method=method,n=len(items),
          progress_mean=np.mean([x['progress_fraction'] for x in items]),
          progress_std=np.std([x['progress_fraction'] for x in items],ddof=1),
          delay_mean=np.mean([x['decision_delay_cycles'] for x in items]),
          unsafe_mean=np.mean([x['unsafe_go_fraction'] for x in items]),
          bytes_mean=np.mean([x['bytes_sent'] for x in items]),
          delivered_mean=np.mean([x['delivered_messages'] for x in items]),
          useful_mean=np.mean([x['useful_messages'] for x in items])))
    with (a.out/'summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(summaries[0]));w.writeheader();w.writerows(summaries)
    comparisons=[];rng=np.random.default_rng(20260926)
    pairs=[('set_independent','coverage_greedy'),('set_independent','singleton_voi'),('set_joint','set_independent'),('set_joint','coverage_greedy'),('set_joint','singleton_voi')]
    for config in sorted({r['config'] for r in rows}):
      for scenario in sorted({r['scenario'] for r in rows}):
       for method,base in pairs:
        left={x['seed']:x for x in groups[(config,scenario,method)]};right={x['seed']:x for x in groups[(config,scenario,base)]};seeds=sorted(set(left)&set(right))
        pd=[left[s]['progress_fraction']-right[s]['progress_fraction'] for s in seeds]
        dd=[right[s]['decision_delay_cycles']-left[s]['decision_delay_cycles'] for s in seeds]
        pm,pl,ph=ci(pd,rng);dm,dl,dh=ci(dd,rng)
        comparisons.append(dict(config=config,scenario=scenario,method=method,baseline=base,n=len(seeds),progress_diff=pm,progress_ci_low=pl,progress_ci_high=ph,delay_improvement_cycles=dm,delay_ci_low=dl,delay_ci_high=dh,positive_progress_fraction=np.mean(np.asarray(pd)>0),tie_fraction=np.mean(np.asarray(pd)==0)))
    with (a.out/'paired_comparisons.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(comparisons[0]));w.writeheader();w.writerows(comparisons)
    actionable={'free','hazard_a','hazard_b','both_hazard'}
    overall=[]
    for config in sorted({r['config'] for r in rows}):
      for method,base in pairs:
        by_seed=defaultdict(list)
        for scenario in actionable:
            left={x['seed']:x for x in groups[(config,scenario,method)]};right={x['seed']:x for x in groups[(config,scenario,base)]}
            for seed in set(left)&set(right):by_seed[seed].append(left[seed]['progress_fraction']-right[seed]['progress_fraction'])
        values=[np.mean(v) for v in by_seed.values()];m,lo,hi=ci(values,rng)
        overall.append(dict(config=config,method=method,baseline=base,n_seeds=len(values),mean_progress_diff=m,ci_low=lo,ci_high=hi))
    with (a.out/'overall_comparisons.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(overall[0]));w.writeheader();w.writerows(overall)
    key={(x['config'],x['method'],x['baseline']):x for x in overall}
    independent_set=key[('independent','set_independent','coverage_greedy')]
    joint_contention=key[('contention','set_joint','set_independent')]
    regress=[]
    for config in ('ideal','independent'):
        regress.append(key[(config,'set_joint','set_independent')]['ci_low'] < -.01)
    verdict={
      'set_utility_supported_under_independent': independent_set['ci_low']>0,
      'joint_arrival_supported_under_contention': joint_contention['ci_low']>0,
      'joint_method_no_material_regression_ideal_independent':not any(regress),
      'pre_registered_interpretation':'Broad set-utility claim requires the first criterion. Joint-arrival claim requires the second without material regression.'}
    (a.out/'verdict.json').write_text(json.dumps(verdict,indent=2))
    print(json.dumps({'rows':len(rows),'groups':len(groups),'verdict':verdict,'selected_overall':{'independent_set_vs_coverage':independent_set,'contention_joint_vs_independent':joint_contention}},indent=2))


if __name__=='__main__':main()
