#!/usr/bin/env python3
"""Finite four-wire paid comparison on an explicitly reused development corpus."""
import argparse,hashlib,json,math,platform,subprocess,time,zlib
from collections import defaultdict
from pathlib import Path
import numpy as np
from frontend import groups
from kernel import geometry,hull
from codec import pack,pack_raw,active_data,unpack,METHODS
from engine import replay
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent
PP=ROOT/'results/prospective_expiry_20261003';PB=ROOT/'results/background_frontend_20261004'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def canonical(d):return json.dumps(d,sort_keys=True,separators=(',',':')).encode()
def write(p,d):p.write_text(json.dumps(d,separators=(',',':'))+'\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();p=a.results.resolve();p.mkdir(parents=True,exist_ok=True);assert not (p/'analysis_sheng.json').exists()
 frozen=read(E/'freeze.json')
 for name,h in frozen['sources'].items():assert sha(ROOT/name)==h,name
 old=read(PP/'analysis_sheng.json');support=read(PB/'body_support_sheng.json');bg=read(PB/'background.json');catalog=old['contract_body']['catalog'];basis=old['contract_body']['basis'];slacks={bp:v['development_slack_um'] for bp,v in support['registry'].items()};assert set(slacks.values())=={0}
 test=[r for r in old['rows'] if r['split']=='test'];planned=[e for e in old['episodes'] if e['episode']['split']=='test'];ref={r['id']:r for r in support['rows']};transforms={}
 for r in old['rows']:
  key=str(r['layout']);T=r['sensor_transform']['matrix'];assert r['anchor']==basis['anchor'] and r['road']==basis['road'];assert key not in transforms or transforms[key]==T;transforms[key]=T
 raw_context=dict(contract=old['contract_sha256'],calibration=old['calibration_sha256'],transforms=transforms)
 context=dict(catalog=catalog,basis=basis,slacks_um=slacks,background_sha256=sha(PB/'background.json'),raw_transport=raw_context,source_hashes=frozen['sources'],point_quantization_allowance_um=8000,motion=dict(speed_um_s=5000000,acceleration_um_s2=3000000),query_radius_um=750000,queries_um=[[-6000000,0],[6000000,0]],cap_us=500000,scope='Reused fixed-scene development model; no prospective risk qualification, live link or continuous mesh guarantee')
 contract=hashlib.sha256(canonical(context)).hexdigest();calibration=hashlib.sha256(canonical(support['registry'])).hexdigest();setupdata=dict(context=context,background=bg);setup_samples=[]
 for _ in range(3):
  t=time.perf_counter();payload=canonical(setupdata);wire=zlib.compress(payload+hashlib.sha256(payload).digest(),6);ss=time.perf_counter()-t;t=time.perf_counter();b=zlib.decompress(wire);assert hashlib.sha256(b[:-32]).digest()==b[-32:];parsed=json.loads(b[:-32]);assert parsed==setupdata;rr=time.perf_counter()-t;setup_samples.append(dict(source_s=ss,receiver_s=rr))
 (p/'setup.bin').write_bytes(wire);setup=dict(samples=setup_samples,wire_bytes=len(wire),wire_sha256=sha(p/'setup.bin'),source_us=math.ceil(max(v['source_s'] for v in setup_samples)*1e6),receiver_us=math.ceil(max(v['receiver_s'] for v in setup_samples)*1e6))
 (p/'messages').mkdir();rows=[];inputs={str((PP/'analysis_sheng.json').relative_to(ROOT)):sha(PP/'analysis_sheng.json'),str((PB/'body_support_sheng.json').relative_to(ROOT)):sha(PB/'body_support_sheng.json'),str((PB/'background.json').relative_to(ROOT)):sha(PB/'background.json')};native=dict(compiler=subprocess.check_output(['c++','--version']).decode().splitlines()[0],platform=platform.platform(),proposer_source_sha256=sha(E/'proposer.cpp'),local_binary_sha256=sha(E/'proposer.so'));write(p/'native_build_sheng.json',native)
 for j,r in enumerate(test):
  path=PP/'capture'/r['cloud_file'];assert sha(path)==r['cloud_sha256'];inputs[str(path.relative_to(ROOT))]=sha(path)
  with np.load(path) as z:raw=z['raw'];xyz=np.c_[raw['x'],raw['y'],raw['z']].astype('<f4');T=z['transform'].copy()
  assert T.tolist()==transforms[str(r['layout'])];bp=r['blueprint'];ci=list(catalog).index(bp);ext=catalog[bp];body=math.ceil(math.sqrt(sum(v*v for v in ext))*1e6);radius=body+8000+slacks[bp];gg=groups(xyz,T,np.asarray(basis['anchor']),np.asarray(basis['road']),ext,bg['layouts'][str(r['layout'])]['codes']);assert gg==ref[r['id']]['groups_cm'];g=geometry(gg,radius,body);methods={}
  selection=max(v['selection_s'] for m in r['methods'].values() for v in m['samples'])
  for method in METHODS:
   samples=[]
   for k in range(3):
    start=time.perf_counter();xx=xyz.copy()
    if method=='raw':ww=pack_raw(xx,T,ci,r['frame'],r['timestamp'],raw_context['contract'],raw_context['calibration'])
    else:
     gs=groups(xx,T,np.asarray(basis['anchor']),np.asarray(basis['road']),ext,bg['layouts'][str(r['layout'])]['codes'])
     if method=='active':data=active_data(geometry(gs,radius,body))
     elif method=='hull':data=[hull(v) for v in gs]
     else:data=gs
     ww=pack(method,data,ci,r['layout'],r['frame'],r['source_us'],contract,calibration)
    source_s=time.perf_counter()-start;start=time.perf_counter();decoded=unpack(ww,method,contract,calibration,catalog,bg,basis,slacks,raw_context);receiver_s=time.perf_counter()-start;assert decoded['source_us']==r['source_us'] and decoded['frame']==r['frame'] and decoded['layout']==r['layout'];expected=dict(status=g['status'],lower_us=[q['lower_us'] for q in g['queries']] if g['status']=='bounded' else []);assert all(decoded[k]==v for k,v in expected.items()),(r['id'],method,expected,decoded);samples.append(dict(source_s=source_s,receiver_s=receiver_s,selection_s=selection))
   if method=='raw':packet=PP/r['methods']['full_xyz']['packet'];assert packet.read_bytes()==ww;inputs[str(packet.relative_to(ROOT))]=sha(packet)
   else:packet=p/'messages'/(r['id']+'_'+method+'.bin');packet.write_bytes(ww)
   methods[method]=dict(**expected,packet=str(packet.relative_to(ROOT)),wire_bytes=len(ww),wire_sha256=sha(packet),samples=samples,source_us=math.ceil((max(v['source_s'] for v in samples)+selection)*1e6),receiver_us=math.ceil(max(v['receiver_s'] for v in samples)*1e6))
  rows.append(dict(id=r['id'],episode_id=r['episode_id'],blueprint=bp,layout=r['layout'],frame=r['frame'],source_us=r['source_us'],acquisition_us=r['acquisition_us'],body_um=body,radius_um=radius,geometry=g,methods=methods))
  if (j+1)%100==0:print('processed',j+1,len(test),flush=True)
 byep=defaultdict(list)
 for r in rows:byep[r['episode_id']].append(r)
 traces=[]
 for e in planned:
  ep=e['episode'];rr=byep[ep['id']];t0=min(r['source_us'] for r in rr) if rr else 0
  for method in METHODS:
   for rate in (20000000,2000000):
    for startup in ('warm','cold'):traces.append(dict(episode_id=ep['id'],blueprint=ep['blueprint'],capture_status=e['status'],method=method,rate=rate,startup=startup,t0=t0,**replay(rr,method,rate,t0,setup if startup=='cold' else None)))
 result=dict(rows=rows,traces=traces,setup=setup,context=context,contract_sha256=contract,calibration_sha256=calibration,input_hashes=inputs,source_hashes=frozen['sources'],scope=context['scope'],planned_test_episodes=len(planned),test_frames=len(test),sampling_scope='Stored original stride-four XYZ. Source charges inherited max measured original selection across parent methods plus each new timed copy/frontend/geometry/encode. Three maxima are observed costs, not WCET. No labels or truth enter runtime.')
 write(p/'analysis_sheng.json',result);print('complete',len(rows),len(traces),flush=True)
if __name__=='__main__':main()
