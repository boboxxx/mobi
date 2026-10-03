#!/usr/bin/env python3
"""Independent delta audit over an immutable, previously audited base partition."""
import argparse,ctypes as C,hashlib,importlib.util,json,math,struct,subprocess,sys,zlib
from functools import lru_cache
from fractions import Fraction
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('bounded_reference',ROOT/'experiments/tube_evidence_20261003/audit.py');refmod=importlib.util.module_from_spec(spec);spec.loader.exec_module(refmod)
geo,terrain=refmod.geo,refmod.terrain
@lru_cache(None)
def contact(x,y,r):return geo.contact(x,y,r)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();p=ROOT/'results/tube_evidence_20261003/replay';prior=json.loads((p.parent/'artifact_manifest.json').read_bytes());manifest=json.loads((a.results/'manifest.json').read_bytes());assert sha(p.parent/'artifact_manifest.json')==manifest['prior_artifact_manifest_sha256']
 for name,item in prior['files'].items():assert sha(ROOT/name)==item['sha256'],name
 for name,h in manifest['source_hashes'].items():assert sha(ROOT/name)==h,name
 cpp=ROOT/'experiments/expiry_runtime_20261003/reference.cpp';so='/tmp/mobi_repair_reference.so';subprocess.run(['c++','-O3','-std=c++17','-ffp-contract=off','-shared','-fPIC',str(cpp),'-o',so],check=True);lib=C.CDLL(so);f64=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');i64=np.ctypeslib.ndpointer(dtype=np.int64,flags='C_CONTIGUOUS');lib.reference_counts.argtypes=[f64,i64,C.c_int,f64,f64,f64,f64,i64]
 rows=json.loads((a.results/'rows.json').read_bytes());assert len(rows)==108;sources={s['case']:s for s in json.loads((ROOT/'results/pose_inversion_20261003/replay/sources.json').read_bytes())};cal=json.loads((ROOT/'results/terrain_score_20261003/analysis_sheng.json').read_bytes());cold=json.loads((p/'cold.json').read_bytes());tasks={};out=[];newcounts=0;reused=0;nodeschecked=0;newages=0;newexclusions=0;witnesses=0;pointchecks=0;fullscans=0
 for row in rows:
  task=row['message']
  if task not in tasks:
   source=sources[row['old_case']];basez=np.load(p/row['proof']);base={k:basez[k] for k in basez.files};wz=np.load(p/row['output']);wa=wz['accepted'];wc=wz['counts'];c=next(c for c in cold if c['proof']==row['proof']);old,oh,_,ow,om=refmod.unpack_full(p/c['reference']);current,ch,xyz,nw,nm=refmod.unpack_full(p/row['current_packet']);wire=(p/row['message']).read_bytes();body=zlib.decompress(wire[8:]);assert hashlib.sha256(body[:-32]).digest()==body[-32:];magic,eps,k,rhash=refmod.PREFIX.unpack(body[:refmod.PREFIX.size]);assert magic==b'TUB1' and rhash==hashlib.sha256(old).digest() and eps==row['radius_um'];entries=np.frombuffer(body,dtype=refmod.ENTRY,count=k,offset=refmod.PREFIX.size+refmod.HEADER.size);ids=entries['index'].astype(np.int64);np.testing.assert_array_equal(entries['xyz'],xyz[ids]);mask=np.ones(len(ow),bool);mask[ids]=False;nominal=ow.copy();nominal[ids]=nw[ids];tasks[task]=dict(source=source,base=base,wa=wa,wc=wc,old=refmod.Ref(ow,om[:3,3],lib),new=refmod.Ref(nw,nm[:3,3],lib),mask=mask,nominal=nominal,origin=om[:3,3],checks={},last_lower=-1,last_upper=500001,last_cells=None)
  t=tasks[task];source=t['source'];base=t['base'];nbase=len(base['cells']);q=Fraction(**cal['summary'][row['blueprint']]['threshold']);ext=np.array(source['extent']);road=np.array(source['road_rotation']);anchor=np.array(source['anchor']);query=np.array([-6 if row['query_index']==0 else 6,0]);rad=math.ceil(np.linalg.norm(ext)*1e6);assert sha(a.results/row['repair_output'])==row['repair_sha256'];z=np.load(a.results/row['repair_output']);cells=z['cells'];meta=z['meta'];counts=z['counts'];flags=z['flags'];witness=z['witness'];n=len(cells);nodeschecked+=n;assert n==row['nodes'];np.testing.assert_array_equal(cells[:nbase],base['cells']);np.testing.assert_array_equal(meta[:nbase,0],base['meta'][:,0]);np.testing.assert_array_equal(meta[:nbase,4],base['meta'][:,4]);assert np.isfinite(cells).all() and np.all(cells[:,:6]<=cells[:,6:]);assert np.all(np.isin(meta[:,3],[0,1,2,4])) and np.all(np.isin(flags,[0,1,2]))
  split=np.flatnonzero(meta[:,3]==1);left=meta[split,1];right=meta[split,2];assert np.all(left>split) and np.all(right>left) and np.all(right<n);np.testing.assert_array_equal(np.sort(np.r_[left,right]),np.arange(1,n));np.testing.assert_array_equal(meta[left,0],split);np.testing.assert_array_equal(meta[right,0],split);np.testing.assert_array_equal(cells[left,:6],cells[split,:6]);np.testing.assert_array_equal(cells[right,6:],cells[split,6:]);change=cells[left,6:]!=cells[split,6:];assert np.all(change.sum(axis=1)==1);axis=change.argmax(axis=1);np.testing.assert_array_equal(cells[left,6+axis],cells[right,axis])
  # At unsplit coordinates left.hi equals parent.hi while right.lo equals parent.lo.
  for j in range(6):
   same=axis!=j;np.testing.assert_array_equal(cells[right[same],j],cells[split[same],j]);diff=axis==j;mid=cells[left[diff],6+j];assert np.all(mid>cells[split[diff],j]) and np.all(mid<cells[split[diff],6+j])
  for i in range(nbase,n):
   d=np.maximum(np.maximum(cells[i,:2]-query,query-cells[i,6:8]),0);du=np.maximum(np.floor(d*1e6-1e-7),0).astype(np.int64);assert meta[i,4]==contact(int(du[0]),int(du[1]),rad)[0];newages+=1
  oldsplit=base['meta'][:,3]==1;np.testing.assert_array_equal(meta[:nbase][oldsplit,:4],base['meta'][oldsplit,:4]);waschecked=base['meta'][:,3]==2;np.testing.assert_array_equal(flags[:nbase][waschecked],np.ones(waschecked.sum(),np.int64));np.testing.assert_array_equal(counts[:nbase][waschecked],t['wc'][waschecked]);reused+=int(waschecked.sum());still=t['wa']==1;assert np.all(meta[:nbase,3][still]==2);assert not np.any(counts[flags==0]);assert not np.any((meta[:,3]==2)&(flags==0))
  for i in np.flatnonzero(flags==2):
   key=cells[i].tobytes()
   if key not in t['checks']:
    b=geo.boxes(dict(lo=cells[i,:6].tolist(),hi=cells[i,6:].tolist()),ext,anchor,road,True);expected=t['old'].count(b,row['radius_um']/1e6,t['mask'])+t['new'].count(b,0,~t['mask']);t['checks'][key]=expected;newcounts+=1
    if newcounts%997==0:np.testing.assert_array_equal(expected,t['old'].count(b,row['radius_um']/1e6,t['mask'],full=True)+t['new'].count(b,0,~t['mask'],full=True))
   np.testing.assert_array_equal(counts[i],t['checks'][key])
  rejected=meta[:,3]==2
  for i in np.flatnonzero(rejected):assert any(refmod.lower(c)>q for c in counts[i])
  added_exclusions=int(np.sum(rejected&~np.r_[still,np.zeros(n-nbase,bool)]));newexclusions+=added_exclusions;assert int(np.sum(meta[:,3]==1)-oldsplit.sum()+added_exclusions+np.sum(meta[:,3]==4))==row['visits']<=row['budget'];assert int(np.sum(flags==2))==row['new_bound_calls'];distance=min(query[0]+12,12-query[0],query[1]+8,8-query[1]);outside=contact(max(0,math.floor(distance*1e6-1e-7)),0,rad)[0];outside_upper=contact(math.ceil(distance*1e6+1e-7),0,rad)[1];kept=(meta[:,3]!=1)&~rejected;lower=min([outside]+meta[kept,4].tolist());upper=outside_upper
  if row['has_witness']:
   assert np.isfinite(witness).all() and np.all(witness>=cells[0,:6]) and np.all(witness<=cells[0,6:]);center=anchor+road@witness[:3];rotation=geo.rotation(witness[3:]);scores=[terrain.reference(t['nominal'][::step],t['origin'],center,rotation,ext) for step in (4,1)];assert all(Fraction(s[2],s[3])<=q for s in scores);d=math.ceil(float(np.linalg.norm((witness[:2]-query)*1e6))+1e-7);upper=min(upper,contact(d,0,rad)[1]);witnesses+=1
  else:assert np.isnan(witness).all()
  assert lower==row['lower_us'] and upper==row['upper_us'] and lower<=upper;assert lower>=row['baseline_lower_us'] and lower>=t['last_lower'] and upper<=t['last_upper'];t['last_lower']=lower;t['last_upper']=upper
  if t['last_cells'] is not None:np.testing.assert_array_equal(cells[:len(t['last_cells'])],t['last_cells'])
  t['last_cells']=cells;out.append({k:row[k] for k in ('blueprint','query_index','radius_um','sigma','budget','lower_us','upper_us','new_bound_calls','has_witness')});print('checked',row['blueprint'],row['query_index'],row['radius_um'],row['budget'],flush=True)
 for t in tasks.values():pointchecks+=t['old'].examined+t['new'].examined;fullscans+=t['old'].full_scans+t['new'].full_scans
 result=dict(rows=out,partition_nodes=nodeschecked,prior_count_reuses=reused,unique_new_count_checks=newcounts,new_age_checks=newages,new_exclusion_records=newexclusions,upper_witnesses=witnesses,candidate_point_checks=pointchecks,full_cloud_crosschecks=fullscans,prior_artifact_manifest_sha256=manifest['prior_artifact_manifest_sha256'],audit_sha256=sha(Path(__file__)),scope='Delta audit composes with immutable byte-verified prior proofs and current counts. Every new cell bound is independently recounted; full partition structure and new integer contact times checked. Candidate cone filtering plus full-cloud samples, not unconditional all-ray scan of every cell. Nominal message-compatible witnesses directly rescored by independent Python halfspaces.');a.out.write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
