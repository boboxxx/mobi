#!/usr/bin/env python3
"""Quadratic-form reference audit, no native/search imports."""
import argparse,hashlib,json,math,sys
from fractions import Fraction
from pathlib import Path
import numpy as np
import analyze as reference
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def box_metric(center,g):
    if (np.abs(center)<=[2.3,1.3]).all():return 0.
    value=float('inf')
    for fixed,extent in [(0,2.3),(1,1.3)]:
        free=1-fixed
        for sign in [-1,1]:
            p=center.copy();p[fixed]=sign*extent;p[free]=np.clip(center[free]-g[free,fixed]*(p[fixed]-center[fixed])/g[free,free],-[2.3,1.3][free],[2.3,1.3][free]);d=p-center;value=min(value,float(d@g@d))
    return math.sqrt(value)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();basepath=a.results/'study/analysis.json';base=json.loads(basepath.read_bytes())
    assert (a.results/'audit_local.json').read_bytes()==(a.results/'audit_sheng.json').read_bytes()
    oldaudit=json.loads((a.results/'audit_sheng.json').read_bytes());assert oldaudit['analyzer_sha256']==sha(Path(__file__).with_name('analyze.py')) and oldaudit['prefix_checks']==252 and oldaudit['source_checks']==120 and oldaudit['cases']==36
    for field in ['source_sha256','input_sha256']:
        for f,h in base[field].items():assert sha(ROOT/f)==h,f
    build=json.loads((a.results/'ellipsoid_build.json').read_bytes());assert build['source_sha256']==sha(Path(__file__).with_name('ellipsoid.cpp'))
    summaries=[];checks=0;cache={}
    for study,count in [('ellipsoid_study',36),('heading_study',12)]:
        s=json.loads((a.results/study/'analysis.json').read_bytes());assert len(s['rows'])==count and s['sphere_study_sha256']==sha(basepath) and s['library_sha256']==build['binary_sha256']
        for f,h in s['source_sha256'].items():assert sha(ROOT/f)==h,f
        for row in s['rows']:
            original=next(r for r in base['rows'] if (r['run'],r['index'],r['klass'])==(row['run'],row['index'],row['klass']))
            for key,v in original.items():
                if key not in ['witness','search_ms','native_calls','candidates']:assert row[key]==v,key
            outer=row['profile']['r_max'] if study=='ellipsoid_study' else row['shape_outer'];core=row['profile']['r_min'];assert core<=outer<=row['profile']['r_max']
            if study=='heading_study':assert row['klass']=='small' and row['run'] in ['c0_view0_reference_fixed','c0_view0_reference_rate20'] and outer==(core if row['shape']=='sphere' else row['profile']['r_max'])
            path=a.results/'study'/row['input_file'];assert sha(path)==row['input_sha256']
            if row['input_file'] not in cache:
                with np.load(path) as z:integers=z['integers'];segments=z['rays'][:,:6]
                times=np.unique(integers[:,6]);back=reference.independent_back(times,row['ref_us']);perray=back[np.searchsorted(times,integers[:,6])];np.testing.assert_allclose(back,row['back_distances'],rtol=0,atol=1e-12);cache[row['input_file']]=(integers,times,perray,segments)
            integers,times,back,segments=cache[row['input_file']];w=row['witness'];summary=dict(study=study,run=row['run'],index=row['index'],klass=row['klass'],shape=row.get('shape','ellipsoid'),lower_horizon_us=row['lower_horizon_us'],upper_horizon_us=None if w is None else w['time_us'])
            assert row['search_ms']>=0 and math.isfinite(row['search_ms']) and 0<row['candidates']<=2000*row['native_calls']
            if w:
                assert 0<=w['time_us']<=1500000 and w['time_us']%5000==0 and w['time_us']>=row['lower_horizon_us'];u=np.asarray(w['outward_direction']);assert abs(np.linalg.norm(u)-1)<1e-14
                index=w['direction_index'] if study=='ellipsoid_study' else w['contact_index']//92
                assert (0<=index<720 if study=='ellipsoid_study' else 0<=index<128)
                angle=index*math.pi/(360 if study=='ellipsoid_study' else 64)+row['motion']['yaw'];np.testing.assert_allclose(u,[math.cos(angle),math.sin(angle)],rtol=0,atol=1e-14)
                axis=np.r_[u,0.];g=np.eye(3)/core**2+(1/outer**2-1/core**2)*np.outer(axis,axis)
                center=np.asarray(w['center_reference']);positions=np.column_stack([center+back[:,None]*u,np.full(len(segments),row['scope']['plane_z'])]);delta=segments[:,3:6]-segments[:,:3];rel=positions-segments[:,:3];den=np.einsum('ni,ij,nj->n',delta,g,delta);along=np.divide(np.einsum('ni,ij,nj->n',rel,g,delta),den,out=np.zeros(len(delta)),where=den>0);residual=rel-np.clip(along,0,1)[:,None]*delta;d=np.sqrt(np.einsum('ni,ij,nj->n',residual,g,residual));margin=float(d.min())-1-row['error']/core;assert margin>1e-8/core;checks+=len(d)
                for t0,t1 in zip(times,times[1:]):
                    dt=Fraction(int(t1)-int(t0),1000000);peak=5+3*dt/2;assert (peak-5)/(dt/2)==3 and (5-peak)/(dt/2)==-3 and (5+peak)*dt/2==5*dt+Fraction(3,4)*dt*dt
                age=Fraction(row['ref_us']-int(times[-1]),1000000);h=Fraction(w['time_us'],1000000);forward=float((5+3*age)*h+Fraction(3,2)*h*h);future=center-u*forward
                if study=='heading_study':np.testing.assert_allclose(future,w['center_future'],rtol=0,atol=1e-12)
                yaw=row['motion']['yaw'];c,sin=math.cos(yaw),math.sin(yaw);rot=np.array([[c,-sin],[sin,c]]);local=(future-np.asarray(row['scope']['query']))@rot;ulocal=u@rot;g2=np.eye(2)/core**2+(1/outer**2-1/core**2)*np.outer(ulocal,ulocal);contact=box_metric(local,g2);assert contact<1-1e-7
                summary.update(normalized_ray_margin=round(margin,6),normalized_collision_penetration=round(1-contact,6),gap_us=w['time_us']-row['lower_horizon_us'])
            summaries.append(summary)
    assert not({'ellipsoid','heading','search','flow','compact','observer'}&set(sys.modules))
    out=dict(base_audit_sha256=sha(a.results/'audit_sheng.json'),base_study_sha256=sha(basepath),cases=48,witnesses=sum(x['upper_horizon_us'] is not None for x in summaries),within_200ms=sum(x['upper_horizon_us'] is not None and x['upper_horizon_us']<=200000 for x in summaries),segment_checks=checks,summaries=summaries,analyzer_sha256=sha(Path(__file__)),scope='Independent quadratic segment/rectangle and exact motion audit; same verified received information; conditional finite candidate families, no global optimality/road guarantee.')
    a.out.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['summaries','scope']}))
if __name__=='__main__':main()
