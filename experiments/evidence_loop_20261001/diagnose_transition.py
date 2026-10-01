#!/usr/bin/env python3
"""Localize why a previous support proposal fails on the second ego frame."""
import argparse,gzip,json,math,sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from fast_path import body,nearest
from renew import support
from strict import Receiver
from compress import pack


def missing_cells(res,pr,scope,m,prior,reference):
    cells=body.required(pr,m,.4);missing=~body.prior_covers(cells,scope,m,prior,pr,reference);w=res['witnesses']@body.rotation(m.yaw)
    for error in np.unique(res['error']):
        radius=pr.r_min-error-pr.step/math.sqrt(2)-1e-9
        if radius<=0:continue
        todo=np.flatnonzero(missing)
        if not len(todo):break
        group=np.flatnonzero(res['error']==error);dist,_=cKDTree(w[group]).query(cells[todo],k=1);missing[todo[dist<radius]]=False
    return cells[missing]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(exist_ok=True)
    name='view0_history';root=a.capture/name;record=json.loads(gzip.decompress((root/'record.json.gz').read_bytes()));p=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));c=body.Contract();rx=Receiver(p,c,name,'Carla/Maps/Town10HD_Opt');template=None
    for d in record['decisions']:
        cloud=np.load(root/'clouds'/(d['id']+'.npz'));sc=body.Scope(name,'Carla/Maps/Town10HD_Opt',tuple(d['query']),float(cloud['plane_z']));m=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
        if d['phase']=='warm' and d['index']==1:
            prior=rx.latest_region();assert prior and prior.established<=d['stamp']<prior.expires and prior.identity==d['prior'];o,r,ref=body.encode_source(cloud['xyz'],cloud['origin'],d['stamp'],d['stamp']);full=body.projections(o,r,ref,p,sc,c);first=full['small'];w=first['witnesses']@body.rotation(m.yaw);old=support(template,tuple(p.items()),c);j,_=nearest(w,old);selected=np.unique(first['ray_indices'][j]);sub=body.projections(o,r[selected],ref,p,sc,c);stats={}
            for n,pr in p.items():
                missing=missing_cells(sub[n],pr,sc,m,prior,ref/1e6);all_missing=missing_cells(full[n],pr,sc,m,prior,ref/1e6);stats[n]=dict(proposal_unexcluded=len(missing),full_ray_unexcluded=len(all_missing));np.savez_compressed(a.out/(n+'.npz'),proposal_missing=missing,full_missing=all_missing,witnesses=full[n]['witnesses']@body.rotation(m.yaw))
            b=pack(cloud['xyz'],cloud['origin'],d['stamp'],d['stamp'],p,sc,c,m,prior,.4,d['sequence']);assert b is not None
            report=dict(run=name,id=d['id'],prior_remaining_s=prior.expires-d['stamp'],proposal_rays=len(selected),classes=stats,actual_source_mode=d['source_mode'],actual_generation_ms=1000*d['generation_s'],actual_effective_age_ms=1000*(d['now']-d['stamp']),actual_geometry=d['geometry'],actual_available=d['available'],scope='Saved-data causal-stage diagnostic: full rays plus valid prior can prove geometry, previous support proposal cannot; no changed safety assumptions or new live run.')
            (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return
        if d['packet_sha256']:template=(root/'packets'/(d['id']+'.json')).read_bytes()
        if d['receiver_accepted']:assert rx.accept(template,sc,m,d['receiver_check_time'])
    raise RuntimeError('Expected archived transition missing')


if __name__=='__main__':main()
