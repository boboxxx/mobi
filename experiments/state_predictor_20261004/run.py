#!/usr/bin/env python3
"""One finite reused-development baseline; not fresh statistical qualification."""
import hashlib,json,sys
from collections import defaultdict
from pathlib import Path
import numpy as np
from predictor import METHODS,fit,predict
from integer_state import error_um,body_um,circle_age,oracle_age

ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,x):p.write_text(json.dumps(x,separators=(',',':'))+'\n')
def main():
    f=read(E/'freeze.json')
    for section in ('sources','inputs'):
        for n,h in f[section].items():assert sha(ROOT/n)==h,n
    assert not (P/'analysis_sheng.json').exists() and not (P/'models_sheng.json').exists()
    old=read(ROOT/'results/pose_support_20261004/analysis_sheng.json');labeldata=read(ROOT/'results/prospective_expiry_20261003/analysis_sheng.json');labels={r['id']:r['true_xy'] for r in labeldata['rows']};new=read(ROOT/'results/prospective_shape_20261004/analysis_sheng.json');catalog=new['context']['catalog'];models={}
    for bp in catalog:
        rr=[r for r in old['rows'] if r['blueprint']==bp];models[bp]={m:fit(rr,labels,m) for m in METHODS}
    write(P/'models_sheng.json',dict(models=models,freeze_sha256=sha(E/'freeze.json'),scope='Fit prior completed batch only; fixed methods/hyperparameters. Newer batch was already observed before this exploratory gate.'))
    rows=[];scores=defaultdict(int);byep=defaultdict(list)
    for r in new['rows']:
        pred={m:predict(r['hulls_cm'],r['layout'],models[r['blueprint']][m]) for m in METHODS};errors={m:None if pred[m] is None else error_um(pred[m],r['true_xy']) for m in METHODS}
        v=dict(id=r['id'],episode_id=r['episode_id'],blueprint=r['blueprint'],split=r['split'],layout=r['layout'],centers_um=pred,errors_um=errors);rows.append(v);byep[r['episode_id']].append(v)
        if r['split']=='calibration':
            for m in METHODS:scores[(r['episode_id'],m)]=max(scores[(r['episode_id'],m)],errors[m] or 0)
    radii={}
    for bp in catalog:
        ee=[e['episode'] for e in new['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='calibration'];assert len(ee)==95
        radii[bp]={m:max(scores[(e['id'],m)] for e in ee) for m in METHODS}
    # Receipt precedes test source-age evaluation; reused data is explicitly not new holdout.
    write(P/'development_radii.json',dict(radii_um=radii,episode_scores={ep+'|'+m:v for (ep,m),v in scores.items()},fresh_qualification=False))
    lookup={r['id']:r for r in new['rows']};queries=[[-6000000,0],[6000000,0]]
    summaries=[]
    for bp in catalog:
        eps=[e['episode'] for e in new['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='test'];assert len(eps)==60
        for m in METHODS:
            excluded=[];gaps=[];over=0;bounded=0;gains=0;losses=0;available_queries=0;refused=0;ages=[]
            for ep in eps:
                rr=byep[ep['id']]
                if any(r['errors_um'][m] is not None and r['errors_um'][m]>radii[bp][m] for r in rr):excluded.append(ep['id'])
                for r in rr:
                    source=lookup[r['id']];center=r['centers_um'][m]
                    if center is None:refused+=1;continue
                    bounded+=1;body=body_um(catalog[bp]);r.setdefault('ages_us',{})[m]=[];r.setdefault('oracle_us',[])
                    for j,q in enumerate(queries):
                        a=circle_age(center,radii[bp][m],body,q);o=oracle_age(source['true_xy'],body,q);r['ages_us'][m].append(a)
                        if m==METHODS[0]:r['oracle_us'].append(o)
                        assert r['oracle_us'][j]==o
                        joint=source['methods']['joint_hull']['lower_us'][j]
                        gaps.append(max(0,o-a));ages.append(a);over+=a>o;gains+=a>joint;losses+=a<joint;available_queries+=1
            pct=lambda x,p:float(np.percentile(x,p)) if x else None
            summaries.append(dict(blueprint=bp,method=m,radius_um=radii[bp][m],planned_test_episodes=60,captured_test_episodes=sum(bool(byep[e['id']]) for e in eps),excluded_episodes=excluded,bounded_frames=bounded,refused_frames=refused,source_queries=available_queries,age_overstatements=over,above_joint=gains,below_joint=losses,age_us_median=pct(ages,50),age_us_p95=pct(ages,95),oracle_gap_us_median=pct(gaps,50),oracle_gap_us_p95=pct(gaps,95)))
    out=dict(rows=rows,summary=summaries,model_sha256=sha(P/'models_sheng.json'),radii_sha256=sha(P/'development_radii.json'),freeze_sha256=sha(E/'freeze.json'),scope='Fixed bbox/ridge/quadratic circle baselines fit prior batch and evaluated on already-observed development data. Source ages only: no actual encoding/processing fees, paid policy utility, fresh risk qualification, unknown inventory, physical/live ego or novelty claim.')
    write(P/'analysis_sheng.json',out);print(json.dumps(summaries,indent=2));print('FINITE_STATE_BASELINES_COMPLETE',flush=True)
if __name__=='__main__':main()
