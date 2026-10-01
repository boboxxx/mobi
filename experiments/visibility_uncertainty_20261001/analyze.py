#!/usr/bin/env python3
import argparse,collections,csv,hashlib,json
from pathlib import Path
import numpy as np


def read(path):
    return list(csv.DictReader(path.open()))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--capture',type=Path,required=True)
    ap.add_argument('--no-plots',action='store_true');a=ap.parse_args();src=Path(__file__).parent
    initial=json.loads((a.results/'manifest.json').read_text());wm=json.loads((a.results/'weighted/manifest.json').read_text())
    lm=json.loads((a.results/'local/manifest.json').read_text());sm=json.loads((a.results/'sensitivity/manifest.json').read_text())
    for m in [initial,wm,lm,sm]:
        for name,digest in m['source_sha256'].items():assert hashlib.sha256((src/name).read_bytes()).hexdigest()==digest,name
    for name,digest in initial['dependency_sha256'].items():
        assert hashlib.sha256((src.parent/'visibility_certificate_20261001'/name).read_bytes()).hexdigest()==digest,name
    for name,digest in initial['input_sha256'].items():
        assert hashlib.sha256((a.capture/'clouds'/name).read_bytes()).hexdigest()==digest,name
    for m,name in [(initial,'PROTOCOL.md'),(wm,'WEIGHTED_FOLLOWUP.md')]:
        assert hashlib.sha256((src/name).read_bytes()).hexdigest()==m['protocol_sha256']
    assert hashlib.sha256((src/'LARGER_ERRORS.md').read_bytes()).hexdigest()==sm['protocol_sha256']
    for m in [lm,sm]:assert hashlib.sha256((a.results/'weighted/weighted.csv').read_bytes()).hexdigest()==m['reference_sha256']
    rows=read(a.results/'projection_scan_audit.csv');weighted=read(a.results/'weighted/weighted.csv')
    assert len(rows)==720 and len(weighted)==288
    assert all(not (float(r['validity_s'])>0) for r in rows if '_near_' in r['id'])
    assert all(r['false_actual_center_exclusion']=='False' for r in weighted)
    assert all(float(r['validity_s'])+1e-10>=float(r['best_uniform_ttl_s']) for r in weighted)
    assert all(float(r['validity_s'])==0 for r in weighted if '_near_' in r['id'])
    pert=read(a.results/'box_perturbations.csv');assert sum(int(r['draws']) for r in pert)==100000
    assert sum(int(r['violations']) for r in pert)==0
    local=read(a.results/'local/local_comparison.csv');sensitivity=read(a.results/'sensitivity/sensitivity.csv')
    assert len(local)==288 and max(float(r['max_abs_error_s']) for r in local)<1e-10
    assert len(sensitivity)==576 and all(r['monotonicity_violation']=='False' for r in sensitivity)
    assert all(float(r['validity_s'])==0 for r in sensitivity if '_near_' in r['id'])
    key=lambda r:tuple(r[k] for k in ['id','scan_period_s','end_phase_rad','model','step_m'])
    reference_by_key={key(r):r for r in weighted}
    assert len(reference_by_key)==288 and {key(r) for r in local}==set(reference_by_key)
    for r in local:
        reference=reference_by_key[key(r)]
        for value in ['validity_s','best_uniform_ttl_s']:
            assert abs(float(r[value])-float(reference[value]))<1e-10
    for e in ['0.01','0.02']:
        subset=[r for r in sensitivity if r['input_box_m']==e]
        assert len(subset)==288 and {key(r) for r in subset}==set(reference_by_key)
        for r in subset:
            for value in ['validity_s','best_uniform_ttl_s']:
                assert float(r[value])<=float(reference_by_key[key(r)][value])+1e-10
    def keep(r):return r['model']=='vehicle_core' or r['step_m']=='0.05'
    local_groups=collections.defaultdict(list)
    for r in local:
        if keep(r):local_groups[(r['id'],r['scan_period_s'],r['end_phase_rad'])].append(r)
    joint_local=[sum(float(r['combined_local_ms']) for r in rs) for rs in local_groups.values()]
    base={(r['id'],r['scan_period_s'],r['end_phase_rad'],r['model']):r for r in rows if r['method']=='individual_age' and keep(r)}
    groups=collections.defaultdict(list)
    for r in weighted:
        if keep(r):groups[(r['id'],r['scan_period_s'],r['end_phase_rad'])].append(r)
    merged=[]
    for key,rs in sorted(groups.items()):
        assert len(rs)==2
        merged.append(dict(id=key[0],scan_period_s=float(key[1]),end_phase_rad=float(key[2]),
                           fixed_cap_ttl_s=min(float(base[key+(r['model'],)]['validity_s']) for r in rs),
                           best_uniform_ttl_s=min(float(r['best_uniform_ttl_s']) for r in rs),
                           heterogeneous_ttl_s=min(float(r['validity_s']) for r in rs),
                           heterogeneous_cpu_ms=sum(float(r['certificate_ms']) for r in rs),
                           uniform_sweep_cpu_ms=sum(float(r['uniform_sweep_ms']) for r in rs)))
    assert len(merged)==96
    with (a.results/'joint_comparison.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(merged[0]),lineterminator='\n');w.writeheader();w.writerows(merged)
    by_period={}
    for period in [.02,.05]:
        rs=[r for r in merged if r['scan_period_s']==period]
        by_period[str(period)]=dict(cases=len(rs),
             fixed_positive=sum(r['fixed_cap_ttl_s']>0 for r in rs),uniform_positive=sum(r['best_uniform_ttl_s']>0 for r in rs),
             heterogeneous_positive=sum(r['heterogeneous_ttl_s']>0 for r in rs),
             fixed_200ms=sum(r['fixed_cap_ttl_s']>=.2 for r in rs),uniform_200ms=sum(r['best_uniform_ttl_s']>=.2 for r in rs),
             heterogeneous_200ms=sum(r['heterogeneous_ttl_s']>=.2 for r in rs),
             weighted_strict_gain_cases=sum(r['heterogeneous_ttl_s']>r['best_uniform_ttl_s']+1e-10 for r in rs),
             max_gain_s=max(r['heterogeneous_ttl_s']-r['best_uniform_ttl_s'] for r in rs))
    larger={}
    for error in [.01,.02]:
        for period in [.02,.05]:
            grouped=collections.defaultdict(list)
            for r in sensitivity:
                if float(r['input_box_m'])==error and float(r['scan_period_s'])==period and keep(r):
                    grouped[(r['id'],r['end_phase_rad'])].append(r)
            assert len(grouped)==48 and all(len(rs)==2 for rs in grouped.values())
            pairs=[(min(float(r['validity_s']) for r in rs),min(float(r['best_uniform_ttl_s']) for r in rs)) for rs in grouped.values()]
            larger['%s:%s'%(error,period)]=dict(cases=48,heterogeneous_positive=sum(x>0 for x,y in pairs),
                 uniform_positive=sum(y>0 for x,y in pairs),heterogeneous_200ms=sum(x>=.2 for x,y in pairs),uniform_200ms=sum(y>=.2 for x,y in pairs))
    summary=dict(validation='passed',box_draws=100000,box_violations=0,hash_checked_clouds=12,
                 primary_comparison_rows=1008,local_equivalence_cases=288,sensitivity_rows=576,joint_cases=96,by_period=by_period,
                 local_max_abs_error_s=lm['max_abs_error_s'],combined_geometry_speed_ratio_median=lm['median_combined_speed_ratio'],
                 combined_local_ms_median=lm['local_ms_median'],combined_local_ms_max=lm['local_ms_max'],larger_errors=larger,
                 joint_combined_local_ms_median=float(np.median(joint_local)),joint_combined_local_ms_max=max(joint_local),
                 heterogeneous_cpu_ms_median=float(np.median([r['heterogeneous_cpu_ms'] for r in merged])),
                 heterogeneous_cpu_ms_max=max(r['heterogeneous_cpu_ms'] for r in merged),
                 scope='Geometric TTL at hypothetical common scan time. No packet/transport/action latency budget is evaluated by these counts.')
    (a.results/'analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
    if not a.no_plots:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
        fig,axs=plt.subplots(1,2,figsize=(11,4))
        for ax,period in zip(axs,[.02,.05]):
            rs=[r for r in merged if r['scan_period_s']==period]
            x=np.array([r['best_uniform_ttl_s'] for r in rs])*1000;y=np.array([r['heterogeneous_ttl_s'] for r in rs])*1000
            ax.scatter(x,y,s=32,alpha=.65,color='#267e79')
            limit=max(300,max(y)*1.1);ax.plot([0,limit],[0,limit],ls='--',color='#8b8b8b')
            ax.set(xlim=(-10,limit),ylim=(-10,limit),xlabel='Best uniform-bound expiry (ms)',ylabel='Per-ray-bound expiry (ms)',
                   title='%d ms hypothetical scan; 48 cases'%round(period*1000))
        fig.suptitle('Same static rays and supplied bounds; two required classes; overlapping cases')
        fig.tight_layout();fig.savefig(a.results/'comparison.png',dpi=180);fig.savefig(a.results/'comparison.pdf');plt.close(fig)
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
