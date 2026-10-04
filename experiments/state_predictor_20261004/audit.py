#!/usr/bin/env python3
"""Independent Fraction containment/dynamics audit; predictor replay is shared."""
import argparse,hashlib,json,math
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
from predictor import METHODS,predict

ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def floorroot(x):return math.isqrt(x.numerator//x.denominator)
def ceilroot(x):
    r=floorroot(x);return r+(r*r<x)
def error(c,xy):return ceilroot(sum((F.from_float(float(x))*1000000-v)**2 for x,v in zip(xy,c)))
def body(ext):return ceilroot(sum((F.from_float(float(x))*1000000)**2 for x in ext))
def age(cl):
    if cl<=0:return 0
    t=max(0,min(500000,int((-5+math.sqrt(25+6*cl/1000000))/3*1000000)))
    valid=lambda v:5000000*v*1000000+1500000*v*v<cl*1000000000000
    while t and not valid(t):t-=1
    while t<500000 and valid(t+1):t+=1
    assert valid(t) and (t==500000 or not valid(t+1))
    return t
def percentile(vals,n,d=100):
    vv=sorted(vals);pos=F((len(vv)-1)*n,d);lo=pos.numerator//pos.denominator;hi=min(lo+1,len(vv)-1);return float(vv[lo]+(vv[hi]-vv[lo])*(pos-lo))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();f=read(E/'freeze.json')
    for section in ('sources','inputs'):
        for n,h in f[section].items():assert sha(ROOT/n)==h,n
    data=read(ROOT/'results/prospective_shape_20261004/analysis_sheng.json');out=read(P/'analysis_sheng.json');models=read(P/'models_sheng.json');rad=read(P/'development_radii.json');assert not rad['fresh_qualification'] and out['freeze_sha256']==models['freeze_sha256']==sha(E/'freeze.json') and out['model_sha256']==sha(P/'models_sheng.json') and out['radii_sha256']==sha(P/'development_radii.json')
    rows=data['rows'];assert [r['id'] for r in rows]==[r['id'] for r in out['rows']];catalog=data['context']['catalog'];scores=defaultdict(int);byep=defaultdict(list);predictions=0;errchecks=0
    for r,v in zip(rows,out['rows']):
        for key in ('id','episode_id','blueprint','split','layout'):assert r[key]==v[key]
        for m in METHODS:
            c=predict(r['hulls_cm'],r['layout'],models['models'][r['blueprint']][m]);assert c==v['centers_um'][m];e=None if c is None else error(c,r['true_xy']);assert e==v['errors_um'][m];predictions+=1;errchecks+=e is not None
            if r['split']=='calibration':scores[(r['episode_id'],m)]=max(scores[(r['episode_id'],m)],e or 0)
        byep[r['episode_id']].append((r,v))
    assert rad['episode_scores']=={ep+'|'+m:s for (ep,m),s in scores.items()}
    radius={};checks=0;summaries=[]
    for bp in catalog:
        cal=[e['episode'] for e in data['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='calibration'];assert len(cal)==95;radius[bp]={m:max(scores[(ep['id'],m)] for ep in cal) for m in METHODS};assert radius[bp]==rad['radii_um'][bp]
        eps=[e['episode'] for e in data['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='test'];assert len(eps)==60
        for m in METHODS:
            excluded=[];gaps=[];ages=[];over=above=below=bounded=refused=0
            for ep in eps:
                rr=byep[ep['id']]
                if any(v['errors_um'][m] is not None and v['errors_um'][m]>radius[bp][m] for _,v in rr):excluded.append(ep['id'])
                for r,v in rr:
                    c=v['centers_um'][m]
                    if c is None:refused+=1;continue
                    bounded+=1;b=body(catalog[bp]);aa=[];oo=[]
                    for j,q in enumerate(([-6000000,0],[6000000,0])):
                        dist=floorroot(sum(F(cc-qq)**2 for cc,qq in zip(c,q)));t=age(max(0,dist-radius[bp][m])-b-750000)
                        truthdist=floorroot(sum((F.from_float(float(x))*1000000-qq)**2 for x,qq in zip(r['true_xy'],q)));oracle=age(truthdist-b-750000);joint=r['methods']['joint_hull']['lower_us'][j];aa.append(t);oo.append(oracle);gaps.append(max(0,oracle-t));ages.append(t);over+=t>oracle;above+=t>joint;below+=t<joint;checks+=1
                        if v['errors_um'][m]<=radius[bp][m]:assert t<=oracle
                    assert aa==v['ages_us'][m] and oo==v['oracle_us']
            summaries.append(dict(blueprint=bp,method=m,radius_um=radius[bp][m],planned_test_episodes=60,captured_test_episodes=sum(bool(byep[ep['id']]) for ep in eps),excluded_episodes=excluded,bounded_frames=bounded,refused_frames=refused,source_queries=len(ages),age_overstatements=over,above_joint=above,below_joint=below,age_us_median=percentile(ages,50),age_us_p95=percentile(ages,95),oracle_gap_us_median=percentile(gaps,50),oracle_gap_us_p95=percentile(gaps,95)))
    for expect,actual in zip(summaries,out['summary']):
        for k in expect:
            if 'median' in k or 'p95' in k:assert abs(expect[k]-actual[k])<1e-7
            else:assert expect[k]==actual[k],(k,expect[k],actual[k])
    result=dict(rows=len(rows),shared_predictor_replays=predictions,independent_exact_error_checks=errchecks,independent_test_age_checks=checks,models_sha256=sha(P/'models_sheng.json'),analysis_sha256=sha(P/'analysis_sheng.json'),source_sha256=sha(Path(__file__)),summary=summaries,fresh_qualification=False,scope='Shared frozen predictor replay; independent rational radii, full planned-episode calibration maxima, exclusions, source ages and comparisons. No model refit/local training repeat or independent fresh qualification.')
    a.out.write_text(json.dumps(result,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in result.items() if k!='summary'}))
if __name__=='__main__':main()
