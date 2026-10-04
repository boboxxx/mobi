#!/usr/bin/env python3
"""Fixed 180-cell yaw model: development calibration and actual paid transport."""
import argparse,hashlib,json,math,sys,time,zlib
from collections import defaultdict
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;EB=ROOT/'experiments/body_expiry_20261004';sys.path.insert(0,str(EB))
from kernel import hull,geometry as sphere_geometry
from frontend import groups
from codec import pack,pack_raw
from engine import replay
from observer import projections,parameters,score,geometry,DIRECTIONS
from wire import unpack,infer,POLICIES
PP=ROOT/'results/prospective_expiry_20261003';PB=ROOT/'results/background_frontend_20261004'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def canon(d):return json.dumps(d,sort_keys=True,separators=(',',':')).encode()
def write(p,d):p.write_text(json.dumps(d,separators=(',',':'))+'\n')
def truth_integer(xy):
 v=[float(x).as_integer_ratio() for x in xy];D=max(t[1] for t in v);return [t[0]*(D//t[1])*1000000 for t in v],D

def load(r):
 path=PP/'capture'/r['cloud_file'];assert sha(path)==r['cloud_sha256']
 with np.load(path) as z:raw=z['raw'];xyz=np.c_[raw['x'],raw['y'],raw['z']].astype('<f4');T=z['transform'].copy()
 return xyz,T,path

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();p=a.results.resolve();assert not (p/'analysis_sheng.json').exists();p.mkdir(parents=True,exist_ok=True);frozen=read(E/'freeze.json')
 for n,h in frozen['sources'].items():assert sha(ROOT/n)==h,n
 prior=read(PP/'analysis_sheng.json');body=read(PB/'body_support_sheng.json');bg=read(PB/'background.json');catalog=prior['contract_body']['catalog'];basis=prior['contract_body']['basis'];reference={r['id']:r for r in body['rows']};inputs={str(v.relative_to(ROOT)):sha(v) for v in [PP/'analysis_sheng.json',PB/'body_support_sheng.json',PB/'background.json']};rows=[];joint_scores=defaultdict(int);matrices={}
 for j,r in enumerate(prior['rows']):
  xyz,T,path=load(r);inputs[str(path.relative_to(ROOT))]=sha(path);bp=r['blueprint'];extent=catalog[bp];gg=groups(xyz,T,np.array(basis['anchor']),np.array(basis['road']),extent,bg['layouts'][str(r['layout'])]['codes']);assert gg==reference[r['id']]['groups_cm'];hh=[hull(g) for g in gg];projected=projections(hh);num,D=truth_integer(r['true_xy']);pose_score=score(projected,extent,num,D);joint_score=max(pose_score,reference[r['id']]['score_um']);joint_scores[r['episode_id']]=max(joint_scores[r['episode_id']],joint_score);key=str(r['layout']);assert key not in matrices or matrices[key]==T.tolist();matrices[key]=T.tolist();rows.append(dict(id=r['id'],episode_id=r['episode_id'],blueprint=bp,split=r['split'],layout=r['layout'],frame=r['frame'],source_us=r['source_us'],acquisition_us=r['acquisition_us'],hulls_cm=hh,pose_score_um=pose_score,body_score_um=reference[r['id']]['score_um'],joint_score_um=joint_score,available=bool(hh)))
  if (j+1)%500==0:print('scored',j+1,flush=True)
 registry={}
 for bp in catalog:
  ss=[joint_scores[e['episode']['id']] for e in prior['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='calibration'];assert len(ss)==95;registry[bp]=dict(development_joint_slack_um=int(max(ss)),calibration_n=95,scope='Reused fixed-data max whole-episode joint score; no new prospective qualification')
 slacks={bp:v['development_joint_slack_um'] for bp,v in registry.items()};rc=dict(contract=prior['contract_sha256'],calibration=prior['calibration_sha256'],transforms=matrices);context=dict(catalog=catalog,basis=basis,background=bg,slacks_um=slacks,raw_transport=rc,directions=DIRECTIONS,tilt_operator_norm_upper=[87267,1000000],yaw_cell_distance_factor=[8730,1000000],point_quantization_allowance_um=8000,source_hashes=frozen['sources'],motion=dict(speed_um_s=5000000,acceleration_um_s2=3000000),query_radius_um=750000,cap_us=500000,runtime_initialization_scope='Native/Python service is already initialized. Cold means shared context transfer, not cold process.',scope='Finite reused-scene shape-prior development, complete yaw cover; no prospective risk or raw-world optimum, unknown inventory, live-link/ego guarantee')
 contract=hashlib.sha256(canon(context)).hexdigest();calibration=hashlib.sha256(canon(registry)).hexdigest();setup_samples=[]
 for _ in range(3):
  t=time.perf_counter();payload=canon(context);wire=zlib.compress(payload+hashlib.sha256(payload).digest(),6);ss=time.perf_counter()-t;t=time.perf_counter();bb=zlib.decompress(wire);assert hashlib.sha256(bb[:-32]).digest()==bb[-32:] and json.loads(bb[:-32])==context;rx=time.perf_counter()-t;setup_samples.append(dict(source_s=ss,receiver_s=rx))
 (p/'setup.bin').write_bytes(wire);setup=dict(samples=setup_samples,wire_bytes=len(wire),wire_sha256=sha(p/'setup.bin'),source_us=math.ceil(max(v['source_s'] for v in setup_samples)*1e6),receiver_us=math.ceil(max(v['receiver_s'] for v in setup_samples)*1e6));(p/'messages').mkdir();oldrows={r['id']:r for r in prior['rows']};test=[r for r in rows if r['split']=='test']
 for j,r in enumerate(test):
  old=oldrows[r['id']];bp=r['blueprint'];extent=catalog[bp];delta=slacks[bp];params=parameters(extent,delta);g=geometry(projections(r['hulls_cm']),params);s=sphere_geometry(r['hulls_cm'],params['body_um']+8000+delta,params['body_um']);r['pose_geometry']=g;r['sphere_geometry']=s;r['parameters']=params;r['methods']={};xyz,T,path=load(old);ci=list(catalog).index(bp);selection=max(v['selection_s'] for mm in old['methods'].values() for v in mm['samples']);common_samples=[]
  for _ in range(3):
   t=time.perf_counter();xx=xyz.copy();gg=groups(xx,T,np.array(basis['anchor']),np.array(basis['road']),extent,bg['layouts'][str(r['layout'])]['codes']);hh=[hull(group) for group in gg];assert hh==r['hulls_cm'];wire=pack('hull',hh,ci,r['layout'],r['frame'],r['source_us'],contract,calibration);ss=time.perf_counter()-t;common_samples.append(ss)
  packet=p/'messages'/(r['id']+'_hull.bin');packet.write_bytes(wire);r['common_hull_samples_s']=common_samples
  for policy in POLICIES:
   expected=infer(r['hulls_cm'],extent,delta,policy);samples=[]
   for k in range(3):
    if policy=='joint_raw':
     t=time.perf_counter();ww=pack_raw(xyz.copy(),T,ci,old['frame'],old['timestamp'],rc['contract'],rc['calibration']);ss=time.perf_counter()-t
    else:ww=wire;ss=common_samples[k]
    t=time.perf_counter();decoded=unpack(ww,policy,context,contract,calibration);rx=time.perf_counter()-t;assert all(decoded[k]==v for k,v in expected.items()) and decoded['source_us']==r['source_us'] and decoded['layout']==r['layout'] and decoded['frame']==r['frame'];samples.append(dict(source_s=ss,receiver_s=rx,selection_s=selection))
   if policy=='joint_raw':packet0=PP/old['methods']['full_xyz']['packet'];assert packet0.read_bytes()==ww;inputs[str(packet0.relative_to(ROOT))]=sha(packet0)
   else:packet0=packet
   r['methods'][policy]=dict(**expected,samples=samples,source_us=math.ceil((max(v['source_s'] for v in samples)+selection)*1e6),receiver_us=math.ceil(max(v['receiver_s'] for v in samples)*1e6),packet=str(packet0.relative_to(ROOT)),wire_bytes=len(ww),wire_sha256=sha(packet0))
  if (j+1)%200==0:print('paid',j+1,flush=True)
 byep=defaultdict(list)
 for r in test:byep[r['episode_id']].append(r)
 traces=[];planned=[e for e in prior['episodes'] if e['episode']['split']=='test']
 for e in planned:
  ep=e['episode'];rr=byep[ep['id']];t0=min(r['source_us'] for r in rr) if rr else 0
  for policy in POLICIES:
   for rate in (20000000,2000000):
    for startup in ('warm','cold'):traces.append(dict(episode_id=ep['id'],blueprint=ep['blueprint'],capture_status=e['status'],method=policy,rate=rate,startup=startup,t0=t0,**replay(rr,policy,rate,t0,setup if startup=='cold' else None)))
 result=dict(rows=rows,traces=traces,setup=setup,context=context,contract_sha256=contract,calibration_sha256=calibration,registry=registry,joint_episode_scores=dict(joint_scores),source_hashes=frozen['sources'],input_hashes=inputs,scope=context['scope'],source_profile_scope='Three complete common XYZ copy/frontend/hull/encode measurements shared identically by the three identical hull wires, plus inherited original selection maximum. Raw separately pays copy+encode; receivers pay their complete actual policy separately. No cached geometry timing; no WCET.')
 write(p/'analysis_sheng.json',result);print('complete',len(rows),len(traces),flush=True)
if __name__=='__main__':main()
