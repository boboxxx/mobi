#!/usr/bin/env python3
"""Independent world-plane, message coverage and continuous partition audit."""
import argparse,ctypes as C,hashlib,importlib.util,json,math,struct,subprocess,zlib
from pathlib import Path
from fractions import Fraction
import numpy as np
from scipy.spatial import cKDTree
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
geo=load('independent_pose_geometry',ROOT/'experiments/pose_inversion_20261003/audit.py')
terrain=load('independent_terrain',ROOT/'experiments/terrain_score_20261003/audit.py')
HEADER=struct.Struct('<4sHHIIHHd16d32sI');PREFIX=struct.Struct('<4sII32s');ENTRY=np.dtype([('index','<u4'),('xyz','<f4',(3,))])
def lower(c):
 n,m,k,h=map(int,c);return max(Fraction(k,n),Fraction(max(0,m-h),m)) if m>=8 else Fraction(0)
class Ref:
 def __init__(self,points,origin,lib):
  self.points=np.ascontiguousarray(points);self.origin=np.ascontiguousarray(origin);self.lib=lib;d=points-origin;length=np.linalg.norm(d,axis=1);self.nonzero=np.flatnonzero(length>1e-12);self.kd=cKDTree(d[self.nonzero]/length[self.nonzero,None]);self.examined=0;self.full_scans=0
 def count(self,b,epsilon,mask=None,full=False):
  center,r,inn,out=b;inside=np.all(abs((self.origin-center)@r)<=out);unresolved=np.any(inn<=0) or inside;delta=epsilon*(1+2e-10)+1e-9 if epsilon else 0;inn=inn-delta;out=out+delta;unresolved|=np.any(inn<=0) or np.all(abs((self.origin-center)@r)<=out)
  if unresolved:
   if epsilon:
    ids=np.arange(len(self.points)) if mask is None else np.flatnonzero(mask);return np.array([[len(ids[ids%4==0]),0,0,len(ids[ids%4==0])],[len(ids),0,0,len(ids)]],np.int64)
   return np.zeros((2,4),np.int64)
  v=center-self.origin;distance=np.linalg.norm(v);radius=np.linalg.norm(out)+1e-5
  if full or distance<=radius:ids=np.arange(len(self.points),dtype=np.int64)
  else:
   chord=np.sqrt(max(0,2*(1-np.sqrt(max(0,1-(radius/distance)**2)))))+1e-8;ids=self.nonzero[np.asarray(self.kd.query_ball_point(v/distance,chord),dtype=int)]
  if mask is not None:ids=ids[mask[ids]]
  ids=np.ascontiguousarray(ids,np.int64);normals=np.ascontiguousarray(np.r_[r.T,-r.T,[[0,0,-1]]]);small=np.ascontiguousarray(np.r_[r.T@center+inn,-r.T@center+inn,-.15-delta]);large=np.ascontiguousarray(np.r_[r.T@center+out,-r.T@center+out,-.15+delta]);answer=np.zeros((2,4),np.int64);self.lib.reference_counts(self.points,ids,len(ids),self.origin,normals,small,large,answer);self.examined+=len(ids);self.full_scans+=int(full);return answer

def unpack_full(path):
 packet=zlib.decompress(path.read_bytes());assert hashlib.sha256(packet[:-32]).digest()==packet[-32:];h=HEADER.unpack(packet[:HEADER.size]);xyz=np.frombuffer(packet,dtype='<f4',offset=HEADER.size,count=h[25]*3).reshape(-1,3);assert len(packet)==HEADER.size+12*h[25]+32;m=np.array(h[8:24]).reshape(4,4);return packet,h,xyz,xyz.astype(float)@m[:3,:3].T+m[:3,3],m

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);ap.add_argument('--radius',type=int);a=ap.parse_args();p=a.results;sourcecpp=ROOT/'experiments/expiry_runtime_20261003/reference.cpp';libpath=Path('/tmp/mobi_tube_reference.so');subprocess.run(['c++','-O3','-std=c++17','-ffp-contract=off','-shared','-fPIC',str(sourcecpp),'-o',str(libpath)],check=True);lib=C.CDLL(str(libpath));f64=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');i64=np.ctypeslib.ndpointer(dtype=np.int64,flags='C_CONTIGUOUS');lib.reference_counts.argtypes=[f64,i64,C.c_int,f64,f64,f64,f64,i64]
 manifest=json.loads((p/'manifest.json').read_bytes());analysispath=ROOT/'results/terrain_score_20261003/analysis_sheng.json';assert hashlib.sha256(analysispath.read_bytes()).hexdigest()==manifest['analysis_sha256'];analysis=json.loads(analysispath.read_bytes());sources={s['case']:s for s in json.loads((ROOT/'results/pose_inversion_20261003/replay/sources.json').read_bytes())};bps=sorted({s['blueprint'] for s in sources.values()});inputs=json.loads((p/'inputs.json').read_bytes());cold=json.loads((p/'cold.json').read_bytes());warm=json.loads((p/'warm.json').read_bytes());nodes_checked=0;cold_counts=0;warm_counts=0;dominance_checks=0;messages=0;pointchecks=0;fullscans=0;truth=[];fingerprints=[];tightness=[]
 for name,sha in manifest['source_hashes'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
 verified_inputs={}
 for inp in inputs:
  source=sources[inp['case']];packet,h,xyz,world,m=unpack_full(p/inp['packet']);assert hashlib.sha256(packet).hexdigest()==inp['packet_sha256'];assert h[3]==source['source_frame'] and h[7]==source['source_timestamp'] and h[24].hex()==manifest['analysis_sha256'];assert h[2]==bps.index(source['blueprint']) and h[5]==4
  with np.load(ROOT/source['source_cloud']) as z:raw=z['raw'];expected=np.c_[raw['x'],raw['y'],raw['z']];np.testing.assert_array_equal(m,z['transform'])
  if inp['sigma']:expected=(expected+np.random.default_rng(inp['seed']).normal(0,inp['sigma'],expected.shape)).astype('<f4')
  np.testing.assert_array_equal(xyz,expected[::4]);records=json.loads((ROOT/source['source_record']).read_bytes());tr=next(r for r in records if r.get('id')==source['source_id']);rotation=np.array(tr['actor_transform']['matrix'])[:3,:3]@geo.rotation(np.deg2rad(tr['bounding_box']['rotation']));scores=[]
  for stride in (16,4):
   n,k,nu,de=terrain.reference(world[::stride//4],m[:3,3],np.array(tr['center']),rotation,tr['bounding_box']['extent']);scores.append(dict(stride=stride,numerator=nu,denominator=de,visible=n,passed=k))
  q=Fraction(**analysis['summary'][source['blueprint']]['threshold']);truth.append(dict(blueprint=source['blueprint'],sigma=inp['sigma'],false_exclusion=any(Fraction(s['numerator'],s['denominator'])>q for s in scores),scores=scores));verified_inputs[(source['blueprint'],inp['sigma'])]=(packet,h,xyz,world,m)
 for row in cold:
  if a.radius is not None and row['radius_um']!=a.radius:continue
  bp=row['blueprint'];eps=row['radius_um']/1e6;source=next(s for s in sources.values() if s['blueprint']==bp and s['episode_index']==0);packet,h,xyz,world,m=unpack_full(p/row['reference']);assert hashlib.sha256(packet).hexdigest()==next(i['reference_sha256'] for i in inputs if i['blueprint']==bp)
  with np.load(ROOT/source['source_cloud']) as z:np.testing.assert_array_equal(xyz,np.c_[z['raw']['x'],z['raw']['y'],z['raw']['z']][::4]);np.testing.assert_array_equal(m,z['transform'])
  ref=Ref(world,m[:3,3],lib);assert hashlib.sha256((p/row['proof']).read_bytes()).hexdigest()==row['proof_sha256'];z=np.load(p/row['proof']);cells=z['cells'];meta=z['meta'];counts=z['counts'];ext=np.array(source['extent']);anchor=np.array(source['anchor']);road=np.array(source['road_rotation']);q=Fraction(**analysis['summary'][bp]['threshold']);query=np.array([(-6 if row['query_index']==0 else 6),0]);radius=math.ceil(float(np.linalg.norm(ext))*1e6);np.testing.assert_array_equal(cells[0,:6],[-12,-8,ext[2]-.1,math.radians(-2),0,math.radians(-2)]);np.testing.assert_array_equal(cells[0,6:],[12,8,ext[2]+.1,math.radians(2),2*math.pi,math.radians(2)]);children=[];retained=[];boxes={}
  for i,(cell,state,cc) in enumerate(zip(cells,meta,counts)):
   lo,hi=cell[:6],cell[6:];nodes_checked+=1;assert np.all(lo<=hi);d=np.maximum(np.maximum(lo[:2]-query,query-hi[:2]),0);du=np.maximum(np.floor(d*1e6-1e-7),0).astype(np.int64);assert state[4]==geo.contact(*du,radius)[0]
   if state[3]==1:
    l,r=int(state[1]),int(state[2]);children.extend([l,r]);assert meta[l,0]==meta[r,0]==i;aa,bb=cells[l],cells[r];np.testing.assert_array_equal(aa[:6],lo);np.testing.assert_array_equal(bb[6:],hi);axis=np.flatnonzero(aa[6:]!=hi);assert len(axis)==1;j=axis[0];assert aa[6+j]==bb[j] and lo[j]<aa[6+j]<hi[j];np.testing.assert_array_equal(np.delete(bb[:6],j),np.delete(lo,j))
   elif state[3]!=2:retained.append(int(state[4]))
   if state[3] in (1,2,4):
    b=geo.boxes(dict(lo=lo.tolist(),hi=hi.tolist()),ext,anchor,road,True);expected=ref.count(b,eps);np.testing.assert_array_equal(expected,cc);cold_counts+=1
    if i%4093==0:np.testing.assert_array_equal(expected,ref.count(b,eps,full=True))
    if state[3]==2:assert any(lower(c)>q for c in expected);boxes[i]=b
   else:assert not np.any(cc)
  assert sorted(children)==list(range(1,len(cells)));distance=min(query[0]+12,12-query[0],query[1]+8,8-query[1]);outlo=geo.contact(max(0,math.floor(distance*1e6-1e-7)),0,radius)[0];outup=geo.contact(math.ceil(distance*1e6+1e-7),0,radius)[1];assert row['lower_us']==min([outlo]+retained) and row['upper_us']==outup
  for w in [w for w in warm if w['proof']==row['proof']]:
   current,nh,nxyz,nworld,nm=verified_inputs[(bp,w['sigma'])];np.testing.assert_array_equal(nm,m);newref=Ref(nworld,nm[:3,3],lib);wire=(p/w['message']).read_bytes();assert len(wire)==w['wire_bytes'] and hashlib.sha256(wire).hexdigest()==w['message_sha256'];magic,size=struct.unpack('<4sI',wire[:8]);assert magic==b'TBZ1';body=zlib.decompress(wire[8:]);assert len(body)==size and hashlib.sha256(body[:-32]).digest()==body[-32:];magic,radius_um,k,rhash=PREFIX.unpack(body[:PREFIX.size]);assert magic==b'TUB1' and radius_um==row['radius_um'] and rhash==hashlib.sha256(packet).digest();assert body[PREFIX.size:PREFIX.size+HEADER.size]==current[:HEADER.size];assert nh[3]>h[3] and nh[7]>h[7] and nh[7]==w['source_timestamp'];assert len(body)==PREFIX.size+HEADER.size+16*k+32;entries=np.frombuffer(body,dtype=ENTRY,count=k,offset=PREFIX.size+HEADER.size);ids=entries['index'].astype(np.int64);assert len(ids)==w['exceptions'] and (not k or (ids[-1]<len(world) and np.all(ids[1:]>ids[:-1])));np.testing.assert_array_equal(entries['xyz'],nxyz[ids]);mask=np.ones(len(world),bool);mask[ids]=False
   if eps:
    delta=nworld[mask].astype(np.longdouble)-world[mask].astype(np.longdouble);assert np.all(np.sum(delta*delta,axis=1)<=np.longdouble(radius_um)**2/np.longdouble(1000000000000))
   else:np.testing.assert_array_equal(nxyz[mask].view(np.uint32),xyz[mask].view(np.uint32))
   assert hashlib.sha256((p/w['output']).read_bytes()).hexdigest()==w['output_sha256'];z=np.load(p/w['output']);accepted=z['accepted'];wc=z['counts'];remaining=[];raw_remaining=[];revoked=0;raw_excluded=0
   for i,state in enumerate(meta):
    if state[3]==1:assert accepted[i]==-1;continue
    if state[3]==2:
     b=boxes[i];expected=ref.count(b,eps,mask)+newref.count(b,0,~mask);np.testing.assert_array_equal(expected,wc[i]);warm_counts+=1;raw=newref.count(b,0);assert np.all(expected[:,0]>=raw[:,0]) and np.all(expected[:,1]<=raw[:,1]) and np.all(expected[:,2]<=raw[:,2]) and np.all(expected[:,3]>=raw[:,3]),(bp,eps,w['sigma'],i,expected,raw);dominance_checks+=1;raw_rejected=any(lower(c)>q for c in raw);raw_excluded+=raw_rejected;rejected=any(lower(c)>q for c in expected);assert accepted[i]==int(rejected);revoked+=not rejected
    else:assert accepted[i]==0 and not np.any(wc[i]);raw_rejected=False
    if accepted[i]==0:remaining.append(int(state[4]))
    if not raw_rejected:raw_remaining.append(int(state[4]))
   assert w['lower_us']==min([outlo]+remaining) and w['upper_us']==outup and w['revoked']==revoked;messages+=1;pointchecks+=newref.examined;fullscans+=newref.full_scans;raw_lower=min([outlo]+raw_remaining);assert raw_lower>=w['lower_us'];tightness.append(dict(blueprint=bp,query_index=row['query_index'],radius_um=row['radius_um'],sigma=w['sigma'],tube_lower_us=w['lower_us'],same_partition_raw_lower_us=raw_lower,representation_loss_us=raw_lower-w['lower_us'],raw_excluded=raw_excluded,tube_excluded=w['excluded']))
  pointchecks+=ref.examined;fullscans+=ref.full_scans;fingerprints.append(dict(blueprint=bp,query_index=row['query_index'],radius_um=row['radius_um'],nodes=len(cells),lower_us=row['lower_us']));print('checked',bp,row['query_index'],row['radius_um'],flush=True)
 out=dict(radius_filter=a.radius,partition_nodes=nodes_checked,cold_count_checks=cold_counts,warm_count_checks=warm_counts,raw_current_dominance_checks=dominance_checks,message_coverage_checks=messages,reference_candidate_point_checks=pointchecks,full_cloud_crosschecks=fullscans,truth_current_observations=truth,same_partition_tightness=tightness,fingerprints=fingerprints,audit_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),reference_cpp_sha256=hashlib.sha256(sourcecpp.read_bytes()).hexdigest(),scope='Independent world-plane counts; inflated SciPy cone prefilter plus deterministic full-cloud checks. Long-double observed-endpoint membership. Synthetic data preserve full-score soundness, not an independently calibrated physical safety claim.');a.out.write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
