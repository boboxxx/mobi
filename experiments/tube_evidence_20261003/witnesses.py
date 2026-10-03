#!/usr/bin/env python3
"""Bounded post-replay search for compatible raw-score contact witnesses."""
import argparse,ctypes as C,hashlib,json,math,subprocess
from pathlib import Path
from fractions import Fraction
import numpy as np
from audit import ROOT,geo,terrain,unpack_full

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();p=a.results;cpp=ROOT/'experiments/expiry_runtime_20261003/reference.cpp';so='/tmp/mobi_tube_witness_reference.so';subprocess.run(['c++','-O3','-std=c++17','-ffp-contract=off','-shared','-fPIC',str(cpp),'-o',so],check=True);lib=C.CDLL(so);f64=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');i64=np.ctypeslib.ndpointer(dtype=np.int64,flags='C_CONTIGUOUS');lib.reference_counts.argtypes=[f64,i64,C.c_int,f64,f64,f64,f64,i64];sources={s['case']:s for s in json.loads((ROOT/'results/pose_inversion_20261003/replay/sources.json').read_bytes())};threshold=json.loads((ROOT/'results/terrain_score_20261003/analysis_sheng.json').read_bytes())['summary'];warm=json.loads((p/'warm.json').read_bytes());rows=[];tested=0;pointchecks=0;rescores=0
 for w in warm:
  source=sources[w['current_case']];q=Fraction(**threshold[w['blueprint']]['threshold']);_,_,_,points,m=unpack_full(p/w['current_packet']);points=np.ascontiguousarray(points);origin=np.ascontiguousarray(m[:3,3]);ids=np.arange(len(points),dtype=np.int64);ext=np.array(source['extent']);anchor=np.array(source['anchor']);road=np.array(source['road_rotation']);query=np.array([-6 if w['query_index']==0 else 6,0]);radius=math.ceil(np.linalg.norm(ext)*1e6)
  with np.load(p/w['proof']) as z:cells=z['cells']
  with np.load(p/w['output']) as z:kept=np.flatnonzero(z['accepted']==0)
  mid=(cells[kept,:6]+cells[kept,6:])/2;near=mid.copy();near[:,:2]=np.clip(query,cells[kept,:2],cells[kept,6:8]);candidates=[];seen=set()
  for poses in (mid,near):
   order=np.argsort(np.sum((poses[:,:2]-query)**2,axis=1),kind='stable')[:16]
   for j in order:
    pose=poses[j];key=pose.tobytes()
    if key not in seen:seen.add(key);candidates.append((int(kept[j]),pose))
  witnesses=[]
  for node,pose in candidates:
   center=anchor+road@pose[:3];r=geo.rotation(pose[3:]);normals=np.ascontiguousarray(np.r_[r.T,-r.T,[[0,0,-1]]]);offset=np.ascontiguousarray(np.r_[r.T@center+ext+.03,-r.T@center+ext+.03,-.15]);cc=np.zeros((2,4),np.int64);inside=np.all(offset-normals@origin>=0)
   if not inside:lib.reference_counts(points,ids,len(points),origin,normals,offset,offset,cc)
   scores=[Fraction(int(c[2]),int(c[0])) if c[0]>=8 else Fraction(0) for c in cc];tested+=1;pointchecks+=len(points)
   if all(s<=q for s in scores):
    actual=[terrain.reference(points[::step],origin,center,r,ext) for step in (4,1)];assert [Fraction(t[2],t[3]) for t in actual]==scores;rescores+=2;distance=math.ceil(float(np.linalg.norm((pose[:2]-query)*1e6))+1e-7);upper=geo.contact(distance,0,radius)[1];assert w['lower_us']<=upper,(w,pose,upper);witnesses.append(dict(node=node,pose=pose.tolist(),scores=[dict(numerator=s.numerator,denominator=s.denominator) for s in scores],distance_upper_um=distance,upper_us=upper))
  upper=min([w['upper_us']]+[x['upper_us'] for x in witnesses]);rows.append(dict(blueprint=w['blueprint'],query_index=w['query_index'],radius_um=w['radius_um'],sigma=w['sigma'],lower_us=w['lower_us'],old_upper_us=w['upper_us'],witness_upper_us=upper,gap_us=upper-w['lower_us'],tested=len(candidates),accepted=len(witnesses),witnesses=witnesses));print('witness',w['blueprint'],w['radius_um'],w['query_index'],w['sigma'],len(witnesses),upper,flush=True)
 out=dict(rows=rows,poses_tested=tested,candidate_point_checks=pointchecks,independent_python_rescores=rescores,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),protocol_sha256=hashlib.sha256((Path(__file__).parent/'WITNESS_PROTOCOL.md').read_bytes()).hexdigest(),scope='Post-replay diagnostic, all108 cases. All-ray exact score witnesses for the same abstract body-disc model. No physical mesh collision, unseen-object guarantee, online cost or optimality from failed search.');a.out.write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
