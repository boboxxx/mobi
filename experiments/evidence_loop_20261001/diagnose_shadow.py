#!/usr/bin/env python3
"""Post-capture localization of unexcluded external-obstacle centers."""
import argparse,gzip,json,math,sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'body_evidence_20261001'))
import body
from strict import Receiver


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(exist_ok=True)
    p=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));c=body.Contract();records=[]
    for name in ['view0_current','view0_history']:
        root=a.capture/name;r=json.loads(gzip.decompress((root/'record.json.gz').read_bytes()));rx=Receiver(p,c,name,'Carla/Maps/Town10HD_Opt')
        for d in r['decisions']:
            cloud=np.load(root/'clouds'/(d['id']+'.npz'));scope=body.Scope(name,'Carla/Maps/Town10HD_Opt',tuple(d['query']),float(cloud['plane_z']));m=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
            if d['phase']=='warm':
                prior=rx.latest_region() if r['history'] else None
                if prior and not prior.established<=d['stamp']<prior.expires:prior=None
                assert (prior.identity if prior else None)==d['prior']
                o,rays,ref=body.encode_source(cloud['xyz'],cloud['origin'],d['stamp'],d['stamp']);projected=body.projections(o,rays,ref,p,scope,c)
                for n,pr in p.items():
                    cells=body.required(pr,m,.4);covered_by_prior=body.prior_covers(cells,scope,m,prior,pr,ref/1e6);missing=np.ones(len(cells),dtype=bool);res=projected[n];w=res['witnesses']@body.rotation(m.yaw)
                    for error in np.unique(res['error']):
                        radius=pr.r_min-error-pr.step/math.sqrt(2)-1e-9
                        if radius<=0:continue
                        todo=np.flatnonzero(missing)
                        if not len(todo):break
                        group=np.flatnonzero(res['error']==error);dist,_=cKDTree(w[group]).query(cells[todo],k=1);missing[todo[dist<radius]]=False
                    after=missing&~covered_by_prior;remain=cells[after]
                    np.savez_compressed(a.out/(name+'_'+n+'.npz'),missing_centers=remain,ray_only_missing=cells[missing],witnesses=w,prior_excluded=cells[covered_by_prior])
                    records.append(dict(run=name,frame=d['frame'],class_name=n,prior_available=prior is not None,prior_remaining_at_observation_s=prior.expires-d['stamp'] if prior else None,required_cells=len(cells),unexcluded_current_only=int(missing.sum()),excluded_by_prior=int(covered_by_prior.sum()),unexcluded_with_valid_prior=int(after.sum()),missing_min=remain.min(axis=0).tolist() if len(remain) else None,missing_max=remain.max(axis=0).tolist() if len(remain) else None))
                break
            if d['receiver_accepted']:
                assert rx.accept((root/'packets'/(d['id']+'.json')).read_bytes(),scope,m,d['receiver_check_time'])
    (a.out/'report.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps(records,indent=2))


if __name__=='__main__':main()
