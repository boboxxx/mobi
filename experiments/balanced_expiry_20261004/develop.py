#!/usr/bin/env python3
"""A finite post-test development probe on published prior data; no holdout claim."""
import hashlib, json
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
from method import ROOT, FAMILIES, conformity, infer
from scores import load_models, predictions
from conditional import certificate, zero_failure_required

E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
OLD=ROOT/'results/prospective_hypotheses_20261004'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):p.write_text(json.dumps(d,separators=(',',':'))+'\n')
def pair(v):return [v.numerator,v.denominator]
def quantile(v):
    v=sorted(v);pos=F((len(v)-1)*95,100);j=pos.numerator//pos.denominator
    return float(v[j]+(v[min(j+1,len(v)-1)]-v[j])*(pos-j))
def main():
    frozen=read(E/'freeze.json')
    for section in ('sources','inputs'):
        for n,h in frozen[section].items():assert sha(ROOT/n)==h,n
    assert not (P/'development_sheng.json').exists()
    data=read(OLD/'qualification_sheng.json');models=load_models();ep_scores=defaultdict(lambda:F(0));rows=[]
    for i,r in enumerate(data['rows']):
        pred,centre=predictions(r['hulls_cm'],r['layout'],r['blueprint'],models)
        assert pred==r['prediction'] and centre==r['ridge_center_um']
        ss={m:conformity(r['hulls_cm'],data['catalog'][r['blueprint']],pred,r['true_xy'],m) for m in FAMILIES}
        rows.append(dict(id=r['id'],episode_id=r['episode_id'],blueprint=r['blueprint'],split=r['split'],scores={m:pair(s) for m,s in ss.items()}))
        for m,s in ss.items():ep_scores[r['episode_id'],m]=max(ep_scores[r['episode_id'],m],s)
        if (i+1)%500==0:print('development scored',i+1,flush=True)
    registry={}
    for bp in data['catalog']:
        eps=[e['episode'] for e in data['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='calibration'];assert len(eps)==125
        registry[bp]={m:pair(max(ep_scores[e['id'],m] for e in eps)) for m in FAMILIES}
    source={r['id']:r for r in data['rows']}
    for row in rows:
        if row['split']!='test':continue
        r=source[row['id']];row['methods']={m:infer(r['hulls_cm'],data['catalog'][r['blueprint']],r['prediction'],F(*registry[r['blueprint']][m]),m) for m in FAMILIES}
    summary=[]
    for bp in data['catalog']:
        eps=[e['episode'] for e in data['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='test'];rr=[r for r in rows if r['split']=='test' and r['blueprint']==bp]
        for m in FAMILIES:
            gaps=[];over=[];above=below=0
            for row in rr:
                original=source[row['id']];v=row['methods'][m];ages=v['lower_us'] if v['status']=='bounded' else [0,0]
                reference=original['geometries']['local_mean' if m=='balanced_mean' else 'local_modes'];old_ages=reference['lower_us'] if reference['status']=='bounded' else [0,0]
                for j,(age,oracle,old) in enumerate(zip(ages,original['oracle_us'],old_ages)):
                    gaps.append(max(0,oracle-age));above+=age>old;below+=age<old
                    if age>oracle:over.append([row['id'],j,age,oracle])
            excluded=[e['id'] for e in eps if ep_scores[e['id'],m]>F(*registry[bp][m])]
            summary.append(dict(blueprint=bp,family=m,threshold=registry[bp][m],planned_test_episodes=60,captured_test_episodes=len(rr)//6,excluded_episodes=excluded,age_overstatements=over,source_queries=len(gaps),oracle_gap_us_p95=quantile(gaps),above_old=above,below_old=below))
    write(P/'development_sheng.json',dict(rows=rows,registry=registry,summary=summary,freeze_sha256=sha(E/'freeze.json'),parent_sha256=sha(OLD/'qualification_sheng.json'),fresh_qualification=False,scope='New score designed after reading prior test results. Entire prior corpus is now development; no independent risk certification, paid service measurement or novelty claim. Frozen predictor replay is shared.'))
    # Original previously-frozen policies only. The new balanced methods have no
    # measured policy and are deliberately excluded from these conditional bounds.
    paid=read(OLD/'paid_sheng.json');results=[]
    for bp in data['catalog']:
        for method in paid['rows'][0]['methods']:
            family=method.rsplit('_',1)[0]
            for rate in (20000000,2000000):
                for startup in ('warm','cold'):
                    traces=[t for t in paid['traces'] if t['blueprint']==bp and t['method']==method and t['rate']==rate and t['startup']==startup];assert len(traces)==60
                    selected=[];failed=[]
                    for tr in traces:
                        grants=[d for d in tr['decisions'] if d['grant']]
                        selected.append(bool(grants));failed.append(any(F(*source[d['fact_id']]['scores'][family])>F(*data['registry'][bp][family]) for d in grants))
                    results.append(dict(blueprint=bp,method=method,rate=rate,startup=startup,**certificate(selected,failed,policies=192)))
    write(P/'conditional_diagnostic.json',dict(policies=results,zero_failure_selected_episodes_required=zero_failure_required(F(1,20),F(1,20),192),parent_paid_sha256=sha(OLD/'paid_sheng.json'),scope='Post-test descriptive fixed-policy, class-specific whole-episode grant-conditional center-exclusion bounds. Simultaneous 192 events; not a new independent certification of the balanced candidate. No per-query or collision claim.'))
    print('FINITE_BALANCED_DEVELOPMENT_COMPLETE',len(rows),flush=True)
if __name__=='__main__':main()
