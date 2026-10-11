import argparse
import hashlib
import json
from pathlib import Path
import platform
import time
from fractions import Fraction as F
import kernel as k

def absorbing_risk(b,matrix,hazard,length):
    # Independent augmented-state recursion carries conflict mass explicitly.
    mass={i:p for i,p in enumerate(b) if i not in hazard}
    bad=sum(p for i,p in enumerate(b) if i in hazard)
    for _ in range(length):
        nxt={i:F(0) for i in range(len(b)) if i not in hazard}
        for i,p in mass.items():
            for j,t in enumerate(matrix[i]):
                if j in hazard:bad+=p*t
                else:nxt[j]+=p*t
        mass=nxt
    return bad

def frac(x):return str(x)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);args=ap.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
    source=Path(__file__).resolve().parent
    freeze=json.loads((source/'freeze.json').read_text())
    for name,receipt in freeze['files'].items():
        data=(source/name).read_bytes()
        assert len(data)==receipt['bytes'] and hashlib.sha256(data).hexdigest()==receipt['sha256']
    t0=time.perf_counter_ns();risks={};endpoints={};unions={};queries=[];timings=[]
    for observation in range(4):
        for length in (1,2,4):
            for model_index,model in enumerate(k.MODELS):
                matrix=k.transition(model);b=k.posterior(model,observation)
                for age in range(17):
                    t=time.perf_counter_ns()
                    risk=k.first_hit(b,matrix,k.HAZARD,length)
                    timings.append(time.perf_counter_ns()-t)
                    assert risk==absorbing_risk(b,matrix,k.HAZARD,length)
                    endpoint,union=k.marginal_bounds(b,matrix,k.HAZARD,length)
                    assert endpoint<=risk<=union
                    key=(observation,length,age,model_index)
                    risks[key],endpoints[key],unions[key]=risk,endpoint,union
                    b=k.propagate(b,matrix)
    nominal=k.MODELS.index((F(55,100),F(0),F(2,100)))
    profiles=[];fee_summary={str(f):{'eligible':0,'accepted':0} for f in (0,1,2)}
    for observation in range(4):
        for length in (1,2,4):
            true_risk=[max(risks[(observation,length,a,m)] for m in range(12)) for a in range(17)]
            for alpha in (F(1,100),F(1,20),F(1,10)):
                allowed=[r<=alpha for r in true_risk]
                prefix=[];valid=True
                for okay in allowed:
                    valid=valid and okay;prefix.append(valid)
                packets=[k.encode(allowed,observation,length,alpha,bitmap=b) for b in (False,True)]
                assert all(k.decode(p)['allowed']==allowed for p in packets)
                packet_names=[]
                for suffix,p in zip(('interval','bitmap'),packets):
                    name='o%d_h%d_a%s_%s.bin'%(observation,length,str(alpha).replace('/','-'),suffix)
                    (out/name).write_bytes(p);packet_names.append(name)
                profiles.append(dict(observation=observation,length=length,alpha=frac(alpha),
                                     valid_start_age_segments=k.segments(allowed),
                                     prefix_last_age=max((a for a,v in enumerate(prefix) if v),default=-1),
                                     interval_bytes=len(packets[0]),bitmap_bytes=len(packets[1]),packets=packet_names))
                for age in range(17):
                    model_risks=[risks[(observation,length,age,m)] for m in range(12)]
                    decisions=dict(robust_window=allowed[age],full_curve=allowed[age],
                                   robust_union=max(unions[(observation,length,age,m)] for m in range(12))<=alpha,
                                   robust_support=true_risk[age]==0,robust_prefix=prefix[age],
                                   nominal_window=model_risks[nominal]<=alpha,
                                   endpoint_only=max(endpoints[(observation,length,age,m)] for m in range(12))<=alpha)
                    queries.append(dict(observation=observation,length=length,alpha=frac(alpha),age=age,
                                        risks=[frac(r) for r in model_risks],decisions=decisions))
                    for fee in (0,1,2):
                        if age<fee:continue
                        fee_summary[str(fee)]['eligible']+=1
                        now=1_000_000+(age-fee)*50_000
                        for packet in packets:
                            assert k.admissible(packet,k.context_digest(observation),length,alpha,now,fee*50_000)==allowed[age]
                        fee_summary[str(fee)]['accepted']+=int(allowed[age])
    methods={}
    for method in queries[0]['decisions']:
        accepted=[q for q in queries if q['decisions'][method]]
        maximum=max((max(F(r) for r in q['risks']) for q in accepted),default=F(0))
        methods[method]=dict(accepted=len(accepted),
                            max_declared_model_risk=frac(maximum),
                            budget_violating_queries=sum(max(F(r) for r in q['risks'])>F(q['alpha']) for q in accepted),
                            robust_safe_queries_lost=sum(q['decisions']['robust_window'] and not q['decisions'][method] for q in queries))
    result=dict(schema=1,scope='synthetic finite discrete per-action conditional model diagnostic',
                freeze_sha256=hashlib.sha256((source/'freeze.json').read_bytes()).hexdigest(),
                models=[[frac(x) for x in m] for m in k.MODELS],queries=queries,profiles=profiles,
                summary=dict(query_count=len(queries),exact_model_query_checks=len(risks),
                             methods=methods,fee_summary=fee_summary,
                             interval_total_bytes=sum(p['interval_bytes'] for p in profiles),
                             bitmap_total_bytes=sum(p['bitmap_bytes'] for p in profiles),
                             nonprefix_profiles=sum(any(lo>p['prefix_last_age'] for lo,hi in p['valid_start_age_segments']) for p in profiles)))
    (out/'scientific.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    timings.sort()
    runtime=dict(host=platform.node(),python=platform.python_version(),
                 total_elapsed_ns=time.perf_counter_ns()-t0,
                 exact_query_ns=dict(median=timings[len(timings)//2],p95=timings[int(.95*(len(timings)-1))],maximum=max(timings)),
                 statement='measured rational reference computation; not production latency or WCET')
    (out/'runtime.json').write_text(json.dumps(runtime,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result['summary'],sort_keys=True))

if __name__=='__main__':main()
