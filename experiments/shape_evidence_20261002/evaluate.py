#!/usr/bin/env python3
"""Frozen shape scoring; labels define evaluation targets, never ray selection."""
import argparse, hashlib, json, math, time
from fractions import Fraction
from pathlib import Path
import numpy as np
from scipy.stats import beta
from model import score, fraction, threshold, rejected, STRIDES
from availability import family_assessment

HERE=Path(__file__).resolve().parent
OFFSETS=[(x,y) for x in (-6.,-3.,3.,6.) for y in (-3.,3.)]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rotation(pitch,yaw,roll):
    p,y,r=np.deg2rad([pitch,yaw,roll]);cp,sp=np.cos(p),np.sin(p);cy,sy=np.cos(y),np.sin(y);cr,sr=np.cos(r),np.sin(r)
    return np.array([[cp*cy,cy*sp*sr-sy*cr,-cy*sp*cr-sy*sr],[cp*sy,sy*sp*sr+cy*cr,-sy*sp*cr+cy*sr],[sp,-cp*sr,cp*cr]])
def upper(k,n):return None if n==0 else (1. if k==n else float(beta.ppf(.95,k+1,n-k)))
def summarize(plan,rows,missing_score=Fraction(1)):
    byepisode={e['id']:[r for r in rows if r['episode_id']==e['id']] for e in plan}
    if missing_score==0:
        for episode_id,rr in byepisode.items():
            availability=family_assessment({(r['layout'],r['stride']):r['truth'] for r in rr},Fraction(1))
            if not availability['available']:byepisode[episode_id]=[]
    output={}
    for blueprint in sorted({e['blueprint'] for e in plan}):
        cal=[e for e in plan if e['blueprint']==blueprint and e['split']=='calibration'];test=[e for e in plan if e['blueprint']==blueprint and e['split']=='test']
        qs={}
        for name,strides in [('full_only',(1,)),('joint',STRIDES)]:
            ss=[]
            for e in cal:
                rr=[r for r in byepisode[e['id']] if r['stride'] in strides]
                ss.append(max(map(lambda r:fraction(r['truth']),rr)) if len(rr)==2*len(strides) else missing_score)
            qs[name]=threshold(ss)
        qs['solid_box']=dict(n=0,rank=0,numerator=0,denominator=1,vacuous=False)
        methods={}
        for name,q in qs.items():
            bad=[];available=0;true_rejected=0;support=0;utility_rejected=0;utility_supported=0;utility_total=0
            per_stride={str(s):dict(true_rejected=0,total=0,utility_rejected=0,utility_total=0) for s in STRIDES}
            for e in test:
                rr=byepisode[e['id']];complete=len(rr)==2*len(STRIDES)
                if complete:available+=1
                if any(rejected(r['truth'],q) for r in rr):bad.append(e['id'])
                for r in rr:
                    tr=rejected(r['truth'],q);true_rejected+=tr;support+=r['truth']['reason'] is None
                    u=sum(rejected(s,q) for s in r['translated']);utility_rejected+=u;utility_supported+=sum(s['reason'] is None for s in r['translated']);utility_total+=len(r['translated'])
                    z=per_stride[str(r['stride'])];z['true_rejected']+=tr;z['total']+=1;z['utility_rejected']+=u;z['utility_total']+=len(r['translated'])
            methods[name]=dict(threshold=q,test_episodes=len(test),available_episodes=available,false_exclusion_episodes=len(bad),false_exclusion_episode_ids=bad,one_sided_95_upper=upper(len(bad),available) if available==len(test) else None,true_hypothesis_rejections=true_rejected,supported_true_cases=support,translated_rejections=utility_rejected,translated_supported=utility_supported,translated_total=utility_total,per_stride=per_stride)
        output[blueprint]=methods
    return output
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',required=True,type=Path);ap.add_argument('--label',default='sheng');ap.add_argument('--availability-followup',action='store_true');a=ap.parse_args();protocol_root=HERE/'availability_followup' if a.availability_followup else HERE;capture=a.results/'capture';records=json.loads((capture/'record.json').read_bytes());plan=json.loads((protocol_root/'plan.json').read_bytes());rows=[];timings=[]
    for rec in records:
        if rec['status']!='captured':continue
        f=capture/rec['cloud_file'];assert sha(f)==rec['cloud_sha256']
        with np.load(f) as z:
            raw=z['raw'];xyz=np.c_[raw['x'],raw['y'],raw['z']].astype(float)@z['transform'][:3,:3].T+z['origin'];origin=z['origin']
        center=np.asarray(rec['center']);rot=np.asarray(rec['actor_transform']['matrix'])[:3,:3]@rotation(*rec['bounding_box']['rotation']);ext=rec['bounding_box']['extent'];theta=math.radians(rec['road_yaw']);forward=np.array([math.cos(theta),math.sin(theta),0.]);side=np.array([-math.sin(theta),math.cos(theta),0.])
        for stride in STRIDES:
            p=xyz[::stride];t=time.perf_counter_ns();true=score(p,origin,center,rot,ext);ns=time.perf_counter_ns()-t
            translated=[score(p,origin,center+x*forward+y*side,rot,ext) for x,y in OFFSETS]
            rows.append(dict(id=rec['id'],episode_id=rec['episode']['id'],blueprint=rec['blueprint'],split=rec['episode']['split'],layout=rec['layout'],stride=stride,points=len(p),truth=true,translated=translated));timings.append(dict(id=rec['id'],stride=stride,truth_score_ns=ns))
        if len(rows)%60==0:print('scored',len(rows),flush=True)
    result=dict(schema=1,plan_sha256=sha(protocol_root/'plan.json'),protocol_sha256=sha(protocol_root/'PROTOCOL.md'),model_sha256=sha(HERE/'model.py'),capture_manifest_sha256=sha(capture/'manifest.json'),summary=summarize(plan,rows,Fraction(0) if a.availability_followup else Fraction(1)),rows=rows,scope='Ideal frozen-pose shape-hypothesis retention and truth-referenced translated-hypothesis diagnostic; not free-space grants or physical TTL validation.')
    (a.results/('analysis_'+a.label+'.json')).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');(a.results/('timings_'+a.label+'.json')).write_text(json.dumps(timings,indent=2)+'\n')
    print(json.dumps(result['summary'],indent=2))
if __name__=='__main__':main()
