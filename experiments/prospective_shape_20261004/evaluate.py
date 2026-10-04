#!/usr/bin/env python3
"""Fresh fixed-score joint coverage and complete paid same-information policies."""
import argparse,hashlib,json,math,sys,time,zlib
from collections import defaultdict
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent
EP=ROOT/'experiments/pose_support_20261004';EB=ROOT/'experiments/body_expiry_20261004'
sys.path.insert(0,str(EP));sys.path.insert(0,str(EB))
from observer import parameters,projections,score,geometry,DIRECTIONS,enclosing_radius_um
from kernel import hull,geometry as sphere_geometry,ceilroot
from frontend import groups
from codec import pack,pack_raw
from wire import POLICIES,infer,unpack
from raw_optimized import decode as decode_raw
from engine import replay
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def canon(d):return json.dumps(d,sort_keys=True,separators=(',',':')).encode()
def write(p,d):p.write_text(json.dumps(d,separators=(',',':'))+'\n')
def truth_integer(xy):
 v=[float(x).as_integer_ratio() for x in xy];D=max(t[1] for t in v);return [t[0]*(D//t[1])*1000000 for t in v],D
def body_score(gg,base,num,D):
 values=[]
 for g in gg:
  rad=max((ceilroot(sum((int(pt[j])*10000*D-num[j])**2 for j in (0,1)))+D-1)//D for pt in g);values.append(max(0,rad-base))
 return min(values) if values else 0
def load(r,p):
 path=p/'capture'/r['cloud_file'];assert sha(path)==r['cloud_sha256']
 with np.load(path) as z:raw=z['raw'];xyz=np.c_[raw['x'],raw['y'],raw['z']].astype('<f4');T=z['transform'].copy()
 return raw,xyz,T,path
def record(r,p,catalog,basis,bg,inputs,matrices):
 raw,xyz,T,path=load(r,p);inputs[str(path.relative_to(ROOT))]=sha(path);ext=catalog[r['blueprint']];assert r['bounding_box']['extent']==ext and r['bounding_box']['rotation']==[0.0,0.0,0.0];anchor=np.r_[r['query'],0.];yaw=math.radians(r['road_yaw']);road=np.array([[math.cos(yaw),-math.sin(yaw),0],[math.sin(yaw),math.cos(yaw),0],[0,0,1.]])
 assert anchor.tolist()==basis['anchor'] and road.tolist()==basis['road'];key=str(r['layout']);assert key not in matrices or matrices[key]==T.tolist();matrices[key]=T.tolist();true=(np.asarray(r['center'])-anchor)@road;num,D=truth_integer(true[:2]);gg=groups(xyz,T,anchor,road,ext,bg['layouts'][key]['codes']);hh=[hull(g) for g in gg];ps=score(projections(hh),ext,num,D);bs=body_score(gg,enclosing_radius_um(ext)+8000,num,D)
 return dict(**r,true_xy=true[:2].tolist(),source_us=math.floor(r['timestamp']*1e6),acquisition_us=math.ceil(r['acquisition_s']*1e6),hulls_cm=hh,groups_cm=gg,pose_score_um=ps,body_score_um=bs,joint_score_um=max(ps,bs),available=bool(gg))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();p=a.results.resolve();assert not (p/'analysis_sheng.json').exists() and not (p/'calibration_frozen.json').exists();f=read(E/'freeze.json')
 for section in ('sources','inputs'):
  for n,h in f[section].items():assert sha(ROOT/n)==h,n
 catalog=read(E/'catalog.json');records=read(p/'capture/record.json');episodes=read(p/'capture/episodes.json');plan=read(E/'plan.json');assert [e['episode'] for e in episodes]==plan and len(plan)==930;bg=read(ROOT/'results/background_frontend_20261004/background.json');basis=read(ROOT/'results/prospective_expiry_20261003/analysis_sheng.json')['contract_body']['basis'];inputs={};matrices={};rows=[];scores=defaultdict(int)
 for j,r in enumerate(v for v in records if v['split']=='calibration'):
  rr=record(r,p,catalog,basis,bg,inputs,matrices);rows.append(rr);scores[r['episode_id']]=max(scores[r['episode_id']],rr['joint_score_um'])
  if (j+1)%500==0:print('calibration scored',j+1,flush=True)
 registry={}
 for bp in catalog:
  ss=[scores[e['id']] for e in plan if e['blueprint']==bp and e['split']=='calibration'];assert len(ss)==95;registry[bp]=dict(joint_slack_um=int(max(ss)),calibration_n=95,rank=95,episode_failure_target=.05,calibration_failure_bound=.95**95)
 calibration=hashlib.sha256(canon(registry)).hexdigest();receipt=dict(registry=registry,calibration_sha256=calibration,calibration_episode_scores={e['id']:scores[e['id']] for e in plan if e['split']=='calibration'},input_hashes=dict(inputs),source_hashes=f['sources'],scope='Fixed direct whole-episode membership scores; receipt written before any test cloud processing. No uprightness premise in statistical coverage.');write(p/'calibration_frozen.json',receipt);receipt_sha=sha(p/'calibration_frozen.json');print('REGISTRY_FROZEN_BEFORE_TEST',calibration,flush=True)
 for j,r in enumerate(v for v in records if v['split']=='test'):
  rr=record(r,p,catalog,basis,bg,inputs,matrices);rows.append(rr);scores[r['episode_id']]=max(scores[r['episode_id']],rr['joint_score_um'])
  if (j+1)%500==0:print('test scored',j+1,flush=True)
 # Preserve the capture's exact source order; calibration read order does not change identity.
 lookup={r['id']:r for r in rows};rows=[lookup[r['id']] for r in records];slacks={bp:v['joint_slack_um'] for bp,v in registry.items()};transport=dict(experiment=E.name,catalog=catalog,basis=basis,transforms=matrices,source_hashes=f['sources']);raw_contract=hashlib.sha256(canon(transport)).hexdigest();rc=dict(contract=raw_contract,calibration=calibration,transforms=matrices)
 context=dict(catalog=catalog,basis=basis,background=bg,slacks_um=slacks,raw_transport=rc,directions=DIRECTIONS,tilt_operator_norm_upper=[87267,1000000],yaw_cell_distance_factor=[8730,1000000],point_quantization_allowance_um=8000,source_hashes=f['sources'],motion=dict(speed_um_s=5000000,acceleration_um_s2=3000000),query_radius_um=750000,cap_us=500000,raw_transport_body=transport,calibration_receipt_sha256=receipt_sha,runtime_initialization_scope='Initialized Python/native service; cold means shared-context transfer, not cold process.',shape_prior_scope='Fixed arbitrary set predictor; direct fresh membership score absorbs misspecification. Uprightness is not assumed for statistical center coverage.',scope='Fresh whole-episode joint current-center qualification under frozen known-class law; conditional source expiry and measured FIFO. No unknown inventory, continuous physics, live wireless/ego or established novelty.')
 contract=hashlib.sha256(canon(context)).hexdigest();setup_samples=[]
 for _ in range(3):
  t=time.perf_counter();payload=canon(context);ww=zlib.compress(payload+hashlib.sha256(payload).digest(),6);ss=time.perf_counter()-t;t=time.perf_counter();b=zlib.decompress(ww);assert hashlib.sha256(b[:-32]).digest()==b[-32:] and json.loads(b[:-32])==context;rx=time.perf_counter()-t;setup_samples.append(dict(source_s=ss,receiver_s=rx))
 (p/'setup.bin').write_bytes(ww);setup=dict(samples=setup_samples,wire_bytes=len(ww),wire_sha256=sha(p/'setup.bin'),source_us=math.ceil(max(v['source_s'] for v in setup_samples)*1e6),receiver_us=math.ceil(max(v['receiver_s'] for v in setup_samples)*1e6));(p/'messages').mkdir();test=[r for r in rows if r['split']=='test']
 for j,r in enumerate(test):
  raw,xyz,T,path=load(r,p);bp=r['blueprint'];extent=catalog[bp];ci=list(catalog).index(bp);delta=slacks[bp];param=parameters(extent,delta);r['parameters']=param;r['pose_geometry']=geometry(projections(r['hulls_cm']),param);r['sphere_geometry']=sphere_geometry(r['hulls_cm'],param['body_um']+8000+delta,param['body_um']);common=[]
  for _ in range(3):
   t=time.perf_counter();xx=np.c_[raw['x'],raw['y'],raw['z']].astype('<f4');gg=groups(xx,T,np.array(basis['anchor']),np.array(basis['road']),extent,bg['layouts'][str(r['layout'])]['codes']);hh=[hull(g) for g in gg];assert hh==r['hulls_cm'];ww=pack('hull',hh,ci,r['layout'],r['frame'],r['source_us'],contract,calibration);ss=time.perf_counter()-t;common.append(ss)
  hpacket=p/'messages'/(r['id']+'_hull.bin');hpacket.write_bytes(ww);r['common_hull_samples_s']=common;r['methods']={}
  for policy in POLICIES:
   expected=infer(r['hulls_cm'],extent,delta,policy);samples=[]
   for k in range(3):
    if policy=='joint_raw':t=time.perf_counter();xx=np.c_[raw['x'],raw['y'],raw['z']].astype('<f4');wire=pack_raw(xx,T,ci,r['frame'],r['timestamp'],raw_contract,calibration);ss=time.perf_counter()-t
    else:wire=ww;ss=common[k]
    t=time.perf_counter()
    if policy=='joint_raw':decoded,rh=decode_raw(wire,context);assert rh==r['hulls_cm']
    else:decoded=unpack(wire,policy,context,contract,calibration)
    rx=time.perf_counter()-t;assert all(decoded[k]==v for k,v in expected.items()) and decoded['source_us']==r['source_us'] and decoded['layout']==r['layout'] and decoded['frame']==r['frame'] and decoded['class_index']==ci;samples.append(dict(source_s=ss,receiver_s=rx,selection_s=r['selection_s']))
   packet=p/'messages'/(r['id']+'_raw.bin') if policy=='joint_raw' else hpacket
   if policy=='joint_raw':packet.write_bytes(wire)
   r['methods'][policy]=dict(**expected,samples=samples,source_us=math.ceil((max(v['source_s'] for v in samples)+r['selection_s'])*1e6),receiver_us=math.ceil(max(v['receiver_s'] for v in samples)*1e6),packet=str(packet.relative_to(ROOT)),wire_bytes=len(wire),wire_sha256=sha(packet))
  if (j+1)%200==0:print('paid',j+1,flush=True)
 byep=defaultdict(list)
 for r in test:byep[r['episode_id']].append(r)
 traces=[]
 for e in episodes:
  ep=e['episode']
  if ep['split']!='test':continue
  rr=byep[ep['id']];t0=min(r['source_us'] for r in rr) if rr else 0
  for policy in POLICIES:
   for rate in (20000000,2000000):
    for startup in ('warm','cold'):traces.append(dict(episode_id=ep['id'],blueprint=ep['blueprint'],capture_status=e['status'],method=policy,rate=rate,startup=startup,t0=t0,**replay(rr,policy,rate,t0,setup if startup=='cold' else None)))
 assert sha(p/'calibration_frozen.json')==receipt_sha
 result=dict(rows=rows,episodes=episodes,traces=traces,setup=setup,context=context,contract_sha256=contract,calibration_sha256=calibration,registry=registry,joint_episode_scores={e['id']:scores[e['id']] for e in plan},calibration_receipt_sha256=receipt_sha,source_hashes=f['sources'],input_hashes=inputs,capture_manifest_sha256=sha(p/'capture/manifest.json'),joint_calibration_confidence_lower=1-6*.95**95,scope=context['scope'],source_profile_scope='Actual stride-copy observed during capture, plus complete source XYZ/frontend/hull/encode or XYZ/raw encode. Three full decoder jobs each, raw hull-optimized. Max observed fees, no WCET.');write(p/'analysis_sheng.json',result);print('complete',len(rows),len(traces),flush=True)
if __name__=='__main__':main()
