#!/usr/bin/env python3
"""Offline same-class witness proposals, independently checked on two evidence sets."""
import argparse,hashlib,json,math,struct,zlib
from pathlib import Path
from fractions import Fraction
import numpy as np
from audit import ROOT,ref,terrain,geo,sha

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();p=ROOT/'results/tube_evidence_20261003/replay';initial=json.loads((a.results/'audit_sheng.json').read_bytes());rows=json.loads((a.results/'search/rows.json').read_bytes());sources={s['case']:s for s in json.loads((ROOT/'results/pose_inversion_20261003/replay/sources.json').read_bytes())};fixed=json.loads((ROOT/'results/proof_repair_20261003/replay/rows.json').read_bytes());cal=json.loads((ROOT/'results/terrain_score_20261003/analysis_sheng.json').read_bytes())['summary'];pools={};seen={};out=[];input_hashes={};checks=0;rays=0
 for r in rows:
  path=a.results/'search'/r['search_output'];assert sha(path)==r['search_sha256'];z=np.load(path);bp=r['blueprint'];pools.setdefault(bp,[]);seen.setdefault(bp,set())
  for i in r['best_trace']:
   pose=z['poses'][i];key=pose.tobytes()
   if key not in seen[bp]:seen[bp].add(key);pools[bp].append(dict(source_task=r['task_id'],source_evaluation=i,pose=pose.tolist()))
 for row in rows:
  bp=row['blueprint'];base=next(r for r in fixed if r['budget']==4096 and r['message']==row['message']);old,h,_,nominal,m=ref.unpack_full(p/row['reference']);wire=(p/row['message']).read_bytes();body=zlib.decompress(wire[8:]);assert hashlib.sha256(body[:-32]).digest()==body[-32:];_,eps,k,rhash=ref.PREFIX.unpack(body[:ref.PREFIX.size]);assert eps==row['radius_um'] and rhash==hashlib.sha256(old).digest();entries=np.frombuffer(body,dtype=ref.ENTRY,count=k,offset=ref.PREFIX.size+ref.HEADER.size);ids=entries['index'].astype(np.int64);nominal[ids]=entries['xyz'].astype(float)@m[:3,:3].T+m[:3,3]
  current,nh,_,actual,nm=ref.unpack_full(p/base['current_packet']);assert body[ref.PREFIX.size:ref.PREFIX.size+ref.HEADER.size]==current[:ref.HEADER.size];np.testing.assert_array_equal(nm,m);assert len(nominal)==len(actual);input_hashes[str((p/base['current_packet']).relative_to(ROOT))]=sha(p/base['current_packet']);mask=np.ones(len(nominal),bool);mask[ids]=False;np.testing.assert_array_equal(nominal[ids],actual[ids])
  if eps==0:np.testing.assert_array_equal(nominal,actual)
  else:assert np.all(np.linalg.norm((actual[mask]-nominal[mask]).astype(np.longdouble),axis=1)<=np.longdouble(eps)/1000000)
  source=sources[row['old_case']];ext=np.array(source['extent']);q=Fraction(**cal[bp]['threshold']);query=np.array([-6 if row['query_index']==0 else 6,0]);radius=math.ceil(float(np.linalg.norm(ext))*1e6);records=[];best_nominal=None;best_actual=None
  for i,item in enumerate(pools[bp]):
   pose=np.array(item['pose']);center=np.array(source['anchor'])+np.array(source['road_rotation'])@pose[:3];rotation=terrain.rot(pose[3:]);record=dict(pool_index=i)
   for name,points in [('nominal',nominal),('actual',actual)]:
    scores=[terrain.reference(points[::step],m[:3,3],center,rotation,ext) for step in (4,1)];record[name+'_scores']=[dict(n=s[0],k=s[1],numerator=s[2],denominator=s[3]) for s in scores];record[name+'_accepted']=all(Fraction(s[2],s[3])<=q for s in scores);checks+=1;rays+=len(points)+len(points[::4])
   du=math.ceil(float(np.linalg.norm((pose[:2]-query)*1e6))+1e-7);upper=geo.contact(du,0,radius)[1];record['upper_us']=upper;record['distance_upper_um']=du
   if record['nominal_accepted']:
    assert upper>=row['lower_us']
    if best_nominal is None or du<best_nominal['distance_upper_um']:best_nominal=record
   if record['actual_accepted']:
    assert upper>=row['lower_us']
    if best_actual is None or du<best_actual['distance_upper_um']:best_actual=record
   records.append(record)
  original=next(r for r in initial['rows'] if (r['blueprint'],r['query_index'],r['radius_um'])==(bp,row['query_index'],row['radius_um']));assert best_nominal is not None and best_nominal['upper_us']<=original['witness_upper_us'];nu=min(row['upper_us'],best_nominal['upper_us']);au=min(row['upper_us'],best_actual['upper_us']) if best_actual else row['upper_us']
  if eps==0:assert nu==au and all(r['nominal_scores']==r['actual_scores'] for r in records)
  out.append(dict(task_id=row['task_id'],blueprint=bp,query_index=row['query_index'],radius_um=eps,sigma=row['sigma'],lower_us=row['lower_us'],old_upper_us=row['upper_us'],initial_search_upper_us=original['witness_upper_us'],nominal_pool_upper_us=nu,actual_pool_upper_us=au,nominal_gap_us=nu-row['lower_us'],actual_gap_us=au-row['lower_us'],best_nominal_pool_index=best_nominal['pool_index'],best_actual_pool_index=best_actual['pool_index'] if best_actual else None,best_nominal_passes_actual=best_nominal['actual_accepted'],nominal_cannot_cover_fixed_reserve=nu<=240000,actual_cannot_cover_fixed_reserve=au<=240000,records=records));print('transfer',row['task_id'],row['lower_us'],nu,au,best_nominal['actual_accepted'],flush=True)
 result=dict(rows=out,pools=pools,full_ray_pose_checks=checks,full_ray_checks=rays,source_sha256=sha(Path(__file__)),protocol_sha256=sha(Path(__file__).parent/'TRANSFER_PROTOCOL.md'),input_hashes=input_hashes,initial_audit_sha256=sha(a.results/'audit_sheng.json'),scope='Post-search finite same-class candidate reuse. Every pooled pose independently rescored on nominal receiver realization and separately on actual hidden raw data. Raw data only enters this auditor, never proposal generation. Upper witnesses are model feasibility counterexamples, not physical collisions. No new lower proof, calibration, online benefit, or exact compression-loss estimate.')
 a.out.write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
