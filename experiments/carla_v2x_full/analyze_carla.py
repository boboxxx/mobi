#!/usr/bin/env python3
import argparse,csv,json
from collections import defaultdict
from pathlib import Path
import numpy as np


def bootstrap(values,rng,n=5000):
    a=np.asarray(values,float);means=np.asarray([a[rng.integers(0,len(a),len(a))].mean() for _ in range(n)])
    return float(a.mean()),float(np.percentile(means,2.5)),float(np.percentile(means,97.5))


def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    with (a.root/'summary.csv').open() as f:rows=list(csv.DictReader(f))
    numeric=['seed','distance_m','clearance_to_go_s','wait_fraction','bytes_sent','scheduled_messages','delivered_messages','useful_messages','dropped_or_late_messages','collisions','loop_p95_ms','loop_p99_ms','loop_max_ms','stale_sensor_frames','free_observation_fraction_A','free_observation_fraction_B']
    for r in rows:
        for k in numeric:r[k]=float(r[k])
    groups=defaultdict(list)
    for r in rows:groups[(r['config'],r['scenario'],r['method'])].append(r)
    summary=[]
    for key,items in sorted(groups.items()):
        d={'config':key[0],'scenario':key[1],'method':key[2],'n':len(items)}
        for metric in ['distance_m','clearance_to_go_s','wait_fraction','bytes_sent','delivered_messages','collisions','loop_p95_ms','loop_p99_ms']:
            d[metric+'_mean']=float(np.mean([x[metric] for x in items]));d[metric+'_std']=float(np.std([x[metric] for x in items],ddof=1)) if len(items)>1 else 0
        summary.append(d)
    with (a.out/'summary.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
    comparisons=[];rng=np.random.default_rng(20260926);pairs=[('set_independent','coverage_greedy'),('set_independent','singleton_voi'),('set_joint','set_independent'),('set_joint','coverage_greedy'),('set_joint','singleton_voi')]
    for config in ('independent','contention'):
      for scenario in ('free','hazard_a'):
       for method,base in pairs:
        left={int(x['seed']):x for x in groups[(config,scenario,method)]};right={int(x['seed']):x for x in groups[(config,scenario,base)]};seeds=sorted(set(left)&set(right))
        dd=[left[s]['distance_m']-right[s]['distance_m'] for s in seeds];delay=[right[s]['clearance_to_go_s']-left[s]['clearance_to_go_s'] for s in seeds]
        dm,dl,dh=bootstrap(dd,rng);tm,tl,th=bootstrap(delay,rng)
        comparisons.append(dict(config=config,scenario=scenario,method=method,baseline=base,n=len(seeds),distance_diff_m=dm,distance_ci_low=dl,distance_ci_high=dh,delay_improvement_s=tm,delay_ci_low=tl,delay_ci_high=th))
    with (a.out/'paired_comparisons.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(comparisons[0]));w.writeheader();w.writerows(comparisons)
    checks={
      'manifest_completed':json.loads((a.root/'manifest.json').read_text())['status']=='completed',
      'expected_140_episodes':len(rows)==140,
      'all_status_completed':all(r['status']=='completed' for r in rows),
      'no_stale_sensor_frames':all(r['stale_sensor_frames']==0 for r in rows),
      'free_scenario_sensor_free':all(r['free_observation_fraction_A']==1 and r['free_observation_fraction_B']==1 for r in rows if r['scenario']=='free'),
      'zero_recorded_collisions':sum(r['collisions'] for r in rows)==0,
      'same_script_hash':len({json.loads((a.root/'manifest.json').read_text())['script_sha256']})==1,
    }
    hazard_files=list((a.root/'episodes').glob('*__hazard_a__*.csv'));transition=[]
    for path in hazard_files:
        with path.open() as f:frames=list(csv.DictReader(f))
        before=[x for x in frames if float(x['sim_time'])<2.5];after=[x for x in frames if float(x['sim_time'])>=2.6]
        transition.append(all(x['obs_A']=='occupied' and int(x['points_A'])>=3 for x in before) and all(x['obs_A']=='free' and int(x['points_A'])==0 for x in after))
    checks['all_hazard_sensor_transitions_valid']=len(transition)==70 and all(transition)
    target={(x['config'],x['scenario'],x['method'],x['baseline']):x for x in comparisons}
    cont=[target[('contention',s,'set_joint','set_independent')] for s in ('free','hazard_a')]
    indep=[target[('independent',s,'set_joint','set_independent')] for s in ('free','hazard_a')]
    verdict={'closed_loop_joint_better_under_contention_both_scenarios':all(x['distance_ci_low']>0 for x in cont),'closed_loop_no_material_regression_independent':all(x['distance_ci_low']>=-.25 for x in indep),'recorded_collisions':int(sum(r['collisions'] for r in rows)),'caution':'Five paired seeds and a controlled corridor do not establish natural-scene safety.'}
    result={'checks':checks,'all_checks_passed':all(checks.values()),'verdict':verdict,'selected_comparisons':{'contention':cont,'independent':indep}}
    (a.out/'validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    if not result['all_checks_passed']:raise SystemExit(1)


if __name__=='__main__':main()
