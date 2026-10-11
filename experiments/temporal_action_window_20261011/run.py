import argparse
from fractions import Fraction as F
import hashlib
import itertools
import json
from pathlib import Path
import platform
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiments/action_window_reference_20261011'))
import kernel as k

def advance(b,matrix,steps):
    for _ in range(steps):b=k.propagate(b,matrix)
    return b

def observe(b,model,o):
    w=tuple(v*k.likelihood(model,o,i) for i,v in enumerate(b))
    z=sum(w)
    assert z>0
    return tuple(v/z for v in w),z

def history_posterior(model,history):
    matrix=k.transition(model);b=k.PRIOR;prob=F(1)
    for index,o in enumerate(history):
        if index:b=advance(b,matrix,2)
        b,z=observe(b,model,o);prob*=z
    return b,prob

def audit_risk(b,matrix,length):
    # State augmentation explicitly accumulates conflict mass.
    bad=sum(b[i] for i in k.HAZARD)
    good={i:v for i,v in enumerate(b) if i not in k.HAZARD}
    for _ in range(length):
        nxt={i:F(0) for i in range(9) if i not in k.HAZARD}
        for i,v in good.items():
            for j,t in enumerate(matrix[i]):
                if j in k.HAZARD:bad+=v*t
                else:nxt[j]+=v*t
        good=nxt
    return bad

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
    freeze_path=Path(__file__).with_name('freeze.json')
    freeze=json.loads(freeze_path.read_text())
    for name,v in freeze['repo_files'].items():
        data=(ROOT/name).read_bytes()
        assert len(data)==v['bytes'] and hashlib.sha256(data).hexdigest()==v['sha256']
    t0=time.perf_counter_ns();histories=list(itertools.product(range(4),repeat=3))
    weights={};history_risks={};latest_risks={};timings=[]
    for m,model in enumerate(k.MODELS):
        matrix=k.transition(model)
        for last in range(4):
            b,_=observe(advance(k.PRIOR,matrix,4),model,last)
            for a in range(17):
                for h in (1,2,4):latest_risks[(m,last,a,h)]=k.first_hit(b,matrix,k.HAZARD,h)
                b=advance(b,matrix,1)
        for index,history in enumerate(histories):
            t=time.perf_counter_ns();b,z=history_posterior(model,history)
            timings.append(time.perf_counter_ns()-t);weights[(m,index)]=z
            for a in range(17):
                for h in (1,2,4):
                    risk=k.first_hit(b,matrix,k.HAZARD,h)
                    assert risk==audit_risk(b,matrix,h)
                    history_risks[(m,index,a,h)]=risk
                b=advance(b,matrix,1)
        assert sum(weights[(m,i)] for i in range(64))==1
    rows=[];groups=[];fees=[]
    for alpha in (F(1,100),F(1,20),F(1,10)):
        for h in (1,2,4):
            for a in range(17):
                decisions={}
                for index,history in enumerate(histories):
                    full=max(history_risks[(m,index,a,h)] for m in range(12))
                    last=max(latest_risks[(m,history[-1],a,h)] for m in range(12))
                    choices={'history':full<=alpha,'latest_only':last<=alpha}
                    decisions[index]=choices
                    rows.append(dict(history_index=index,length=h,age=a,alpha=str(alpha),
                                     robust_history_risk=str(full),robust_latest_risk=str(last),decisions=choices))
                for m in range(12):
                    for method in ('history','latest_only'):
                        accepted=sum(weights[(m,i)] for i in range(64) if decisions[i][method])
                        bad=sum(weights[(m,i)]*history_risks[(m,i,a,h)] for i in range(64) if decisions[i][method])
                        conditional=bad/accepted if accepted else None
                        assert conditional is None or conditional<=alpha
                        groups.append(dict(alpha=str(alpha),length=h,age=a,model=m,method=method,
                                           accepted_probability=str(accepted),conflict_mass=str(bad),
                                           selected_risk=None if conditional is None else str(conditional)))
    for alpha in (F(1,100),F(1,20),F(1,10)):
        for fee in (0,1,2):
            selected=[g for g in groups if g['alpha']==str(alpha) and g['age']>=fee]
            model_rows=[]
            for m in range(12):
                d={method:sum(F(g['accepted_probability']) for g in selected if g['model']==m and g['method']==method)/(3*(17-fee))
                   for method in ('history','latest_only')}
                model_rows.append(dict(model=m,history_acceptance=str(d['history']),
                                       latest_acceptance=str(d['latest_only']),difference=str(d['history']-d['latest_only'])))
            fees.append(dict(alpha=str(alpha),fee_ticks=fee,models=model_rows))
    summary=dict(query_count=len(rows),exact_history_model_queries=len(history_risks),
                 selected_risk_group_checks=len(groups),budget_violations=0,
                 history_accepted=sum(r['decisions']['history'] for r in rows),
                 latest_accepted=sum(r['decisions']['latest_only'] for r in rows),
                 history_gained=sum(r['decisions']['history'] and not r['decisions']['latest_only'] for r in rows),
                 history_lost=sum(not r['decisions']['history'] and r['decisions']['latest_only'] for r in rows))
    result=dict(schema=1,scope='synthetic exact known-family conditional per-action diagnostic',
                freeze_sha256=hashlib.sha256(freeze_path.read_bytes()).hexdigest(),
                acquisition_ticks=[0,2,4],source_reference_tick=4,
                histories=[list(h) for h in histories],
                joint_history_probabilities=[[str(weights[(m,i)]) for i in range(64)] for m in range(12)],
                query_decisions=rows,selection_audit=groups,fee_summaries=fees,summary=summary)
    (out/'scientific.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    timings.sort()
    (out/'runtime.json').write_text(json.dumps(dict(host=platform.node(),python=platform.python_version(),
         total_elapsed_ns=time.perf_counter_ns()-t0,history_filter_ns=dict(median=timings[len(timings)//2],p95=timings[int(.95*(len(timings)-1))],maximum=max(timings)),
         statement='exact reference measured runtime; additional acquisition/radio costs not measured; no WCET'),sort_keys=True,indent=2)+'\n')
    print(json.dumps(summary,sort_keys=True))

if __name__=='__main__':main()
