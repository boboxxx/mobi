#!/usr/bin/env python3
"""Shared exemplar replay; independent rational pose/circle clipping and scores."""
import argparse,hashlib,json,math
from collections import defaultdict,Counter
from fractions import Fraction as F
from pathlib import Path
from model import predict,prepare
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
FAMILIES=('local_mean','local_modes');VARIANTS=('plain','max','clip')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def up(x):return -((-x.numerator)//x.denominator)
def floorroot(x):return math.isqrt(x.numerator//x.denominator)
def ceilroot(x):
    r=floorroot(x);return r+(r*r<x)
def params(ext,delta=0):
    ee=[F.from_float(float(v))*1000000 for v in ext];b=ceilroot(sum(v*v for v in ee));xy=ceilroot(sum(v*v for v in ee[:2]));pad=up(F(b*87267,1000000))+up(F(xy*8730,1000000))+8000+delta
    return b,[up(v)+pad for v in ee[:2]]
def projected(hulls,dirs):
    tables=[]
    for h in hulls:
        tab=[]
        for c,s in dirs:
            uu=[(c*p[0]+s*p[1])*10000 for p in h];vv=[(-s*p[0]+c*p[1])*10000 for p in h];tab.append([min(uu),max(uu),min(vv),max(vv)])
        tables.append(tab)
    return tables
def rectangle_list(tables,dirs,ext,delta):
    _,(A,B)=params(ext,delta);out=[]
    for table in tables:
        for cell,(umin,umax,vmin,vmax) in enumerate(table):
            c,s=dirs[cell];norm=c*c+s*s;nu=ceilroot(F(norm));bounds=[umax-A*nu,umin+A*nu,vmax-B*nu,vmin+B*nu]
            if bounds[0]<=bounds[1] and bounds[2]<=bounds[3]:out.append((cell,bounds,norm))
    return out
def pose_score(tables,dirs,ext,xy):
    _,(A,B)=params(ext);point=[F.from_float(float(v))*1000000 for v in xy];values=[]
    for table in tables:
        for cell,(umin,umax,vmin,vmax) in enumerate(table):
            c,s=dirs[cell];nu=ceilroot(F(c*c+s*s));u=c*point[0]+s*point[1];v=-s*point[0]+c*point[1];excess=max(F(0),umax-A*nu-u,u-umin-A*nu,vmax-B*nu-v,v-vmin-B*nu);values.append(up(excess/nu))
    return min(values) if values else 0
def err(center,xy):return ceilroot(sum((F.from_float(float(v))*1000000-c)**2 for v,c in zip(xy,center)))
def squared(rect,point,dirs):
    cell,(a,b,z,w),den=rect;c,s=dirs[cell];u=c*point[0]+s*point[1];v=-s*point[0]+c*point[1];return F(max(a-u,0,u-b)**2+max(z-v,0,v-w)**2,den)
def circle(center,radius,query):return max(0,floorroot(sum(F(c-q)**2 for c,q in zip(center,query)))-radius)
def age(distance,body):
    gap=distance-body-750000
    if gap<=0:return 0
    t=max(0,min(500000,int((-5+math.sqrt(25+6*gap/1000000))/3*1000000)));valid=lambda t:10000000*t+3*t*t<2000000*gap
    while t and not valid(t):t-=1
    while t<500000 and valid(t+1):t+=1
    return t
def independent_infer(hulls,extent,pred,q,family,variant,dirs):
    b,_=params(extent);tables=projected(hulls,dirs);rects=rectangle_list(tables,dirs,extent,up(q*10000))
    if not hulls:return dict(status='refused',lower_us=[],active_pairs=0,pruned_pairs=0)
    supported=pred['status']=='supported';centers=([pred['mean_um']] if family=='local_mean' else pred['centers_um']) if supported else [];radius=up(q*(pred['single_scale_um'] if family=='local_mean' else pred['modes_scale_um'])) if supported else None
    if supported and variant=='plain':return dict(status='bounded',lower_us=[age(min(circle(c,radius,query) for c in centers),b) for query in ((-6000000,0),(6000000,0))],active_pairs=0,pruned_pairs=0,radius_um=radius,fallback=False)
    if not rects:return dict(status='empty',lower_us=[],active_pairs=0,pruned_pairs=0)
    if not supported:return dict(status='bounded',lower_us=[age(floorroot(min(squared(r,query,dirs) for r in rects)),b) for query in ((-6000000,0),(6000000,0))],active_pairs=0,pruned_pairs=0,fallback=True)
    pairs=[(c,[r for r in rects if squared(r,c,dirs)<=radius*radius]) for c in centers] if variant=='clip' else [];pruned=sum(len(rects)-len(rr) for _,rr in pairs);alive=[(c,rr) for c,rr in pairs if rr]
    if variant=='clip' and not alive:return dict(status='empty',lower_us=[],active_pairs=0,pruned_pairs=pruned,radius_um=radius)
    ages=[]
    for query in ((-6000000,0),(6000000,0)):
        if variant=='max':dist=max(floorroot(min(squared(r,query,dirs) for r in rects)),min(circle(c,radius,query) for c in centers))
        else:dist=min(max(circle(c,radius,query),floorroot(min(squared(r,query,dirs) for r in rr))) for c,rr in alive)
        ages.append(age(dist,b))
    return dict(status='bounded',lower_us=ages,active_pairs=sum(len(rr) for _,rr in alive),pruned_pairs=pruned,radius_um=radius,fallback=False)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();f=read(E/'freeze.json')
    for section in ('sources','inputs'):
        for n,h in f[section].items():assert sha(ROOT/n)==h,n
    d=read(P/'development_sheng.json');registry=read(P/'development_registry.json');models=read(P/'models_sheng.json');parent=read(ROOT/'results/prospective_shape_20261004/analysis_sheng.json');dirs=read(ROOT/'experiments/pose_support_20261004/directions.json')['normal_xy'];lookup={r['id']:r for r in parent['rows']};runtimes={bp:prepare(m) for bp,m in models['models'].items()};scores=defaultdict(lambda:F(0));byep=defaultdict(list);checks=0;oracle=read(ROOT/'results/state_predictor_20261004/analysis_sheng.json');oracles={r['id']:r.get('oracle_us',[]) for r in oracle['rows'] if r['split']=='test'}
    assert d['models_sha256']==sha(P/'models_sheng.json') and d['registry_sha256']==sha(P/'development_registry.json') and d['freeze_sha256']==models['freeze_sha256']==sha(E/'freeze.json') and not registry['fresh_qualification']
    assert set(r['id'] for r in d['rows'])==set(lookup) and len(d['rows'])==len(lookup)
    for i,row in enumerate(d['rows']):
        r=lookup[row['id']];bp=r['blueprint'];extent=parent['context']['catalog'][bp]
        for key in ('id','episode_id','blueprint','split'):assert row[key]==r[key]
        pred=predict(r['hulls_cm'],r['layout'],models['models'][bp],runtimes[bp]);assert pred==row['prediction'];sgeom=F(pose_score(projected(r['hulls_cm'],dirs),dirs,extent,r['true_xy']),10000)
        for family in FAMILIES:
            s=sgeom
            if pred['status']=='supported':
                centers=[pred['mean_um']] if family=='local_mean' else pred['centers_um'];scale=pred['single_scale_um'] if family=='local_mean' else pred['modes_scale_um'];s=max(s,F(min(err(c,r['true_xy']) for c in centers),scale))
            assert row['scores'][family]==[s.numerator,s.denominator]
            if r['split']=='calibration':scores[(r['episode_id'],family)]=max(scores[(r['episode_id'],family)],s)
            else:
                q=F(*registry['registry'][bp][family]);assert row['oracle_us']==oracles[r['id']] and row['joint_us']==r['methods']['joint_hull']['lower_us']
                for variant in VARIANTS:
                    expect=independent_infer(r['hulls_cm'],extent,pred,q,family,variant,dirs);actual=row['methods'][family+'_'+variant];assert all(actual[k]==v for k,v in expect.items()),(r['id'],family,variant);assert actual['prediction_inference_s']>=0
                    if s<=q and expect['status']=='bounded':assert all(t<=o for t,o in zip(expect['lower_us'],row['oracle_us']))
                    checks+=1
        byep[r['episode_id']].append(row)
        if (i+1)%500==0:print('audited',i+1,flush=True)
    expected_registry={}
    for bp in parent['context']['catalog']:
        eps=[e['episode'] for e in parent['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='calibration'];assert len(eps)==95;expected_registry[bp]={}
        for m in FAMILIES:
            q=max(scores[(e['id'],m)] for e in eps);expected_registry[bp][m]=[q.numerator,q.denominator]
    assert registry['registry']==expected_registry and registry['episode_scores']=={ep+'|'+m:[s.numerator,s.denominator] for (ep,m),s in scores.items()}
    # Recompute all integer outcome totals; measured timing quantiles remain descriptive.
    outcomes=[]
    for summary in d['summary']:
        bp=summary['blueprint'];key=summary['method'];family,variant=key.rsplit('_',1);eps=[e['episode'] for e in parent['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='test'];rr=[r for e in eps for r in byep[e['id']]];q=F(*registry['registry'][bp][family]);excluded=[e['id'] for e in eps if any(F(*r['scores'][family])>q for r in byep[e['id']])];assert excluded==summary['family_excluded_episodes']
        over=above=below=bounded=queries=pruned=active=0;statuses=Counter();gaps=[]
        for r in rr:
            v=r['methods'][key];statuses[v['status']]+=1;pruned+=v['pruned_pairs'];active+=v['active_pairs']
            if not r['oracle_us']:continue
            aa=v['lower_us'] if v['status']=='bounded' else [0,0];bounded+=v['status']=='bounded'
            for t,o,j in zip(aa,r['oracle_us'],r['joint_us']):over+=t>o;above+=t>j;below+=t<j;queries+=1;gaps.append(max(0,o-t))
        expect=dict(planned_test_episodes=60,captured_test_episodes=sum(bool(byep[e['id']]) for e in eps),bounded_frames=bounded,source_queries=queries,age_overstatements=over,above_joint=above,below_joint=below,pruned_pairs=pruned,active_pairs=active,prediction_statuses=dict(Counter(r['prediction']['status'] for r in rr)),method_statuses=dict(statuses));assert all(summary[k]==v for k,v in expect.items());gaps.sort();pos=F((len(gaps)-1)*95,100);j=pos.numerator//pos.denominator;p95=float(gaps[j]+(gaps[min(j+1,len(gaps)-1)]-gaps[j])*(pos-j));assert summary['oracle_gap_us_p95']==p95;outcomes.append(dict(blueprint=bp,method=key,excluded_episodes=len(excluded),**expect,oracle_gap_us_p95=p95))
    out=dict(rows=len(d['rows']),independent_geometry_checks=checks,shared_prediction_replays=len(d['rows']),summary=outcomes,source_sha256=sha(Path(__file__)),development_sha256=sha(P/'development_sheng.json'),models_sha256=sha(P/'models_sheng.json'),fresh_qualification=False,scope='Shared frozen exemplar/feature replay; independent rational pose scores, registry maxima, exact rectangle-circle pruning, distance/age bounds, exclusions and integer outcomes. Existing data, no fresh risk/paid policy/novelty claim.')
    a.out.write_text(json.dumps(out,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in out.items() if k!='summary'}))
if __name__=='__main__':main()
