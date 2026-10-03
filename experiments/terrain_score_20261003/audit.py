#!/usr/bin/env python3
"""Independent seven world-plane intersection and calibration audit."""
import argparse,hashlib,json,math
from fractions import Fraction
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
def rot(a):
    p,y,r=a;rx=np.array([[1,0,0],[0,math.cos(r),math.sin(r)],[0,-math.sin(r),math.cos(r)]]);ry=np.array([[math.cos(p),0,-math.sin(p)],[0,1,0],[math.sin(p),0,math.cos(p)]]);rz=np.array([[math.cos(y),-math.sin(y),0],[math.sin(y),math.cos(y),0],[0,0,1]]);return rz@ry@rx
def reference(points,origin,center,rotation,extent):
    normals=np.concatenate([rotation.T,-rotation.T,[[0,0,-1]]]);offset=np.r_[rotation.T@center+np.array(extent)+.03,-rotation.T@center+np.array(extent)+.03,-.15]
    origin_slack=offset-normals@origin
    if np.all(origin_slack>=0):return (0,0,0,1)
    enter=np.zeros(len(points));exit=np.full(len(points),np.inf);valid=np.ones(len(points),bool)
    for n,b in zip(normals,origin_slack):
        den=(points-origin)@n;positive=den>1e-12;negative=den< -1e-12;stationary=~(positive|negative);valid&=~stationary|(b>=0);hit=np.divide(b,den,out=np.zeros(len(points)),where=~stationary);enter=np.maximum(enter,np.where(negative,hit,-np.inf));exit=np.minimum(exit,np.where(positive,hit,np.inf))
    eligible=valid&(exit>=enter)&(enter<=1+1e-10);n=int(eligible.sum());k=int(np.sum(eligible&(exit<1-1e-10)));return n,k,k if n>=8 else 0,n if n>=8 else 1
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--analysis',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();data=json.loads(a.analysis.read_bytes());records={};clouds={};checks=0;points_checked=0
    for name,sha in data['input_hashes'].items():
        path=ROOT/name;assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
        if path.name=='record.json':
            for r in json.loads(path.read_bytes()):
                if r['status']=='captured':records[r['id']]=(r,path.parent/r['cloud_file'])
    def check(s,p,o,c,r,e):
        nonlocal checks,points_checked
        actual=reference(p,o,np.array(c),r,e);assert actual==(s['visible_count'],s['pass_count'],s['numerator'],s['denominator']),(actual,s);checks+=1;points_checked+=len(p)
    def read(path):
        with np.load(path) as z:return np.c_[z['raw']['x'],z['raw']['y'],z['raw']['z']].astype(float)@z['transform'][:3,:3].T+z['origin'],z['origin'].copy()
    for row in data['rows']:
        r,path=records[row['id']]
        if row['id'] not in clouds:clouds[row['id']]=read(path)
        p,o=clouds[row['id']];check(row['score'],p[::row['stride']],o,r['center'],np.array(r['actor_transform']['matrix'])[:3,:3]@rot(np.deg2rad(r['bounding_box']['rotation'])),r['bounding_box']['extent'])
    sources={s['case']:s for s in json.loads((ROOT/'results/pose_inversion_20261003/replay/sources.json').read_bytes())}
    for c in data['witnesses']:
        s=sources[c['case']];p,o=read(ROOT/s['source_cloud']);pose=np.array(c['pose']);center=np.array(s['anchor'])+np.array(s['road_rotation'])@pose[:3]
        q=Fraction(**data['summary'][s['blueprint']]['threshold'])
        for stride in (16,4,1):
            check(c['scores'][str(stride)],p[::stride],o,center,rot(pose[3:]),s['extent']);accepted=all(Fraction(c['scores'][str(t)]['numerator'],c['scores'][str(t)]['denominator'])<=q for t in (16,4,1) if t>=stride);assert accepted==c['accepted_by_stride'][str(stride)]
    # Independently recompute episode-max quantiles and false exclusions.
    grouped={}
    for row in data['rows']:grouped.setdefault(row['episode'],[]).append(row)
    plans=[]
    for name in data['input_hashes']:
        if name.endswith('plan.json'):
            for e in json.loads((ROOT/name).read_bytes()):
                if (e['blueprint'].startswith('walker.'))==('availability_followup' in name):plans.append(e)
    for bp,s in data['summary'].items():
        cal=[e for e in plans if e['blueprint']==bp and e['split']=='calibration'];tests=[e for e in plans if e['blueprint']==bp and e['split']=='test'];assert len(cal)==19
        def values(e):return [Fraction(r['score']['numerator'],r['score']['denominator']) for r in grouped.get(e['id'],[])]
        q=max(max(values(e)) if len(values(e))==6 else Fraction(0) for e in cal);assert q==Fraction(**s['threshold']);assert [e['id'] for e in tests if len(values(e))==6 and max(values(e))>q]==s['test_false_exclusion']
    a.out.write_text(json.dumps(dict(score_checks=checks,point_checks=points_checked,input_hash_checks=len(data['input_hashes']),analysis_sha256=hashlib.sha256(a.analysis.read_bytes()).hexdigest(),audit_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),independent_world_plane_counts=True),indent=2)+'\n')
if __name__=='__main__':main()
