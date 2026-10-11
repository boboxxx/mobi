"""Post-result independent probability reconstruction; not a new trial."""
from fractions import Fraction as F
import argparse
import hashlib
import itertools
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MODELS=list(itertools.product((F(35,100),F(55,100),F(75,100)),(F(0),F(15,100)),(F(2,100),F(12,100))))
PRIOR=[F(4,10),F(3,10),F(2,10),F(1,10)]+[F(0)]*5

def update(v,model):
    p,r,e=model;new=[F(0)]*9
    for state,mass in enumerate(v):
        if state==8:new[0]+=mass*r;new[8]+=mass*(1-r)
        else:new[state]+=mass*(1-p);new[state+1]+=mass*p
    return new

def measurement(v,model,obs):
    e=model[2];out=[]
    for i,mass in enumerate(v):
        correct=0 if i<=1 else 1 if i<=3 else 2
        l=F(2,5) if obs==3 else F(3,5)*(1-e if obs==correct else e*F(1,2))
        out.append(mass*l)
    return out

def normalized(v):
    z=sum(v);assert z>0
    return [x/z for x in v],z

def crossing(v,model,h):
    # Accumulated absorption, avoiding production matrix products.
    bad=v[4]+v[5];good=list(v);good[4]=good[5]=F(0)
    for _ in range(h):
        good=update(good,model);bad+=good[4]+good[5];good[4]=good[5]=F(0)
    assert sum(good)+bad==1
    return bad

def load(unit,host):
    p=ROOT/'results'/unit/host/'scientific.json'
    return json.loads(p.read_text()),{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--host',choices=['local','sheng'],required=True);ap.add_argument('--out',required=True);args=ap.parse_args()
    first,receipt1=load('action_window_reference_20261011',args.host)
    second,receipt2=load('temporal_action_window_20261011',args.host)
    one={};full={};last={};weights={};histories=list(itertools.product(range(4),repeat=3))
    for m,model in enumerate(MODELS):
        for obs in range(4):
            b,_=normalized(measurement(PRIOR,model,obs))
            for age in range(17):
                for h in (1,2,4):one[(m,obs,age,h)]=crossing(b,model,h)
                b=update(b,model)
            b=list(PRIOR)
            for _ in range(4):b=update(b,model)
            b,_=normalized(measurement(b,model,obs))
            for age in range(17):
                for h in (1,2,4):last[(m,obs,age,h)]=crossing(b,model,h)
                b=update(b,model)
        for index,history in enumerate(histories):
            raw=list(PRIOR)
            for i,obs in enumerate(history):
                if i:
                    for _ in range(2):raw=update(raw,model)
                raw=measurement(raw,model,obs)
            b,z=normalized(raw);weights[(m,index)]=z
            for age in range(17):
                for h in (1,2,4):full[(m,index,age,h)]=crossing(b,model,h)
                b=update(b,model)
        assert sum(weights[(m,i)] for i in range(64))==1
        assert [str(weights[(m,i)]) for i in range(64)]==second['joint_history_probabilities'][m]
    assert len(first['queries'])==612 and len(second['query_decisions'])==9792
    for q in first['queries']:
        risks=[one[(m,q['observation'],q['age'],q['length'])] for m in range(12)]
        assert [str(r) for r in risks]==q['risks']
        assert q['decisions']['robust_window']==(max(risks)<=F(q['alpha']))
    checked=[]
    for q in second['query_decisions']:
        index=q['history_index'];a=q['age'];h=q['length'];alpha=F(q['alpha'])
        values=[full[(m,index,a,h)] for m in range(12)]
        bound=max(values);which=[m for m,r in enumerate(values) if r==bound]
        latest=max(last[(m,histories[index][-1],a,h)] for m in range(12))
        assert str(bound)==q['robust_history_risk'] and str(latest)==q['robust_latest_risk']
        assert q['decisions']=={'history':bound<=alpha,'latest_only':latest<=alpha}
        checked.append((bound,index,a,h,which))
    best=min(checked,key=lambda x:(x[0],x[1],x[2],x[3]))
    witness=dict(minimum_worst_model_risk=str(best[0]),history=list(histories[best[1]]),
                 age=best[2],length=best[3],worst_model_indices=best[4],
                 models=[[str(x) for x in MODELS[m]] for m in best[4]],
                 largest_tested_budget='1/10',all_queries_infeasible_at_tested_budgets=best[0]>F(1,10))
    # Oracle knows the state at acquisition tick4, not at its future use time.
    # Only states0..7 are reachable at tick4 from the declared initial prior.
    oracle={};oracle_rows=[]
    for state in range(8):
        states={m:[F(int(i==state)) for i in range(9)] for m in range(12)}
        for age in range(17):
            for h in (1,2,4):oracle[(state,age,h)]=max(crossing(states[m],MODELS[m],h) for m in range(12))
            for m in range(12):states[m]=update(states[m],MODELS[m])
    for alpha in (F(1,100),F(1,20),F(1,10)):
        for fee in (0,1,2):
            eligible=[(s,a,h) for s in range(8) for a in range(fee,17) for h in (1,2,4)]
            oracle_rows.append(dict(alpha=str(alpha),fee_ticks=fee,query_count=len(eligible),
                                    accepted=sum(oracle[key]<=alpha for key in eligible),
                                    statement='full source-state oracle diagnostic; not a sensor or system result'))
    audit=dict(status='PASS',scope='independent exact reconstruction plus post-result explanatory oracle',
               input_receipts=[receipt1,receipt2],first_model_risks_checked=len(one),
               temporal_model_risks_checked=len(full),temporal_decisions_checked=len(checked),
               minimum_risk_witness=witness,oracle_reference=oracle_rows,
               interpretation='impossibility restricted to fixed action, age grid, known model family and per-history worst-model criterion; no global task impossibility')
    Path(args.out).write_text(json.dumps(audit,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':'PASS','witness':witness,'oracle_reference':oracle_rows},sort_keys=True))

if __name__=='__main__':main()
