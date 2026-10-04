#!/usr/bin/env python3
"""Offline-only raw-backed witnesses for the parent max-score calibration rows."""
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();base=ROOT/'results/prospective_expiry_20261003';d=json.loads((base/'analysis_sheng.json').read_bytes());out=[]
    for bp,ext in d['contract_body']['catalog'].items():
        r=max((r for r in d['rows'] if r['blueprint']==bp and r['split']=='calibration'),key=lambda r:r['residual_m']);p=base/'capture'/r['cloud_file'];assert sha(p)==r['cloud_sha256']
        with np.load(p) as z:raw=z['raw'];xyz=np.c_[raw['x'],raw['y'],raw['z']].astype(float);T=z['transform']
        local=(xyz@T[:3,:3].T+T[:3,3]-r['anchor'])@np.asarray(r['road']);mask=(abs(local[:,0])<=12)&(abs(local[:,1])<=8)&(local[:,2]>.3)&(local[:,2]<2*ext[2]+.3);points=local[mask];target=raw['id'][mask]==r['actor_id'];g=np.floor(points[:,:2]/.2).astype(int);offset=g.min(0);idx=g-offset;grid=np.zeros(tuple(idx.max(0)+1),bool);grid[tuple(idx.T)]=True;labels,n=ndimage.label(grid,np.ones((3,3),int));ll=labels[tuple(idx.T)];groups=[]
        for i in range(1,n+1):
            pp=points[ll==i];lo=pp.min(0);hi=pp.max(0);retained=len(pp)>=3 and max(hi[:2]-lo[:2])<=2*math.sqrt(sum(e*e for e in ext))+.2 and hi[2]-lo[2]<=2*ext[2]+.2
            groups.append(dict(points=len(pp),target_returns=int(target[ll==i].sum()),span_m=[round(float(x),9) for x in hi-lo],observed_box_midpoint=[round(float(x),9) for x in (lo+hi)/2],retained=bool(retained)))
        out.append(dict(id=r['id'],blueprint=bp,residual_m=r['residual_m'],true_xy=r['true_xy'],actor_returns=r['actor_returns'],selected_target_returns=int(target.sum()),cloud_file=str(p.relative_to(ROOT)),cloud_sha256=sha(p),groups=groups))
    a.out.write_text(json.dumps(dict(rows=out,source_sha256=sha(Path(__file__)),parent_analysis_sha256=sha(base/'analysis_sheng.json'),scope='Offline parent frontend failure witnesses, IDs only after raster grouping; not online detection, risk qualification or threshold tuning.'),indent=2)+'\n')
if __name__=='__main__':main()
