#!/usr/bin/env python3
"""Finite directly transmitted source deadlines with full/minimal registration."""
import argparse,hashlib,json,math,struct,sys,time,zlib
from collections import defaultdict
from pathlib import Path
import numpy as np
E=Path(__file__).resolve().parent;sys.path.insert(0,str(E))
from evaluate import ROOT,groups,hull,infer,read,canon,write,sha,replay
HEADER=struct.Struct('<4sBBIIq32s32sqq');STATUS={'bounded':0,'refused':1,'empty':2}
def encode(decoded,ci,layout,frame,source,contract,calibration):
 status=decoded['status'];status=status if status in STATUS else 'refused';values=decoded['lower_us'] if status=='bounded' else [0,0];blob=HEADER.pack(b'LSE1',STATUS[status],layout,ci,frame,source,bytes.fromhex(contract),bytes.fromhex(calibration),*values);return zlib.compress(blob+hashlib.sha256(blob).digest(),6)
def decode(wire,contract,calibration,catalog):
 b=zlib.decompress(wire);assert len(b)==HEADER.size+32 and hashlib.sha256(b[:-32]).digest()==b[-32:];h=HEADER.unpack(b[:-32]);assert h[0]==b'LSE1' and h[1] in (0,1,2) and h[2] in (0,1) and 0<=h[3]<len(catalog) and h[6].hex()==contract and h[7].hex()==calibration and all(0<=v<=500000 for v in h[8:]);status=('bounded','refused','empty')[h[1]];assert status=='bounded' or h[8:]==(0,0);return dict(status=status,lower_us=list(h[8:]) if status=='bounded' else [],class_index=h[3],layout=h[2],frame=h[4],source_us=h[5])
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();p=a.results.resolve();assert (p/'run_terminal.txt').read_text()=='FINITE_PROSPECTIVE_SHAPE_COMPLETE\n' and not (p/'lease_baseline_sheng.json').exists();f=read(E/'lease_baseline_freeze.json')
 for n,h in f['sources'].items():assert sha(ROOT/n)==h,n
 d=read(p/'analysis_sheng.json');ctx=d['context'];minimal=dict(kind='honest registered source deadlines, no source-execution attestation',primary_context_sha256=d['contract_sha256'],primary_source_hashes=ctx['source_hashes'],catalog=ctx['catalog'],registry=d['registry'],queries_um=[[-6000000,0],[6000000,0]],query_radius_um=750000,cap_us=500000,calibration_receipt_sha256=d['calibration_receipt_sha256'],source_identity_sha256=sha(E/'lease_baseline.py'));contract=hashlib.sha256(canon(minimal)).hexdigest();samples=[]
 for _ in range(3):
  t=time.perf_counter();b=canon(minimal);setup_wire=zlib.compress(b+hashlib.sha256(b).digest(),6);source_s=time.perf_counter()-t;t=time.perf_counter();bb=zlib.decompress(setup_wire);assert hashlib.sha256(bb[:-32]).digest()==bb[-32:] and json.loads(bb[:-32])==minimal;receiver_s=time.perf_counter()-t;samples.append(dict(source_s=source_s,receiver_s=receiver_s))
 (p/'lease_setup_minimal.bin').write_bytes(setup_wire);setup=dict(samples=samples,wire_bytes=len(setup_wire),wire_sha256=sha(p/'lease_setup_minimal.bin'),source_us=math.ceil(max(v['source_s'] for v in samples)*1e6),receiver_us=math.ceil(max(v['receiver_s'] for v in samples)*1e6));(p/'lease_messages').mkdir();rows=[];byep=defaultdict(list)
 for j,r in enumerate(v for v in d['rows'] if v['split']=='test'):
  path=p/'capture'/r['cloud_file'];assert sha(path)==r['cloud_sha256']
  with np.load(path) as z:raw=z['raw'];T=z['transform'].copy()
  bp=r['blueprint'];extent=ctx['catalog'][bp];ci=list(ctx['catalog']).index(bp);expected=r['methods']['joint_hull'];profiles=[]
  for _ in range(3):
   t=time.perf_counter();xyz=np.c_[raw['x'],raw['y'],raw['z']].astype('<f4');gg=groups(xyz,T,np.asarray(ctx['basis']['anchor']),np.asarray(ctx['basis']['road']),extent,ctx['background']['layouts'][str(r['layout'])]['codes']);hh=[hull(g) for g in gg];out=infer(hh,extent,ctx['slacks_um'][bp],'joint_hull');wire=encode(out,ci,r['layout'],r['frame'],r['source_us'],contract,d['calibration_sha256']);ss=time.perf_counter()-t;t=time.perf_counter();decoded=decode(wire,contract,d['calibration_sha256'],ctx['catalog']);rx=time.perf_counter()-t;assert hh==r['hulls_cm'] and (decoded['status'],decoded['lower_us'])==(expected['status'],expected['lower_us']) and decoded['source_us']==r['source_us'] and decoded['frame']==r['frame'] and decoded['class_index']==ci and decoded['layout']==r['layout'];profiles.append(dict(source_s=ss,receiver_s=rx,selection_s=r['selection_s']))
  packet=p/'lease_messages'/(r['id']+'.bin');packet.write_bytes(wire);m=dict(status=decoded['status'],lower_us=decoded['lower_us'],samples=profiles,source_us=math.ceil((max(v['source_s'] for v in profiles)+r['selection_s'])*1e6),receiver_us=math.ceil(max(v['receiver_s'] for v in profiles)*1e6),packet=str(packet.relative_to(ROOT)),wire_bytes=len(wire),wire_sha256=sha(packet));rows.append(dict(id=r['id'],episode_id=r['episode_id'],blueprint=bp,method=m));byep[r['episode_id']].append(dict(r,methods={'lease':m}))
  if (j+1)%300==0:print('lease paid',j+1,flush=True)
 traces=[]
 for ep in d['episodes']:
  e=ep['episode']
  if e['split']!='test':continue
  rr=byep[e['id']];t0=min(r['source_us'] for r in rr) if rr else 0
  for registration,reg in [('full',d['setup']),('minimal',setup)]:
   for rate in (20000000,2000000):
    for startup in ('warm','cold'):traces.append(dict(episode_id=e['id'],blueprint=e['blueprint'],capture_status=ep['status'],method='lease',registration=registration,rate=rate,startup=startup,t0=t0,**replay(rr,'lease',rate,t0,reg if startup=='cold' else None)))
 policies=[dict(registration=reg,rate=rate,startup=startup,grants=sum(t['grants'] for t in traces if t['registration']==reg and t['rate']==rate and t['startup']==startup),scheduled_queries=11520) for reg in ('full','minimal') for rate in (20000000,2000000) for startup in ('warm','cold')];write(p/'lease_baseline_sheng.json',dict(rows=rows,traces=traces,minimal_context=minimal,minimal_contract_sha256=contract,minimal_setup=setup,policies=policies,primary_analysis_sha256=sha(p/'analysis_sheng.json'),primary_audit_sha256=sha(p/'audit_sheng.json'),freeze_sha256=sha(E/'lease_baseline_freeze.json'),scope='Finite trusted registered-source lower deadlines. Same calibrated predictor and primary source ages, complete new source/receiver fees; full and actual minimal receiver registration. No new risk/attestation/physical guarantee.'));print(json.dumps(policies),flush=True)
if __name__=='__main__':main()
