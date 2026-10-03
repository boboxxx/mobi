#!/usr/bin/env python3
"""Independent face-event intersections, frozen draws, labels and quantiles."""
import argparse, hashlib, json, math
from fractions import Fraction
from pathlib import Path
import numpy as np
from scipy.stats import beta
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rot(angles):
    p,y,r=map(math.radians,angles);cp,sp=math.cos(p),math.sin(p);cy,sy=math.cos(y),math.sin(y);cr,sr=math.cos(r),math.sin(r)
    return np.array([[cp*cy,cy*sp*sr-sy*cr,-cy*sp*cr-sy*sr],[cp*sy,sy*sp*sr+cy*cr,-sy*sp*cr+cy*sr],[sp,-cp*sr,cp*cr]])
def reference(points,origin,center,rotation,extent):
    # Intersect six finite faces, unlike the tested accumulated slab bounds.
    a=(origin-center)@rotation;e=np.asarray(extent)+.03
    if all(abs(a)<=e):return dict(pass_count=0,visible_count=0,numerator=0,denominator=1,reason='sensor_inside_hypothesis')
    b=(points-center)@rotation;d=b-a;times=[]
    for axis in range(3):
        others=[i for i in range(3) if i!=axis]
        for sign in (-1,1):
            moving=abs(d[:,axis])>1e-12
            t=np.divide(sign*e[axis]-a[axis],d[:,axis],out=np.zeros(len(d)),where=moving)
            crossing=a[others]+t[:,None]*d[:,others]
            valid=moving&np.all(abs(crossing)<=e[others]+1e-10,axis=1)
            times.append(np.where(valid,t,np.nan))
    tt=np.array(times);entry=np.min(np.where(np.isnan(tt),np.inf,tt),axis=0);leave=np.max(np.where(np.isnan(tt),-np.inf,tt),axis=0)
    visible=(leave>=np.maximum(entry,0))&(entry<=1+1e-10)&(leave>=0);n=int(visible.sum());k=int((visible&(leave<1-1e-10)).sum())
    return dict(pass_count=k,visible_count=n,numerator=k if n>=8 else 0,denominator=n if n>=8 else 1,reason=None if n>=8 else 'insufficient_visible_rays')
def frac(s):return Fraction(s['numerator'],s['denominator'])
def bad(s,q):return s['reason'] is None and frac(s)>frac(q)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();cap=a.results/'capture';records=json.loads((cap/'record.json').read_bytes());plan=json.loads((HERE/'plan.json').read_bytes());analysis=json.loads((a.results/'analysis_sheng.json').read_bytes());manifest=json.loads((cap/'manifest.json').read_bytes());index={(x['id'],x['stride']):x for x in analysis['rows']};byid={e['id']:e for e in plan}
    assert len(plan)==234 and len(byid)==234
    for f in ('plan.json','PROTOCOL.md','model.py','capture.py'):
        key={'PROTOCOL.md':'protocol','capture.py':'source','plan.json':'plan','model.py':'model'}[f]+'_sha256';assert sha(HERE/f)==manifest[key]
    assert analysis['capture_manifest_sha256']==sha(cap/'manifest.json')
    for bp in sorted({e['blueprint'] for e in plan}):
        for split,n in [('calibration',19),('test',20)]:
            ee=[e for e in plan if e['blueprint']==bp and e['split']==split];assert len(ee)==n;g=np.random.Generator(np.random.PCG64(ee[0]['seed']))
            for i,e in enumerate(ee):
                assert e['index']==i;assert [e[k] for k in ('longitudinal_m','lateral_m','yaw_deg')]==[float(g.uniform(-1.5,1.5)),float(g.uniform(-.5,.5)),float(g.uniform(0,360))]
    frameids=[];count=0;rays=0;ownreturns=0
    for rec in records:
        assert rec['episode']==byid[rec['episode']['id']]
        if rec['status']!='captured':continue
        assert rec['layout'] in (0,1);assert rec['frame']==rec['sensor_frame']==rec['snapshot_frame'];assert rec['timestamp']==rec['snapshot_timestamp'];frameids.append(rec['frame']);f=cap/rec['cloud_file'];assert sha(f)==rec['cloud_sha256']
        with np.load(f) as z:
            raw=z['raw'];assert raw.dtype.itemsize==24 and raw.dtype.names==('x','y','z','cos','id','tag');origin=np.asarray(rec['sensor_transform']['location']);r=rot(rec['sensor_transform']['rotation']);xyz=np.c_[raw['x'],raw['y'],raw['z']].astype(float)@r.T+origin;np.testing.assert_allclose(z['transform'][:3,:3],r,atol=2e-15,rtol=0);np.testing.assert_array_equal(z['origin'],origin);assert float(z['timestamp'])==rec['timestamp']
        rays+=len(raw);ownreturns+=int(np.sum(raw['id']==rec['actor_id']));assert int(np.sum(raw['id']==rec['actor_id']))==rec['actor_returns'];assert len(raw)==rec['points']
        ar=rot(rec['actor_transform']['rotation']);bb=rec['bounding_box'];center=np.asarray(rec['center']);np.testing.assert_allclose(np.asarray(bb['location'])@ar.T+rec['actor_transform']['location'],center,rtol=0,atol=2e-5);np.testing.assert_allclose(rec['actor_transform']['matrix'],rec['snapshot_transform']['matrix'],rtol=0,atol=1e-6);rotation=ar@rot(bb['rotation']);y=math.radians(rec['road_yaw']);forward=np.array([math.cos(y),math.sin(y),0]);side=np.array([-math.sin(y),math.cos(y),0]);centers=[center]+[center+x*forward+z*side for x in (-6.,-3.,3.,6.) for z in (-3.,3.)]
        for stride in (1,4,16):
            row=index[(rec['id'],stride)];assert row['episode_id']==rec['episode']['id'] and row['split']==rec['episode']['split'] and row['layout']==rec['layout'] and row['blueprint']==rec['blueprint'];assert row['points']==len(xyz[::stride])
            for c,tested in zip(centers,[row['truth']]+row['translated']):
                ref=reference(xyz[::stride],origin,c,rotation,bb['extent']);assert ref==tested,(rec['id'],stride,ref,tested);count+=1
        if len(frameids)%40==0:print('audited',len(frameids),flush=True)
    assert len(set(frameids))==len(frameids);assert len(index)==3*len(frameids)==len(analysis['rows']);assert manifest['captured']==len(frameids)
    summaries=[]
    for bp,methods in analysis['summary'].items():
        cal=[e for e in plan if e['blueprint']==bp and e['split']=='calibration'];te=[e for e in plan if e['blueprint']==bp and e['split']=='test']
        for method,s in methods.items():
            q=s['threshold']
            if method=='solid_box':assert frac(q)==0
            else:
                ss=[]
                for e in cal:
                    rr=[r for r in analysis['rows'] if r['episode_id']==e['id'] and (method=='joint' or r['stride']==1)]
                    ss.append(max(frac(r['truth']) for r in rr) if len(rr)==(6 if method=='joint' else 2) else Fraction(1))
                assert q['n']==19 and q['rank']==19 and frac(q)==sorted(ss)[18];assert q['vacuous']==(frac(q)==1)
            rr=[r for r in analysis['rows'] if r['blueprint']==bp and r['split']=='test'];badids=[e['id'] for e in te if any(bad(r['truth'],q) for r in rr if r['episode_id']==e['id'])];assert badids==s['false_exclusion_episode_ids'];assert sum(bad(r['truth'],q) for r in rr)==s['true_hypothesis_rejections'];assert sum(bad(t,q) for r in rr for t in r['translated'])==s['translated_rejections'];assert sum(len(r['translated']) for r in rr)==s['translated_total'];assert sum(r['truth']['reason'] is None for r in rr)==s['supported_true_cases']
            complete=sum(sum(r['episode_id']==e['id'] for r in rr)==6 for e in te);assert complete==s['available_episodes'];k=len(badids);ub=(1. if k==20 else float(beta.ppf(.95,k+1,20-k))) if complete==20 else None;assert ub==s['one_sided_95_upper'];summaries.append(dict(blueprint=bp,method=method,false_exclusions=k,available=complete,threshold=str(frac(q))))
    assert json.loads((cap/'cleanup.json').read_bytes())==dict(vehicles=0,walkers=0,sensors=0,synchronous=False)
    result=dict(episodes=len(plan),frames=len(frameids),raw_rays=rays,actor_returns=ownreturns,independent_box_checks=count,summary=summaries,analysis_sha256=sha(a.results/'analysis_sheng.json'),capture_manifest_sha256=sha(cap/'manifest.json'),audit_source_sha256=sha(Path(__file__)),scope='Independent six-face intersections, draw/split hashes, same-frame labels and exact quantiles; statistical exchangeability and physical sensor validity are assumptions, not audit conclusions.')
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('summary','scope')}))
if __name__=='__main__':main()
