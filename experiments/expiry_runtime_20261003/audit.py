#!/usr/bin/env python3
"""Independent geometry, count, partition and timestamp audit of native proofs."""
import argparse,ctypes as C,hashlib,importlib.util,json,math,struct,subprocess,zlib
from pathlib import Path
from fractions import Fraction
import numpy as np
from scipy.spatial import cKDTree
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
old=load('pose_reference',ROOT/'experiments/pose_inversion_20261003/audit.py')

def reject(c,q):
 n,m,k,h=map(int,c);return m>=8 and max(Fraction(k,n),Fraction(max(0,m-h),m))>q
class Reference:
 def __init__(self,world,origin,lib):
  self.world=np.ascontiguousarray(world);self.origin=np.ascontiguousarray(origin);self.lib=lib;d=world-origin;length=np.linalg.norm(d,axis=1);self.nonzero=np.flatnonzero(length>1e-12);self.tree=cKDTree(d[self.nonzero]/length[self.nonzero,None]);self.point_checks=0;self.full_checks=0
 def counts(self,b,full=False):
  center,r,inner,outer=b;o=(self.origin-center)@r
  if np.any(inner<=0) or np.all(abs(o)<=outer):return np.zeros((2,4),np.int64)
  distance=np.linalg.norm(center-self.origin);radius=np.linalg.norm(outer)+1e-5
  if full or distance<=radius:ids=np.arange(len(self.world),dtype=np.int64)
  else:
   chord=np.sqrt(max(0,2*(1-np.sqrt(max(0,1-(radius/distance)**2)))))+1e-8;ids=np.ascontiguousarray(self.nonzero[np.asarray(self.tree.query_ball_point((center-self.origin)/distance,chord),dtype=int)],dtype=np.int64)
  normals=np.ascontiguousarray(np.r_[r.T,-r.T,[[0,0,-1]]]);small=np.ascontiguousarray(np.r_[r.T@center+inner,-r.T@center+inner,-.15]);large=np.ascontiguousarray(np.r_[r.T@center+outer,-r.T@center+outer,-.15]);answer=np.zeros((2,4),np.int64);self.lib.reference_counts(self.world,ids,len(ids),self.origin,normals,small,large,answer);self.point_checks+=len(ids);self.full_checks+=int(full);return answer

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();libpath=Path('/tmp/mobi_expiry_reference.so');subprocess.run(['c++','-O3','-std=c++17','-ffp-contract=off','-shared','-fPIC',str(HERE/'reference.cpp'),'-o',str(libpath)],check=True);lib=C.CDLL(str(libpath));f64=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');i64=np.ctypeslib.ndpointer(dtype=np.int64,flags='C_CONTIGUOUS');lib.reference_counts.argtypes=[f64,i64,C.c_int,f64,f64,f64,f64,i64]
 data=json.loads((ROOT/'results/terrain_score_20261003/analysis_sheng.json').read_bytes());sources={s['case']:s for s in json.loads((ROOT/'results/pose_inversion_20261003/replay/sources.json').read_bytes())};rows=json.loads((a.results/'rows.json').read_bytes());warm=json.loads((a.results/'warm.json').read_bytes());manifest=json.loads((a.results/'manifest.json').read_bytes());header=struct.Struct('<4sHHIIHHd16d32sI');packets={};references={};totalnodes=0;excluded=0;warmcounts=0;geometry_checks=0;fingerprints=[]
 for path,sha in manifest['source_hashes'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha,path
 for row in rows:
  s=sources[row['case']];payload=zlib.decompress((a.results/row['packet']).read_bytes());assert hashlib.sha256(payload).hexdigest()==row['packet_sha256'];assert hashlib.sha256(payload[:-32]).digest()==payload[-32:];h=header.unpack(payload[:header.size]);assert h[:2]==(b'PIV1',1) and h[3]==s['source_frame'] and h[5]==4 and h[7]==s['source_timestamp'] and h[24].hex()==manifest['analysis_sha256'];matrix=np.array(h[8:24]).reshape(4,4);xyz=np.frombuffer(payload,dtype='<f4',offset=header.size,count=h[25]*3).reshape(-1,3)
  if row['case'] not in packets:
   with np.load(ROOT/s['source_cloud']) as z:raw=z['raw'];np.testing.assert_array_equal(xyz,np.c_[raw['x'],raw['y'],raw['z']][::4]);np.testing.assert_array_equal(matrix,z['transform']);assert len(raw)==h[4]
   world=xyz.astype(float)@matrix[:3,:3].T+matrix[:3,3];packets[row['case']]=(payload,world,matrix);references[row['case']]=Reference(world,matrix[:3,3],lib)
  ref=references[row['case']];blob=(a.results/row['proof']).read_bytes();assert hashlib.sha256(blob).hexdigest()==row['proof_sha256'];proof=np.load(a.results/row['proof']);cells=proof['cells'];meta=proof['meta'];counts=proof['counts'];n=len(cells);totalnodes+=n;assert n==row['nodes'];q=Fraction(**data['summary'][s['blueprint']]['threshold']);ext=np.array(s['extent']);road=np.array(s['road_rotation']);anchor=np.array(s['anchor']);query=np.array([(-6 if row['query_index']==0 else 6),0]);radius=math.ceil(float(np.linalg.norm(ext))*1e6);np.testing.assert_array_equal(cells[0,:6],[-12,-8,ext[2]-.1,math.radians(-2),0,math.radians(-2)]);np.testing.assert_array_equal(cells[0,6:],[12,8,ext[2]+.1,math.radians(2),2*math.pi,math.radians(2)]);seen=[];lower=[];geos={}
  for i,(cell,m,cc) in enumerate(zip(cells,meta,counts)):
   lo,hi=cell[:6],cell[6:];assert np.all(lo<=hi);d=np.maximum(np.maximum(lo[:2]-query,query-hi[:2]),0);du=np.maximum(np.floor(d*1e6-1e-7),0).astype(np.int64);assert old.contact(*du,radius)[0]==m[4]
   if m[3]==1:
    left,right=int(m[1]),int(m[2]);seen += [left,right];assert meta[left,0]==meta[right,0]==i;aa,bb=cells[left],cells[right];np.testing.assert_array_equal(aa[:6],lo);np.testing.assert_array_equal(bb[6:],hi);axis=np.flatnonzero(aa[6:]!=hi);assert len(axis)==1;j=axis[0];assert aa[6+j]==bb[j] and lo[j]<aa[6+j]<hi[j];np.testing.assert_array_equal(np.delete(bb[:6],j),np.delete(lo,j))
   elif m[3]!=2:lower.append(int(m[4]))
   if m[3] in (1,2,4):
    b=old.boxes(dict(lo=lo.tolist(),hi=hi.tolist()),ext,anchor,road,True);expected=ref.counts(b);np.testing.assert_array_equal(expected,cc);geometry_checks+=1
    # Deterministic full-cloud cross-check of the broader reference cone.
    if i%997==0:np.testing.assert_array_equal(ref.counts(b,True),expected)
    if m[3]==2:assert any(reject(c,q) for c in expected);excluded+=1;geos[i]=b
   else:assert not np.any(cc)
  assert sorted(seen)==list(range(1,n));dist=min(query[0]+12,12-query[0],query[1]+8,8-query[1]);outlo=old.contact(max(0,math.floor(dist*1e6-1e-7)),0,radius)[0];outup=old.contact(math.ceil(dist*1e6+1e-7),0,radius)[1];assert row['lower_us']==min([outlo]+lower);assert row['upper_us']==outup;assert row['excluded']==int((meta[:,3]==2).sum());fingerprints.append(dict(case=row['case'],query=row['query_index'],nodes=n,lower_us=row['lower_us'],upper_us=outup))
  if s['episode_index']==0:
   w=next(w for w in warm if w['old_case']==row['case'] and w['query_index']==row['query_index']);current=sources[w['current_case']];newpayload=zlib.decompress((a.results/w['current_packet']).read_bytes());nh=header.unpack(newpayload[:header.size]);nm=np.array(nh[8:24]).reshape(4,4);np.testing.assert_array_equal(nm,matrix);assert nh[3]>h[3] and nh[7]>h[7] and nh[7]==w['current_timestamp'];newxyz=np.frombuffer(newpayload,dtype='<f4',offset=header.size,count=nh[25]*3).reshape(-1,3)
   with np.load(ROOT/current['source_cloud']) as z:np.testing.assert_array_equal(newxyz,np.c_[z['raw']['x'],z['raw']['y'],z['raw']['z']][::4]);assert float(z['timestamp'])==nh[7]
   newworld=newxyz.astype(float)@nm[:3,:3].T+nm[:3,3];newref=Reference(newworld,nm[:3,3],lib);result=np.load(a.results/w['output']);status=result['accepted'];newcounts=result['counts'];remaining=[];revoked=0
   for i in range(n):
    if meta[i,3]==1:assert status[i]==-1;continue
    if meta[i,3]==2:
     expected=newref.counts(geos[i]);np.testing.assert_array_equal(expected,newcounts[i]);warmcounts+=1;is_excluded=any(reject(c,q) for c in expected);assert status[i]==int(is_excluded);revoked+=not is_excluded
    else:assert status[i]==0 and not np.any(newcounts[i])
    if status[i]==0:remaining.append(int(meta[i,4]))
   assert w['lower_us']==min([outlo]+remaining) and w['upper_us']==outup and w['revoked']==revoked;references['warm:'+row['case']+str(row['query_index'])]=newref
  print('checked',row['case'],row['query_index'],flush=True)
 out=dict(cold_calls=len(rows),warm_calls=len(warm),partition_nodes=totalnodes,cold_geometry_checks=geometry_checks,excluded_cells=excluded,warm_excluded_cell_rechecks=warmcounts,reference_candidate_point_checks=sum(r.point_checks for r in references.values()),full_cloud_cone_crosschecks=sum(r.full_checks for r in references.values()),reference_prefilter='Independent SciPy KD-tree with inflated outer-sphere cone; all selected rays tested by separately compiled world-plane reference. Deterministic full-cloud checks supplement the real-arithmetic cone-inclusion derivation; float guards are not formal rounding.',fingerprints=fingerprints,rows_sha256=hashlib.sha256((a.results/'rows.json').read_bytes()).hexdigest(),warm_sha256=hashlib.sha256((a.results/'warm.json').read_bytes()).hexdigest(),audit_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),reference_sha256=hashlib.sha256((HERE/'reference.cpp').read_bytes()).hexdigest());a.out.write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
