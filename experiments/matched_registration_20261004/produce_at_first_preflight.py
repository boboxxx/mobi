#!/usr/bin/env python3
"""One finite matched-registration paid replay; no capture/model/risk refit."""
import argparse,hashlib,math,time
from collections import defaultdict
from pathlib import Path
import numpy as np
from common import ROOT,E,PARENT,parent,lease,sha,read,write,canon,registration,encode_setup,decode_setup,decode
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();p=a.results.resolve();p.mkdir(exist_ok=True);assert not (p/'analysis_sheng.json').exists();f=read(E/'freeze.json')
 for section in ('sources','inputs'):
  for n,h in f[section].items():assert sha(ROOT/n)==h,n
 d=read(PARENT/'analysis_sheng.json');ctx=registration(d);ctx_hash=hashlib.sha256(canon(ctx)).hexdigest();samples=[]
 for _ in range(3):
  t=time.perf_counter();wire=encode_setup(ctx);ss=time.perf_counter()-t;t=time.perf_counter();assert decode_setup(wire,ctx_hash)==ctx;rx=time.perf_counter()-t;samples.append(dict(source_s=ss,receiver_s=rx))
 (p/'setup.bin').write_bytes(wire);setup=dict(samples=samples,wire_bytes=len(wire),wire_sha256=sha(p/'setup.bin'),source_us=math.ceil(max(v['source_s'] for v in samples)*1e6),receiver_us=math.ceil(max(v['receiver_s'] for v in samples)*1e6));(p/'messages').mkdir();rows=[];byep=defaultdict(list)
 for j,r in enumerate(v for v in d['rows'] if v['split']=='test'):
  cloud=PARENT/'capture'/r['cloud_file'];assert sha(cloud)==r['cloud_sha256']
  with np.load(cloud) as z:raw=z['raw'];T=z['transform'].copy()
  bp=r['blueprint'];extent=ctx['catalog'][bp];ci=list(ctx['catalog']).index(bp);methods={}
  for method in ('hull','deadline'):
   profiles=[]
   for _ in range(3):
    t=time.perf_counter();xyz=np.c_[raw['x'],raw['y'],raw['z']].astype('<f4');gg=parent.groups(xyz,T,np.asarray(d['context']['basis']['anchor']),np.asarray(d['context']['basis']['road']),extent,d['context']['background']['layouts'][str(r['layout'])]['codes']);hh=[parent.hull(g) for g in gg]
    if method=='hull':packet=parent.pack(hh,ci,r['layout'],r['frame'],r['source_us'],ctx['primary_context_sha256'],ctx['calibration_sha256'])
    else:packet=lease.encode(parent.infer(hh,extent,ctx['registry'][bp]['joint_slack_um'],'joint_hull'),ci,r['layout'],r['frame'],r['source_us'],ctx['primary_context_sha256'],ctx['calibration_sha256'])
    ss=time.perf_counter()-t;t=time.perf_counter();out=decode(packet,method,ctx);rx=time.perf_counter()-t;assert hh==r['hulls_cm'] and (out['status'],out['lower_us'])==(r['methods']['joint_hull']['status'],r['methods']['joint_hull']['lower_us']) and out['source_us']==r['source_us'] and out['frame']==r['frame'] and out['class_index']==ci and out['layout']==r['layout'];profiles.append(dict(source_s=ss,receiver_s=rx,selection_s=r['selection_s']))
   target=p/'messages'/(r['id']+'_'+method+'.bin');target.write_bytes(packet);methods[method]=dict(status=out['status'],lower_us=out['lower_us'],samples=profiles,source_us=math.ceil((max(v['source_s'] for v in profiles)+r['selection_s'])*1e6),receiver_us=math.ceil(max(v['receiver_s'] for v in profiles)*1e6),wire_bytes=len(packet),wire_sha256=sha(target),packet=str(target.relative_to(ROOT)))
  item=dict(id=r['id'],episode_id=r['episode_id'],blueprint=bp,cloud_file=r['cloud_file'],cloud_sha256=r['cloud_sha256'],layout=r['layout'],frame=r['frame'],source_us=r['source_us'],acquisition_us=r['acquisition_us'],selection_s=r['selection_s'],methods=methods);rows.append(item);byep[r['episode_id']].append(item)
  if (j+1)%300==0:print('matched paid',j+1,flush=True)
 traces=[]
 for ep in d['episodes']:
  e=ep['episode']
  if e['split']!='test':continue
  rr=byep[e['id']];t0=min(r['source_us'] for r in rr) if rr else 0
  for method in ('hull','deadline'):
   for rate in (20000000,2000000):
    for startup in ('warm','cold'):traces.append(dict(episode_id=e['id'],blueprint=e['blueprint'],capture_status=ep['status'],method=method,rate=rate,startup=startup,t0=t0,**parent.replay(rr,method,rate,t0,setup if startup=='cold' else None)))
 policies=[]
 for rate in (20000000,2000000):
  for startup in ('warm','cold'):
   mapping={method:{t['episode_id']:t for t in traces if t['method']==method and t['rate']==rate and t['startup']==startup} for method in ('hull','deadline')};gain=loss=0
   for ep,t in mapping['hull'].items():
    for x,y in zip(t['decisions'],mapping['deadline'][ep]['decisions']):gain+=int(x['grant'] and not y['grant']);loss+=int(y['grant'] and not x['grant'])
   policies.append(dict(rate=rate,startup=startup,scheduled_queries=11520,grants={m:sum(t['grants'] for t in mapping[m].values()) for m in mapping},hull_only=gain,deadline_only=loss))
 write(p/'analysis_sheng.json',dict(rows=rows,traces=traces,policies=policies,setup=setup,registration=ctx,registration_sha256=ctx_hash,parent_analysis_sha256=sha(PARENT/'analysis_sheng.json'),parent_audit_sha256=sha(PARENT/'audit_v2_sheng.json'),freeze_sha256=sha(E/'freeze.json'),scope='Reused fresh-study data for finite matched lightweight registration and newly paid same-inference hull/deadline jobs. Original source coverage event/registry unchanged; no new qualification or capture, radio, physical guarantee, dynamic-query utility or MobiCom novelty.'));print('complete',len(rows),len(traces),flush=True)
if __name__=='__main__':main()
