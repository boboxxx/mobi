#!/usr/bin/env python3
"""Finite full-RAW receiver hull reduction; primary sources stay immutable."""
import argparse,hashlib,json,math,sys,time,zlib
from collections import defaultdict
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'experiments/body_expiry_20261004'))
from kernel import hull
from frontend import groups
from engine import replay
from wire import RAW,infer
from observer import DIRECTIONS
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def decode(wire,ctx):
 assert ctx['directions']==DIRECTIONS and ctx['tilt_operator_norm_upper']==[87267,1000000] and ctx['yaw_cell_distance_factor']==[8730,1000000]
 b=zlib.decompress(wire);assert hashlib.sha256(b[:-32]).digest()==b[-32:]
 h=RAW.unpack(b[:RAW.size]);rc=ctx['raw_transport'];assert h[0]==b'RXYZ' and h[5].hex()==rc['contract'] and h[6].hex()==rc['calibration'] and len(b)==RAW.size+128+h[4]*12+32
 ci,frame,source=h[1],h[2],math.floor(h[3]*1e6);catalog=ctx['catalog'];assert 0<=ci<len(catalog)
 T=np.frombuffer(b,dtype='<f8',count=16,offset=RAW.size).reshape(4,4);xyz=np.frombuffer(b,dtype='<f4',count=h[4]*3,offset=RAW.size+128).reshape(-1,3)
 matches=[int(k) for k,v in rc['transforms'].items() if np.array_equal(T,v)];assert len(matches)==1
 layout=matches[0];bp=list(catalog)[ci];gg=groups(xyz,T,np.array(ctx['basis']['anchor']),np.array(ctx['basis']['road']),catalog[bp],ctx['background']['layouts'][str(layout)]['codes']);hh=[hull(g) for g in gg]
 out=infer(hh,catalog[bp],ctx['slacks_um'][bp],'joint_raw')
 return dict(**out,class_index=ci,frame=frame,source_us=source,layout=layout),hh
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();p=a.results.resolve();out=p/'raw_optimized_sheng.json';assert not out.exists();freeze=read(E/'raw_optimization_freeze.json')
 for section in ('sources','inputs'):
  for n,h in freeze[section].items():assert sha(ROOT/n)==h,n
 d=read(p/'analysis_sheng.json');prior=read(ROOT/'results/prospective_expiry_20261003/analysis_sheng.json');rows=[];byep=defaultdict(list)
 for j,r in enumerate(v for v in d['rows'] if v['split']=='test'):
  m=r['methods']['joint_raw'];wire=(ROOT/m['packet']).read_bytes();assert sha(ROOT/m['packet'])==m['wire_sha256'];samples=[]
  expected=dict(status=m['status'],lower_us=m['lower_us'],class_index=list(d['context']['catalog']).index(r['blueprint']),frame=r['frame'],source_us=r['source_us'],layout=r['layout'])
  for _ in range(3):
   t=time.perf_counter();decoded,hh=decode(wire,d['context']);dt=time.perf_counter()-t;assert decoded==expected and hh==r['hulls_cm'];samples.append(dt)
  mm=dict(m,receiver_us=math.ceil(max(samples)*1e6));rr=dict(r,methods={'joint_raw':mm});byep[r['episode_id']].append(rr)
  rows.append(dict(id=r['id'],episode_id=r['episode_id'],blueprint=r['blueprint'],decoded=decoded,hulls_cm=hh,receiver_samples_s=samples,receiver_us=mm['receiver_us'],source_us=m['source_us'],packet=m['packet'],wire_sha256=m['wire_sha256'],wire_bytes=m['wire_bytes']))
  if (j+1)%300==0:print('optimized',j+1,flush=True)
 traces=[]
 for e in prior['episodes']:
  ep=e['episode']
  if ep['split']!='test':continue
  rr=byep[ep['id']];t0=min(r['source_us'] for r in rr) if rr else 0
  for rate in (20000000,2000000):
   for startup in ('warm','cold'):traces.append(dict(episode_id=ep['id'],blueprint=ep['blueprint'],capture_status=e['status'],method='joint_raw',rate=rate,startup=startup,t0=t0,**replay(rr,'joint_raw',rate,t0,d['setup'] if startup=='cold' else None)))
 policies=[dict(rate=rate,startup=startup,grants=sum(t['grants'] for t in traces if t['rate']==rate and t['startup']==startup),scheduled_queries=11520) for rate in (20000000,2000000) for startup in ('warm','cold')]
 out.write_text(json.dumps(dict(rows=rows,traces=traces,policies=policies,freeze_sha256=sha(E/'raw_optimization_freeze.json'),scope='Same exact RAW model/output with complete hull reduction; only receiver fee replaced. No tilt repair or prospective qualification.'),separators=(',',':'))+'\n');print(json.dumps(policies),flush=True)
if __name__=='__main__':main()
