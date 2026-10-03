#!/usr/bin/env python3
"""Posthoc actual target-return support check; labels never enter prediction."""
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results;d=json.loads((p/'analysis_sheng.json').read_bytes());catalog=d['contract_body']['catalog'];out=[]
    for r in d['rows']:
        path=p/'capture'/r['cloud_file'];assert sha(path)==r['cloud_sha256']
        with np.load(path) as z:raw=z['raw'];matrix=z['transform']
        target=raw[raw['id']==r['actor_id']];ext=catalog[r['blueprint']];body=math.ceil(math.sqrt(sum(v*v for v in ext))*1e6)
        if len(target):
            xyz=np.c_[target['x'],target['y'],target['z']].astype(float);world=xyz[:,0,None]*matrix[:3,0]+xyz[:,1,None]*matrix[:3,1]+xyz[:,2,None]*matrix[:3,2]+matrix[:3,3];delta=world-np.array(r['center']);xy=np.sqrt(delta[:,0]*delta[:,0]+delta[:,1]*delta[:,1])*1e6;spatial=np.sqrt(np.sum(delta*delta,axis=1))*1e6;xy_excess=max(0.,float(np.max(xy))-body);spatial_excess=max(0.,float(np.max(spatial))-body)
            bad_xy=int(np.sum(xy>body));bad_spatial=int(np.sum(spatial>body))
        else:xy_excess=spatial_excess=0.;bad_xy=bad_spatial=0
        out.append(dict(id=r['id'],blueprint=r['blueprint'],split=r['split'],target_returns=len(target),body_um=body,xy_outside_returns=bad_xy,spatial_outside_returns=bad_spatial,max_xy_excess_um=round(xy_excess,6),max_spatial_excess_um=round(spatial_excess,6)))
    result=dict(rows=out,summary=[dict(blueprint=bp,frames=sum(r['blueprint']==bp for r in out),frames_without_target_returns=sum(r['blueprint']==bp and not r['target_returns'] for r in out),xy_outside_frames=sum(r['blueprint']==bp and r['xy_outside_returns']>0 for r in out),spatial_outside_frames=sum(r['blueprint']==bp and r['spatial_outside_returns']>0 for r in out),max_xy_excess_um=max([r['max_xy_excess_um'] for r in out if r['blueprint']==bp]+[0]),max_spatial_excess_um=max([r['max_spatial_excess_um'] for r in out if r['blueprint']==bp]+[0])) for bp in catalog],source_sha256=sha(Path(__file__)),analysis_sha256=sha(p/'analysis_sheng.json'),scope='Posthoc semantic-ID identification of actually returned target surface points against the declared enclosing body sphere/disc. Uses ALL retained target returns, not discarded original returns. Finite observed support only; no unseen surface, complete inventory or continuous physical safety proof.')
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary']))
if __name__=='__main__':main()
