#!/usr/bin/env python3
"""Post-result hypothesis: all observed component points bound a known body center.
No expiry/online authority is created. Labels serve offline scoring only.
"""
import argparse,hashlib,json,math
from collections import defaultdict
from decimal import Decimal,localcontext
from pathlib import Path
import numpy as np
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def covered(groups,rad_um,true):
    if not groups:return True
    with localcontext() as ctx:
        ctx.prec=80;t=[Decimal.from_float(float(x))*1000000 for x in true];rr=rad_um*rad_um
        return any(all(sum((Decimal(int(p[j])*10000)-t[j])**2 for j in (0,1))<=rr for p in g) for g in groups)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results;d=read(p/'analysis_sheng.json');background=read(p/'background.json');base=ROOT/'results/prospective_expiry_20261003';parent=read(base/'analysis_sheng.json');out=[];scores=defaultdict(float);catalog=d['catalog']
    for r,fr in zip(parent['rows'],d['rows']):
        assert r['id']==fr['id'];path=base/'capture'/r['cloud_file'];assert sha(path)==r['cloud_sha256']
        with np.load(path) as z:raw=z['raw'];xyz=np.c_[raw['x'],raw['y'],raw['z']].astype(float);T=z['transform']
        local=(xyz@T[:3,:3].T+T[:3,3]-r['anchor'])@np.array(r['road']);ext=catalog[r['blueprint']];mask=(abs(local[:,0])<=12)&(abs(local[:,1])<=8)&(local[:,2]>.3)&(local[:,2]<2*ext[2]+.3)
        g=np.floor(local*10).astype(np.int64);code=(g[:,0]+120)*161*27+(g[:,1]+80)*27+g[:,2]-3;mask&=~((local[:,2]<3)&np.isin(code,background['layouts'][str(r['layout'])]['codes']))
        pp=local[mask];target=raw['id'][mask]==r['actor_id'];groups=[];details=[];body_um=math.ceil(math.sqrt(sum(x*x for x in ext))*1e6);point_radius_um=body_um+8000
        if len(pp):
            ij=np.floor(pp[:,:2]/.2).astype(int);offset=ij.min(0);ind=ij-offset;grid=np.zeros(tuple(ind.max(0)+1),bool);grid[tuple(ind.T)]=True;labels,n=ndimage.label(grid,np.ones((3,3),int));ll=labels[tuple(ind.T)]
            for k in range(1,n+1):
                pts=pp[ll==k];lo=pts.min(0);hi=pts.max(0)
                if len(pts)<3 or max(hi[:2]-lo[:2])>2*math.sqrt(sum(x*x for x in ext))+.2 or hi[2]-lo[2]>2*ext[2]+.2:continue
                cm=np.unique(np.rint(pts[:,:2]*100).astype(np.int32),axis=0);groups.append(cm.tolist());error=max(0.,float(np.max(np.linalg.norm(cm/100.-r['true_xy'],axis=1)))-point_radius_um/1e6)
                details.append(dict(points=len(pts),target_returns=int(target[ll==k].sum()),all_target=bool(target[ll==k].all()),quantized_points=len(cm),support_score_m=error))
        score=min(x['support_score_m'] for x in details) if details else 0.;scores[r['episode_id']]=max(scores[r['episode_id']],score)
        # Data retain complete component ball supports, not only a fitted centroid.
        out.append(dict(id=r['id'],episode_id=r['episode_id'],blueprint=r['blueprint'],split=r['split'],true_xy=r['true_xy'],body_um=body_um,point_quantization_allowance_um=8000,groups_cm=groups,group_diagnostics=details,score_m=score,centroid_model_covered=fr['variants'][0]['covered'],zero_slack_covered=covered(groups,point_radius_um,r['true_xy']),available=bool(groups)))
        if len(out)%500==0:print('supports',len(out),flush=True)
    registry={}
    for bp in catalog:
        ss=[scores[e['episode']['id']] for e in parent['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='calibration'];assert len(ss)==95;registry[bp]=dict(development_slack_um=math.ceil(max(ss)*1e6+1e-7),scope='Descriptive reused-data fit, no prospective risk bound')
    summary=[]
    for bp in catalog:
        rr=[r for r in out if r['blueprint']==bp and r['split']=='test'];bad=set();zero=set();fixed=set();narrow_bad=set()
        for r in rr:
            r['fitted_covered']=covered(r['groups_cm'],r['body_um']+8000+registry[bp]['development_slack_um'],r['true_xy'])
            if not r['fitted_covered']:bad.add(r['episode_id'])
            if not r['zero_slack_covered']:zero.add(r['episode_id'])
            if not r['centroid_model_covered']:narrow_bad.add(r['episode_id'])
            if not r['centroid_model_covered'] and r['fitted_covered'] and r['available']:fixed.add(r['episode_id'])
        summary.append(dict(blueprint=bp,captured_test_frames=len(rr),available_frames=sum(r['available'] for r in rr),scheduled_test_episodes=60,centroid_model_excluded_episodes=len(narrow_bad),zero_slack_excluded_episodes=len(zero),fitted_support_excluded_episodes=len(bad),fitted_support_excluded_episode_ids=sorted(bad),centroid_excluded_episodes_with_covered_support=len(fixed),**registry[bp]))
    result=dict(rows=out,registry=registry,summary=summary,source_sha256=sha(Path(__file__)),analysis_sha256=sha(p/'analysis_sheng.json'),background_sha256=sha(p/'background.json'),scope='Post-result hypothesis diagnostic: union of component-wise intersections of known-body enclosing discs around quantized current points. Offline scoring and Decimal true-center membership only. No computed distance/expiry, paid utility, new risk calibration, raw-world identifiability or completeness proof for unknown inventory.')
    a.out.write_text(json.dumps(result,separators=(',',':'))+'\n');print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
