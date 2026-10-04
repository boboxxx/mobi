#!/usr/bin/env python3
"""One fixed fit/development gate; no new qualification or paid policy claim."""
import hashlib,json,time
from collections import defaultdict,Counter
from fractions import Fraction as F
from pathlib import Path
from model import fit,predict,prepare
from geometry import conformity,infer
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
FAMILIES=('local_mean','local_modes');VARIANTS=('plain','max','clip')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,x):p.write_text(json.dumps(x,separators=(',',':'))+'\n')
def qtile(v,p):
    v=sorted(v);pos=F((len(v)-1)*p,100);i=pos.numerator//pos.denominator;return float(v[i]+(v[min(i+1,len(v)-1)]-v[i])*(pos-i))
def main():
    f=read(E/'freeze.json')
    for section in ('sources','inputs'):
        for n,h in f[section].items():assert sha(ROOT/n)==h,n
    assert not (P/'models_sheng.json').exists() and not (P/'development_sheng.json').exists()
    old=read(ROOT/'results/pose_support_20261004/analysis_sheng.json');labels={r['id']:r['true_xy'] for r in read(ROOT/'results/prospective_expiry_20261003/analysis_sheng.json')['rows']};data=read(ROOT/'results/prospective_shape_20261004/analysis_sheng.json');catalog=data['context']['catalog'];models={}
    for bp in catalog:
        models[bp]=fit([r for r in old['rows'] if r['blueprint']==bp],labels);print('fit',bp,models[bp]['training_rows'],flush=True)
    write(P/'models_sheng.json',dict(models=models,freeze_sha256=sha(E/'freeze.json'),scope='Single frozen fit on prior batch; local residuals exclude entire same episode. No latest-development labels in fit.'))
    runtime={bp:prepare(m) for bp,m in models.items()};scores=defaultdict(lambda:F(0));rows=[]
    for r in data['rows']:
        if r['split']!='calibration':continue
        pred=predict(r['hulls_cm'],r['layout'],models[r['blueprint']],runtime[r['blueprint']]);ss={m:conformity(r['hulls_cm'],catalog[r['blueprint']],pred,r['true_xy'],m) for m in FAMILIES};rows.append(dict(id=r['id'],episode_id=r['episode_id'],blueprint=r['blueprint'],split=r['split'],prediction=pred,scores={m:[v.numerator,v.denominator] for m,v in ss.items()}))
        for m,v in ss.items():scores[(r['episode_id'],m)]=max(scores[(r['episode_id'],m)],v)
    registry={}
    for bp in catalog:
        plan=[e['episode'] for e in data['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='calibration'];assert len(plan)==95;registry[bp]={}
        for m in FAMILIES:
            q=max(scores[(e['id'],m)] for e in plan);registry[bp][m]=[q.numerator,q.denominator]
    receipt=dict(registry=registry,episode_scores={ep+'|'+m:[v.numerator,v.denominator] for (ep,m),v in scores.items()},fresh_qualification=False,scope='Already-observed development batch; descriptive max95, not a new holdout.')
    write(P/'development_registry.json',receipt)
    # Oracle values come from independently audited exact stored current-center reference.
    reference=read(ROOT/'results/state_predictor_20261004/analysis_sheng.json');oracle={r['id']:r.get('oracle_us',[]) for r in reference['rows'] if r['split']=='test'};byep=defaultdict(list)
    for j,r in enumerate(v for v in data['rows'] if v['split']=='test'):
        pred=predict(r['hulls_cm'],r['layout'],models[r['blueprint']],runtime[r['blueprint']]);ss={m:conformity(r['hulls_cm'],catalog[r['blueprint']],pred,r['true_xy'],m) for m in FAMILIES};methods={}
        for m in FAMILIES:
            q=F(*registry[r['blueprint']][m])
            for variant in VARIANTS:
                # One actual prediction+geometry profile per method, not WCET or full frontend cost.
                start=time.perf_counter();pp=predict(r['hulls_cm'],r['layout'],models[r['blueprint']],runtime[r['blueprint']]);g=infer(r['hulls_cm'],catalog[r['blueprint']],pp,q,m,variant);elapsed=time.perf_counter()-start;assert pp==pred;methods[m+'_'+variant]=dict(**g,prediction_inference_s=elapsed)
        out=dict(id=r['id'],episode_id=r['episode_id'],blueprint=r['blueprint'],split=r['split'],prediction=pred,scores={m:[v.numerator,v.denominator] for m,v in ss.items()},oracle_us=oracle[r['id']],joint_us=r['methods']['joint_hull']['lower_us'],methods=methods);rows.append(out);byep[r['episode_id']].append(out)
        if (j+1)%250==0:print('development',j+1,flush=True)
    summary=[]
    for bp in catalog:
        ep=[e['episode'] for e in data['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='test'];assert len(ep)==60
        for m in FAMILIES:
            q=F(*registry[bp][m]);excluded=[e['id'] for e in ep if any(F(*r['scores'][m])>q for r in byep[e['id']])]
            for variant in VARIANTS:
                key=m+'_'+variant;rr=[r for e in ep for r in byep[e['id']]];gaps=[];ages=[];over=above=below=bounded=pruned=active=0;fees=[]
                for r in rr:
                    out=r['methods'][key];fees.append(out['prediction_inference_s']);pruned+=out['pruned_pairs'];active+=out['active_pairs']
                    if not r['oracle_us']:continue
                    if out['status']=='bounded':aa=out['lower_us'];bounded+=1
                    else:aa=[0,0]
                    for t,o,joint in zip(aa,r['oracle_us'],r['joint_us']):gaps.append(max(0,o-t));ages.append(t);over+=t>o;above+=t>joint;below+=t<joint
                summary.append(dict(blueprint=bp,method=key,q=[q.numerator,q.denominator],planned_test_episodes=60,captured_test_episodes=sum(bool(byep[e['id']]) for e in ep),family_excluded_episodes=excluded,prediction_statuses=dict(Counter(r['prediction']['status'] for r in rr)),method_statuses=dict(Counter(r['methods'][key]['status'] for r in rr)),bounded_frames=bounded,source_queries=len(ages),age_overstatements=over,above_joint=above,below_joint=below,oracle_gap_us_p95=qtile(gaps,95),age_us_p95=qtile(ages,95),pruned_pairs=pruned,active_pairs=active,prediction_inference_us_median=qtile([v*1e6 for v in fees],50),prediction_inference_us_p95=qtile([v*1e6 for v in fees],95)))
    write(P/'development_sheng.json',dict(rows=rows,summary=summary,models_sha256=sha(P/'models_sheng.json'),registry_sha256=sha(P/'development_registry.json'),freeze_sha256=sha(E/'freeze.json'),scope='One finite previously-observed development gate, fixed model/guard/scales; one actual predictor+geometry profile each, no full XYZ/encode/link costs, fresh qualification or novelty claim.'));print('FINITE_HYPOTHESES_DEVELOPMENT_COMPLETE',flush=True)
if __name__=='__main__':main()
