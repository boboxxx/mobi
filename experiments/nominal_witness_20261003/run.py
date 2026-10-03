#!/usr/bin/env python3
import argparse,ctypes as C,hashlib,json,math,subprocess,sys,time,zlib
from pathlib import Path
import numpy as np
from scipy.optimize import differential_evolution
from scipy.stats import qmc
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'experiments/tube_evidence_20261003'))
from codec import decode,decode_full

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

class Scorer:
 def __init__(self,lib,points,source,origin):
  f64=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');i32=np.ctypeslib.ndpointer(dtype=np.int32,flags='C_CONTIGUOUS');i64=np.ctypeslib.ndpointer(dtype=np.int64,flags='C_CONTIGUOUS')
  lib.scorer_create.argtypes=[f64,i32,C.c_int,f64,f64,f64,f64];lib.scorer_create.restype=C.c_void_p;lib.scorer_evaluate.argtypes=[C.c_void_p,f64,C.c_int,i64];lib.scorer_destroy.argtypes=[C.c_void_p]
  self.lib=lib;strides=np.where(np.arange(len(points))%4==0,16,4).astype(np.int32)
  self.ptr=lib.scorer_create(np.ascontiguousarray(points),strides,len(points),np.ascontiguousarray(source['extent'],dtype=float),np.ascontiguousarray(source['anchor'],dtype=float),np.ascontiguousarray(source['road_rotation'],dtype=float),np.ascontiguousarray(origin))
  if not self.ptr:raise ValueError('scorer construction failed')
 def __call__(self,poses):
  poses=np.ascontiguousarray(poses,dtype=float);out=np.empty((len(poses),2,2),np.int64);self.lib.scorer_evaluate(self.ptr,poses,len(poses),out);return out
 def close(self):self.lib.scorer_destroy(self.ptr)

def initial(points,source,lo,hi,seed):
 sobol=qmc.Sobol(6,scramble=True,seed=seed).random_base2(8);population=lo+(hi-lo)*sobol
 p=(points-np.asarray(source['anchor']))@np.asarray(source['road_rotation'])
 mask=(p[:,0]>=lo[0])&(p[:,0]<=hi[0])&(p[:,1]>=lo[1])&(p[:,1]<=hi[1])&(points[:,2]>.3)&(points[:,2]<2*source['extent'][2]+.3)
 p=p[mask];bins={}
 for xy in p[:,:2]:bins.setdefault(tuple(np.floor(xy/.5).astype(int)),[]).append(xy)
 order=sorted(bins,key=lambda k:(-len(bins[k]),k))[:16]
 for j,key in enumerate(order):
  xy=np.mean(bins[key],axis=0)
  for k in range(8):population[128+8*j+k]=[xy[0],xy[1],source['extent'][2],0,k*math.pi/4,0]
 return population,len(order)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);(a.out/'search').mkdir()
 so='/tmp/mobi_nominal_scorer.so';cmd=['c++','-O3','-std=c++17','-ffp-contract=off','-shared','-fPIC',str(HERE/'scorer.cpp'),'-o',so];subprocess.run(cmd,check=True);lib=C.CDLL(so)
 prior=ROOT/'results/tube_evidence_20261003/replay';repair=ROOT/'results/proof_repair_20261003';tasks=[r for r in json.loads((repair/'replay/rows.json').read_bytes()) if r['budget']==4096];assert len(tasks)==36
 sources={s['case']:s for s in json.loads((ROOT/'results/pose_inversion_20261003/replay/sources.json').read_bytes())};bps=sorted({s['blueprint'] for s in sources.values()});calpath=ROOT/'results/terrain_score_20261003/analysis_sheng.json';digest=sha(calpath);cal=json.loads(calpath.read_bytes())['summary'];cold=json.loads((prior/'cold.json').read_bytes());rows=[];inputs={};meta_path=ROOT/'results/pose_inversion_20261003/replay/sources.json'
 for task_id,row in enumerate(tasks):
  start=time.perf_counter();source=sources[row['old_case']];ref=next(c['reference'] for c in cold if c['proof']==row['proof']);reference=zlib.decompress((prior/ref).read_bytes());wire=(prior/row['message']).read_bytes();d=decode(wire,reference,digest,bps);old=d['old'];points=old['views'][-1]['points'].copy();points[d['indices']]=d['exact_world'];scorer=Scorer(lib,points,source,old['origin']);lo=np.array([-12,-8,source['extent'][2]-.1,-math.pi/90,0,-math.pi/90]);hi=np.array([12,8,source['extent'][2]+.1,math.pi/90,2*math.pi,math.pi/90]);seed=31003+task_id;init,nbins=initial(points,source,lo,hi,seed);threshold=cal[row['blueprint']]['threshold'];qn,qd=threshold['numerator'],threshold['denominator'];query=np.array([-6 if row['query_index']==0 else 6,0]);pose_history=[];count_history=[];trace=[];best_distance=float('inf');evaluations=0
  def objective(x):
   nonlocal best_distance,evaluations
   poses=np.ascontiguousarray(x.T);counts=scorer(poses);n=counts[:,:,0];k=counts[:,:,1];accepted=np.all((n<8)|(k*qd<=qn*n),axis=1);scores=np.where(n>=8,k/np.maximum(n,1),0.);distance=np.linalg.norm(poses[:,:2]-query,axis=1)
   for i in np.flatnonzero(accepted):
    if distance[i]<best_distance:best_distance=float(distance[i]);trace.append(evaluations+int(i))
   pose_history.append(poses);count_history.append(counts);evaluations+=len(poses)
   return np.where(accepted,distance/30,2+np.maximum(0,scores.max(axis=1)-qn/qd)+.01*distance/30)
  opt=differential_evolution(objective,list(zip(lo,hi)),init=init,maxiter=31,mutation=(.5,1.),recombination=.7,polish=False,tol=0,atol=0,seed=seed,updating='deferred',vectorized=True,workers=1)
  elapsed=time.perf_counter()-start;scorer.close();poses=np.concatenate(pose_history);counts=np.concatenate(count_history);name='search/task_%02d.npz'%task_id;np.savez_compressed(a.out/name,poses=poses,counts=counts,trace=np.array(trace,np.int64),initial=init);accepted=np.all((counts[:,:,0]<8)|(counts[:,:,1]*qd<=qn*counts[:,:,0]),axis=1)
  out={k:row[k] for k in ('blueprint','query_index','radius_um','sigma','old_case','message','lower_us','upper_us')};out.update(task_id=task_id,reference=ref,seed=seed,proposed_bins=nbins,evaluations=evaluations,accepted_evaluations=int(accepted.sum()),best_trace=trace,best_pose=poses[trace[-1]].tolist() if trace else None,best_distance=best_distance if trace else None,search_output=name,search_sha256=sha(a.out/name),elapsed_s=elapsed,optimizer_iterations=int(opt.nit));rows.append(out)
  for p in (prior/ref,prior/row['message'],calpath,meta_path,repair/'replay/rows.json'):inputs[str(p.relative_to(ROOT))]=sha(p)
  print(json.dumps({k:out[k] for k in ('task_id','blueprint','query_index','radius_um','evaluations','accepted_evaluations','best_distance','elapsed_s')}),flush=True)
 (a.out/'rows.json').write_text(json.dumps(rows,indent=2,allow_nan=False)+'\n');deps=[HERE/f for f in ('run.py','scorer.cpp','PROTOCOL.md')]+[ROOT/'experiments/expiry_runtime_20261003/kernel.cpp',ROOT/'experiments/tube_evidence_20261003/codec.py',ROOT/'experiments/pose_inversion_20261003/packet.py'];(a.out/'manifest.json').write_text(json.dumps(dict(source_hashes={str(p.relative_to(ROOT)):sha(p) for p in deps},input_hashes=inputs,prior_artifact_manifest_sha256=sha(repair/'artifact_manifest.json'),command=cmd),indent=2)+'\n')

if __name__=='__main__':main()
