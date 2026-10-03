#!/usr/bin/env python3
"""Independent full-ray verification of receiver-only feasible upper witnesses."""
import argparse,hashlib,importlib.util,json,math,struct,zlib
from fractions import Fraction
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
ref=load('independent_receiver_packet',ROOT/'experiments/tube_evidence_20261003/audit.py')
geo,terrain=ref.geo,ref.terrain
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();manifest=json.loads((a.results/'manifest.json').read_bytes())
 for section in ('source_hashes','input_hashes'):
  for name,h in manifest[section].items():assert sha(ROOT/name)==h,name
 prior=ROOT/'results/proof_repair_20261003/artifact_manifest.json';assert sha(prior)==manifest['prior_artifact_manifest_sha256']
 for name,record in json.loads(prior.read_bytes())['files'].items():assert sha(ROOT/name)==record['sha256'],name
 sources={s['case']:s for s in json.loads((ROOT/'results/pose_inversion_20261003/replay/sources.json').read_bytes())};calpath=ROOT/'results/terrain_score_20261003/analysis_sheng.json';cal=json.loads(calpath.read_bytes())['summary'];bps=sorted({s['blueprint'] for s in sources.values()});fixed=json.loads((ROOT/'results/proof_repair_20261003/replay/rows.json').read_bytes());p=ROOT/'results/tube_evidence_20261003/replay';rows=json.loads((a.results/'rows.json').read_bytes());assert len(rows)==36;out=[];poses_checked=0;rays_checked=0;witness_checks=0;all_evaluations=0;unique_tasks=set()
 for row in rows:
  key=(row['blueprint'],row['query_index'],row['radius_um']);assert key not in unique_tasks;unique_tasks.add(key)
  base=next(r for r in fixed if r['budget']==4096 and (r['blueprint'],r['query_index'],r['radius_um'])==key);assert row['lower_us']==base['lower_us'] and row['upper_us']==base['upper_us'] and row['message']==base['message'];source=sources[row['old_case']]
  old,h,xyz,world,m=ref.unpack_full(p/row['reference']);wire=(p/row['message']).read_bytes();magic,size=struct.unpack('<4sI',wire[:8]);body=zlib.decompress(wire[8:]);assert magic==b'TBZ1' and len(body)==size and hashlib.sha256(body[:-32]).digest()==body[-32:];magic,eps,k,rhash=ref.PREFIX.unpack(body[:ref.PREFIX.size]);assert magic==b'TUB1' and eps==row['radius_um'] and rhash==hashlib.sha256(old).digest();nh=ref.HEADER.unpack(body[ref.PREFIX.size:ref.PREFIX.size+ref.HEADER.size]);assert nh[:3]==h[:3] and nh[4:7]==h[4:7] and nh[8:]==h[8:] and nh[3]>h[3] and nh[7]>h[7];assert h[24].hex()==sha(calpath) and h[2]==bps.index(row['blueprint']);assert len(body)==ref.PREFIX.size+ref.HEADER.size+16*k+32
  entries=np.frombuffer(body,dtype=ref.ENTRY,count=k,offset=ref.PREFIX.size+ref.HEADER.size);ids=entries['index'].astype(np.int64);assert not k or (ids[-1]<len(world) and np.all(ids[1:]>ids[:-1]));assert np.isfinite(entries['xyz']).all();nominal_xyz=xyz.copy();nominal_xyz[ids]=entries['xyz'];nominal=nominal_xyz.astype(float)@m[:3,:3].T+m[:3,3];mask=np.ones(len(world),bool);mask[ids]=False;np.testing.assert_array_equal(nominal[mask],world[mask]);np.testing.assert_array_equal(nominal[ids],entries['xyz'].astype(float)@m[:3,:3].T+m[:3,3])
  assert sha(a.results/row['search_output'])==row['search_sha256'];z=np.load(a.results/row['search_output']);poses=z['poses'];counts=z['counts'];trace=z['trace'];ext=np.array(source['extent']);lo=np.array([-12,-8,ext[2]-.1,-math.pi/90,0,-math.pi/90]);hi=np.array([12,8,ext[2]+.1,math.pi/90,2*math.pi,math.pi/90]);assert poses.shape==(row['evaluations'],6) and counts.shape==(len(poses),2,2);assert np.isfinite(poses).all() and np.all(poses>=lo) and np.all(poses<=hi);np.testing.assert_allclose(poses[:256],z['initial'],rtol=0,atol=1e-14);assert 256<=len(poses)<=8192 and len(poses)%256==0;all_evaluations+=len(poses);assert np.all(counts>=0) and np.all(counts[:,:,1]<=counts[:,:,0]);q=Fraction(**cal[row['blueprint']]['threshold']);accepted=np.all((counts[:,:,0]<8)|(counts[:,:,1]*q.denominator<=q.numerator*counts[:,:,0]),axis=1);assert accepted.sum()==row['accepted_evaluations'];query=np.array([-6 if row['query_index']==0 else 6,0]);distance=np.linalg.norm(poses[:,:2]-query,axis=1);reconstructed=[];best=math.inf
  for i in np.flatnonzero(accepted):
   if distance[i]<best:best=distance[i];reconstructed.append(int(i))
  np.testing.assert_array_equal(trace,reconstructed);assert reconstructed==row['best_trace'];checks=sorted(set(reconstructed)|set(np.linspace(0,len(poses)-1,32,dtype=int).tolist()));witnesses=[];radius=math.ceil(float(np.linalg.norm(ext))*1e6)
  for i in checks:
   pose=poses[i];center=np.asarray(source['anchor'])+np.asarray(source['road_rotation'])@pose[:3];rotation=terrain.rot(pose[3:]);score=[terrain.reference(nominal[::step],m[:3,3],center,rotation,ext) for step in (4,1)];np.testing.assert_array_equal(counts[i],np.array([s[:2] for s in score]));poses_checked+=1;rays_checked+=len(nominal)+len(nominal[::4])
   if i in reconstructed:
    assert all(Fraction(s[2],s[3])<=q for s in score);du=math.ceil(float(np.linalg.norm((pose[:2]-query)*1e6))+1e-7);upper=geo.contact(du,0,radius)[1];assert upper>=row['lower_us'];witness_checks+=1;witnesses.append(dict(evaluation=i,pose=pose.tolist(),scores=[dict(n=s[0],k=s[1],numerator=s[2],denominator=s[3]) for s in score],distance_upper_um=du,upper_us=upper))
  if reconstructed:np.testing.assert_array_equal(poses[reconstructed[-1]],row['best_pose']);assert best==row['best_distance']
  else:assert row['best_pose'] is None and row['best_distance'] is None
  upper=min([row['upper_us']]+[w['upper_us'] for w in witnesses]);out.append(dict(blueprint=row['blueprint'],query_index=row['query_index'],radius_um=row['radius_um'],sigma=row['sigma'],evaluations=len(poses),accepted_evaluations=int(accepted.sum()),lower_us=row['lower_us'],old_upper_us=row['upper_us'],witness_upper_us=upper,gap_us=upper-row['lower_us'],upper_improvement_us=row['upper_us']-upper,witnesses=witnesses));print('checked',row['task_id'],len(witnesses),row['lower_us'],upper,flush=True)
 result=dict(rows=out,total_evaluations=all_evaluations,full_ray_pose_checks=poses_checked,full_ray_checks=rays_checked,best_witness_checks=witness_checks,tasks_with_accepted_pose=sum(bool(r['witnesses']) for r in out),tasks_with_tighter_upper=sum(r['upper_improvement_us']>0 for r in out),max_upper_improvement_us=max(r['upper_improvement_us'] for r in out),min_gap_us=min(r['gap_us'] for r in out),max_gap_us=max(r['gap_us'] for r in out),tasks_with_gap_at_most_10000us=sum(r['gap_us']<=10000 for r in out),auditor_sha256=sha(Path(__file__)),prior_artifact_manifest_sha256=manifest['prior_artifact_manifest_sha256'],scope='All successive best accepted poses independently rescored on all nominal-message rays at both nested budgets, plus32 spread evaluations per task. Unselected optimizer evaluations are not all independently rescored; they do not justify any exclusion. Receiver-only legal nominal realization, not actual hidden current data or physical mesh. Existing4096-visit lower bounds compose with immutable prior audits. Offline search is not an online benefit or independent risk validation.')
 a.out.write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
