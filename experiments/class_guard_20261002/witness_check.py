#!/usr/bin/env python3
"""Recheck all old candidate trajectories under the actual augmented information."""
import argparse,hashlib,importlib.util,json,math,sys,time
from fractions import Fraction
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('independent_witness_reference',ROOT/'experiments/validity_witness_20261002/analyze.py')
reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference);body=reference.body
sha=reference.sha

def contact_metric(center,g):
    if (np.abs(center)<=[2.3,1.3]).all():return 0.
    best=math.inf
    for fixed,extent in [(0,2.3),(1,1.3)]:
        free=1-fixed
        for sign in [-1,1]:
            point=center.copy();point[fixed]=sign*extent;point[free]=np.clip(center[free]-g[free,fixed]*(point[fixed]-center[fixed])/g[free,free],-[2.3,1.3][free],[2.3,1.3][free]);delta=point-center;best=min(best,float(delta@g@delta))
    return math.sqrt(best)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.results=a.results.resolve();old=ROOT/'results/validity_witness_20261002';inputs={};cache={};summaries=[];checks=0;times_ms=[]
    def read(path):inputs[str(path.relative_to(ROOT))]=sha(path);return json.loads(path.read_bytes())
    s=read(a.results/'study/analysis.json');base=read(old/'study/analysis.json')
    for suffix in ['audit','extension_audit']:
        assert (old/(suffix+'_local.json')).read_bytes()==(old/(suffix+'_sheng.json')).read_bytes();read(old/(suffix+'_sheng.json'))
    for field in ['source_sha256','input_sha256']:
        for f,h in base[field].items():assert sha(ROOT/f)==h
    for field in ['source_sha256','input_sha256']:
        for f,h in s[field].items():assert sha(ROOT/f)==h
    profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=body.Contract()
    for family,count in [('study',36),('ellipsoid_study',36),('heading_study',12)]:
        candidates=read(old/family/'analysis.json');assert len(candidates['rows'])==count
        for row in candidates['rows']:
            started=time.perf_counter();key=(row['run'],row['index']);scope=body.Scope(**row['scope']);original=next(x for x in base['rows'] if (x['run'],x['index'],x['klass'])==(row['run'],row['index'],row['klass']));assert row['input_sha256']==original['input_sha256']
            if key not in cache:
                oldinput=old/'study'/row['input_file'];assert sha(oldinput)==row['input_sha256'];inputs[str(oldinput.relative_to(ROOT))]=sha(oldinput)
                with np.load(oldinput) as z:original_integers=z['integers'].copy()
                chunks=[original_integers];root=read(a.results/'study/roots'/(row['run']+'_augmented.json'));paths=[a.results/'study/source'/(row['run']+'_drive_%03d.json'%i) for i in range(20,row['index']+1)]
                for raw in [root['raw']]+[read(path) for path in paths]:
                    p,o,r=body.decode(body.canonical(raw),profiles,scope,contract);assert p['reference_us']<=row['ref_us'];chunks.append(np.column_stack([o[r[:,0]],r[:,1:]]))
                integers=np.unique(np.concatenate(chunks),axis=0);actual=np.unique(integers[:,6]);assert actual.tolist()==row['actual_times_us'];back=reference.independent_back(actual,row['ref_us']);perray=back[np.searchsorted(actual,integers[:,6])];segments=integers[:,:6]*.001;cache[key]=(integers,actual,perray,segments)
            integers,actual,back,segments=cache[key];w=row['witness'];assert w is not None;h=Fraction(w['time_us'],1000000);u=np.asarray(w['outward_direction']);assert abs(np.linalg.norm(u)-1)<1e-14;center=np.asarray(w['center_reference']);core=profiles[row['klass']].r_min;outer=(core if family=='study' else profiles[row['klass']].r_max if family=='ellipsoid_study' else row['shape_outer']);assert core<=outer<=profiles[row['klass']].r_max
            # Same sampled speed/global acceleration trajectory at every received time.
            for t0,t1 in zip(actual,actual[1:]):
                dt=Fraction(int(t1)-int(t0),1000000);peak=5+3*dt/2;assert (peak-5)/(dt/2)==3 and (5-peak)/(dt/2)==-3 and (5+peak)*dt/2==5*dt+Fraction(3,4)*dt*dt
            positions=np.column_stack([center+back[:,None]*u,np.full(len(segments),scope.plane_z)]);axis=np.r_[u,0.];g=np.eye(3)/core**2+(1/outer**2-1/core**2)*np.outer(axis,axis);delta=segments[:,3:6]-segments[:,:3];relative=positions-segments[:,:3];den=np.einsum('ni,ij,nj->n',delta,g,delta);along=np.divide(np.einsum('ni,ij,nj->n',relative,g,delta),den,out=np.zeros(len(delta)),where=den>0);residual=relative-np.clip(along,0,1)[:,None]*delta;dist=np.sqrt(np.einsum('ni,ij,nj->n',residual,g,residual));margin=float(dist.min())-1-math.sqrt(3)*(.01+.0005)/core;survives=margin>1e-8/core;checks+=len(dist)
            age=Fraction(row['ref_us']-int(actual[-1]),1000000);forward=float((5+3*age)*h+Fraction(3,2)*h*h);future=center-u*forward;yaw=row['motion']['yaw'];rot=np.array([[math.cos(yaw),-math.sin(yaw)],[math.sin(yaw),math.cos(yaw)]]);local=(future-np.asarray(scope.query))@rot;ulocal=u@rot;g2=np.eye(2)/core**2+(1/outer**2-1/core**2)*np.outer(ulocal,ulocal);penetration=1-contact_metric(local,g2);assert penetration>1e-7
            lower=next(x for x in s['rows'] if (x['run'],x['index'],x['method'],x['preset'],x['repeat'])==(row['run'],row['index'],'aug_fine','standard',0));assert lower['horizon_us']>0
            if survives:assert w['time_us']>=lower['horizon_us']
            summaries.append(dict(family=family,run=row['run'],index=row['index'],klass=row['klass'],tested_upper_us=w['time_us'],survives=survives,normalized_ray_margin=round(margin,6),normalized_rectangle_penetration=round(penetration,6),rays=len(integers),joint_lower_us=lower['horizon_us']));times_ms.append((time.perf_counter()-started)*1000)
    joint=[]
    for run,index in sorted(cache):
        rows=[x for x in summaries if (x['run'],x['index'])==(run,index)];lower=rows[0]['joint_lower_us'];uppers=[x['tested_upper_us'] for x in rows if x['survives']];upper=min(uppers) if uppers else None
        joint.append(dict(run=run,index=index,lower_us=lower,upper_us=upper,gap_us=None if upper is None else upper-lower,relative_loss_bound=None if upper is None else 1-lower/upper))
    assert len(summaries)==84 and len(joint)==18 and not({'search','flow','compact','observer','guard','dictionary'}&set(sys.modules))
    result=dict(cases=84,surviving_witnesses=sum(x['survives'] for x in summaries),segment_checks=checks,queries_with_verified_upper=sum(x['upper_us'] is not None for x in joint),joint=joint,summaries=summaries,input_sha256=inputs,protocol_sha256=sha(Path(__file__).with_name('WITNESS_PROTOCOL.md')),analyzer_sha256=sha(Path(__file__)),scope='Conditional all84 fixed old candidates rechecked against augmented actual received histories. Unknown upper if none survives; no global search/road/physical guarantee. Lower bound requires separate complete class_guard audit.')
    a.out.write_text(json.dumps(result,indent=2)+'\n');a.out.with_suffix('.timing.json').write_text(json.dumps(dict(checking_ms=times_ms,scope='Offline diagnostic, excluded from online controller; not WCET.'),indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['summaries','joint','input_sha256','scope']}))
if __name__=='__main__':main()
