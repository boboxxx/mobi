#!/usr/bin/env python3
"""Independent raw-byte/pose/corner audit; no tested geometric module imports."""
import argparse,hashlib,itertools,json,math
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull,distance
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rotation(pitch,yaw,roll):
 p,y,r=map(math.radians,[pitch,yaw,roll]);cp,sp=math.cos(p),math.sin(p);cy,sy=math.cos(y),math.sin(y);cr,sr=math.cos(r),math.sin(r)
 return np.array([[cp*cy,cy*sp*sr-sy*cr,-cy*sp*cr-sy*sr],[cp*sy,sy*sp*sr+cy*cr,-sy*sp*cr+cy*sr],[sp,-cp*sr,cp*cr]])
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.results=a.results.resolve();capture=a.results/'capture';rows=json.loads((capture/'record.json').read_bytes());tested=json.loads((a.results/'analysis_sheng.json').read_bytes());manifest=json.loads((capture/'manifest.json').read_bytes());assert len(rows)==48 and manifest['captured']==48;assert sha(ROOT/'experiments/physical_contract_20261002/capture.py')==manifest['source_sha256'];assert sha(ROOT/'experiments/physical_contract_20261002/PROTOCOL.md')==manifest['protocol_sha256'];assert len({x['id'] for x in rows})==48
 corners=np.array(list(itertools.product([-1,1],repeat=3)));qc=np.array(list(itertools.product([-.01,.01],repeat=2)));out=[];totalrays=0;cornerchecks=0
 for row in rows:
  assert row['status']=='captured';x=next(x for x in tested['rows'] if x['id']==row['id']);p=capture/row['cloud_file'];assert sha(p)==row['cloud_sha256']
  with np.load(p) as z:raw=z['raw'];xyz=z['xyz'];origin=z['origin'];matrix=z['transform'];stamp=float(z['timestamp'])
  assert raw.dtype.names==('x','y','z','cos','id','tag') and raw.dtype.itemsize==24;assert len(raw)==row['points'];totalrays+=len(raw);loc=np.c_[raw['x'],raw['y'],raw['z']].astype(float);sensor=row['sensor_transform'];rot=rotation(*sensor['rotation']);reference=loc@rot.T+np.asarray(sensor['location']);np.testing.assert_allclose(xyz,reference,rtol=0,atol=2e-12);np.testing.assert_allclose(origin,sensor['location'],rtol=0,atol=0);np.testing.assert_allclose(matrix[:3,:3],rot,rtol=0,atol=2e-15)
  actor=row['actor_transform'];r=rotation(*actor['rotation']);bb=row['bounding_box'];c=np.asarray(bb['location'])@r.T+actor['location'];np.testing.assert_allclose(c,row['center'],rtol=0,atol=2e-5);center=np.asarray(row['center']);plane=row['plane_z'];query=np.asarray(row['query']);rmin,rmax,step=(.2,.4,.05) if row['klass']=='small' else (.55,2.5,.1);assert (x['r_min'],x['r_max'])==(rmin,rmax)
  ii=np.where((reference[:,2]<plane-1e-9)&(origin[2]>plane+1e-9))[0];f=(plane-origin[2])/(reference[ii,2]-origin[2]);w=origin[:2]+f[:,None]*(reference[ii,:2]-origin[:2]);dist=np.hypot(w[:,0]-center[0],w[:,1]-center[1]);j=np.argmin(dist);assert int(ii[j])==x['nearest_ray_index'];assert abs(dist[j]-x['nominal_min_crossing_distance_m'])<5.1e-10;assert x['nominal_contradiction']==(rmin-dist[j]>1e-7)
  idx=x['proof_ray_index'];endq=np.rint(reference[idx]/.001).astype(np.int64);oq=np.rint(origin/.001).astype(np.int64);assert x['proof_origin_integer']==oq.tolist();assert x['proof_ray_integer']==[0]+endq.tolist()+[math.floor(stamp*1e6)];assert x['reference_us']==math.ceil(stamp*1e6)
  o=oq*.001;end=endq*.001;t=(o[2]-plane)/(o[2]-end[2]);nom=o[:2]+t*(end[:2]-o[:2])-query;np.testing.assert_allclose(nom,x['proof_projected_local'],rtol=0,atol=2e-12)
  tile=np.asarray(x['tile_center_local']);assert np.max(np.abs(center[:2]-query-tile))<=step/2+1e-10;age=(x['reference_us']-x['proof_ray_integer'][4])/1e6;moving=5*age+1.5*age*age;maxdistance=0.;maxerror=0.
  for oc in o+corners*.0105:
   for ec in end+corners*.0105:
    assert ec[2]<plane<oc[2];u=(plane-oc[2])/(ec[2]-oc[2]);wc=oc[:2]+u*(ec[:2]-oc[:2])-query
    for qe in qc:
     ww=wc-qe;maxdistance=max(maxdistance,float(np.linalg.norm(ww-tile)));maxerror=max(maxerror,float(np.linalg.norm(ww-nom)));cornerchecks+=1
  assert maxerror+moving<=x['proof_error']+1e-9;computed=rmin-x['proof_error']-step/math.sqrt(2)-float(np.linalg.norm(nom-tile))-1e-9;assert abs(computed-x['receiver_margin_m'])<5.1e-10;assert x['receiver_excludes_actual_tile']==(computed>1e-7)
  if x['receiver_excludes_actual_tile']:assert maxdistance+step/math.sqrt(2)+moving<rmin-1e-7
  own=reference[raw['id']==row['actor_id']];assert len(own)==x['own_returns']==row['actor_returns'];rad=float(np.max(np.linalg.norm(own[:,:2]-center[:2],axis=1))) if len(own) else None;assert (rad is None and x['observed_outer_radius_m'] is None) or abs(rad-x['observed_outer_radius_m'])<5.1e-10;assert x['actual_return_outside_outer']==bool(rad is not None and rad>rmax+1e-5)
  hull=own[ConvexHull(own[:,:2]).vertices,:2] if len(own)>=3 else own[:,:2];diam=float(distance.pdist(hull).max()) if len(hull)>1 else 0.;out.append(dict(id=row['id'],robust_exclusion=x['receiver_excludes_actual_tile'],corner_margin_m=round(rmin-maxdistance-step/math.sqrt(2)-moving,8),actual_outer_failure=x['actual_return_outside_outer'],observed_diameter_m=round(diam,8),any_center_outer_impossible=diam>2*rmax+1e-5))
 cleanup=json.loads((capture/'cleanup.json').read_bytes());assert cleanup==dict(vehicles=0,walkers=0,sensors=0,synchronous=False)
 result=dict(frames=len(rows),raw_rays=totalrays,corner_checks=cornerchecks,robust_exclusions=sum(x['robust_exclusion'] for x in out),actual_outer_failures=sum(x['actual_outer_failure'] for x in out),any_center_outer_failures=sum(x['any_center_outer_impossible'] for x in out),rows=out,analysis_sha256=sha(a.results/'analysis_sheng.json'),capture_manifest_sha256=sha(capture/'manifest.json'),auditor_sha256=sha(Path(__file__)),scope='Independent sensor Euler transforms, frame/pose provenance, actual ray-plane crossings,256 perturbation corners per decisive ray, occupied tile and actor-labelled outer/diameter checks; no legacy geometry imports. Finite non-refutation is not calibration.')
 a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['rows','scope']}))
if __name__=='__main__':main()
