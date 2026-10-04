#!/usr/bin/env python3
"""Independent actual-wire, profile, scope and full three-FIFO replay audit."""
import argparse,hashlib,importlib.util,itertools,json,math,struct,zlib
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;PP=ROOT/'results/prospective_shape_20261004';BEX=struct.Struct('<4sBBIIq32s32s');LSE=struct.Struct('<4sBBIIq32s32sqq')
spec=importlib.util.spec_from_file_location('independent_body',ROOT/'experiments/body_expiry_20261004/audit.py');ind=importlib.util.module_from_spec(spec);spec.loader.exec_module(ind)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def canon(d):return json.dumps(d,sort_keys=True,separators=(',',':')).encode()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results.resolve();d=read(p/'analysis_sheng.json');old=read(PP/'analysis_sheng.json');f=read(E/'freeze.json');ctx=d['registration'];assert d['parent_analysis_sha256']==sha(PP/'analysis_sheng.json') and d['parent_audit_sha256']==sha(PP/'audit_v2_sheng.json') and d['freeze_sha256']==sha(E/'freeze.json')
 for section in ('sources','inputs'):
  for n,h in f[section].items():assert sha(ROOT/n)==h,n
 assert 'background' not in ctx and 'directions' not in ctx and 'raw_transport' not in ctx and ctx['primary_context_sha256']==old['contract_sha256'] and ctx['primary_sources']==old['source_hashes'] and ctx['catalog']==old['context']['catalog'] and ctx['registry']==old['registry'] and ctx['calibration_sha256']==old['calibration_sha256'] and ctx['calibration_receipt_sha256']==old['calibration_receipt_sha256'] and ctx['motion']==old['context']['motion'] and ctx['queries_um']==[[-6000000,0],[6000000,0]] and ctx['query_radius_um']==750000 and ctx['cap_us']==500000 and ctx['installed_grid_sha256']==sha(ROOT/'experiments/pose_support_20261004/directions.json') and ctx['new_wire_service_sha256']==sha(E/'common.py')
 wire=(p/'setup.bin').read_bytes();b=zlib.decompress(wire);assert hashlib.sha256(b[:-32]).digest()==b[-32:] and json.loads(b[:-32])==ctx and hashlib.sha256(b[:-32]).hexdigest()==d['registration_sha256'];s=d['setup'];assert len(wire)==s['wire_bytes'] and sha(p/'setup.bin')==s['wire_sha256'] and len(s['samples'])==3
 for field,key in [('source_us','source_s'),('receiver_us','receiver_s')]:assert s[field]==math.ceil(max(v[key] for v in s['samples'])*1e6)
 lookup={r['id']:r for r in old['rows'] if r['split']=='test'};assert [r['id'] for r in d['rows']]==list(lookup);byep=defaultdict(list);packets=0;grants_from_bad=defaultdict(int);bad={r['id'] for r in read(PP/'audit_v2_sheng.json')['frame_checks'] if r['split']=='test' and not r['joint_covered']}
 for r in d['rows']:
  o=lookup[r['id']];assert all(r[k]==o[k] for k in ('id','episode_id','blueprint','cloud_file','cloud_sha256','layout','frame','source_us','acquisition_us','selection_s'));assert sha(PP/'capture'/r['cloud_file'])==r['cloud_sha256'];assert set(r['methods'])=={'hull','deadline'};expected=o['methods']['joint_hull'];ci=list(ctx['catalog']).index(r['blueprint'])
  for method,m in r['methods'].items():
   wire=(ROOT/m['packet']).read_bytes();assert len(wire)==m['wire_bytes'] and sha(ROOT/m['packet'])==m['wire_sha256'];b=zlib.decompress(wire);assert hashlib.sha256(b[:-32]).digest()==b[-32:]
   if method=='hull':
    h=BEX.unpack(b[:BEX.size]);assert h==(b'BEX1',1,r['layout'],ci,r['frame'],r['source_us'],bytes.fromhex(old['contract_sha256']),bytes.fromhex(old['calibration_sha256']));assert json.loads(b[BEX.size:-32])==o['hulls_cm'];assert wire==(ROOT/expected['packet']).read_bytes()
   else:
    h=LSE.unpack(b[:-32]);status={'bounded':0,'refused':1,'empty':2}.get(expected['status'],1);assert len(b)==LSE.size+32 and h==(b'LSE1',status,r['layout'],ci,r['frame'],r['source_us'],bytes.fromhex(old['contract_sha256']),bytes.fromhex(old['calibration_sha256']),*(expected['lower_us'] if status==0 else [0,0]))
   assert (m['status'],m['lower_us'])==(expected['status'],expected['lower_us']) and len(m['samples'])==3 and all(v['selection_s']==r['selection_s'] for v in m['samples']);assert m['source_us']==math.ceil((max(v['source_s'] for v in m['samples'])+r['selection_s'])*1e6) and m['receiver_us']==math.ceil(max(v['receiver_s'] for v in m['samples'])*1e6);packets+=1
  byep[r['episode_id']].append(r)
 episodes={e['episode']['id']:e for e in old['episodes'] if e['episode']['split']=='test'};seen=set();mapping={}
 for tr in d['traces']:
  key=(tr['episode_id'],tr['method'],tr['rate'],tr['startup']);assert key not in seen;seen.add(key);ep=episodes[tr['episode_id']];rr=byep[tr['episode_id']];t0=min(r['source_us'] for r in rr) if rr else 0;assert tr['blueprint']==ep['episode']['blueprint'] and tr['capture_status']==ep['status'] and tr['t0']==t0;v=ind.independent_replay(rr,tr['method'],tr['rate'],t0,s if tr['startup']=='cold' else None);assert all(tr[k]==value for k,value in v.items());mapping[key]=tr;grants_from_bad[(tr['method'],tr['rate'],tr['startup'])]+=sum(x['grant'] and x['fact_id'] in bad for x in tr['decisions'])
 assert seen==set(itertools.product(episodes,('hull','deadline'),(20000000,2000000),('warm','cold'))) and len(seen)==2880;policies=[]
 for rate in (20000000,2000000):
  for startup in ('warm','cold'):
   g={m:sum(mapping[(ep,m,rate,startup)]['grants'] for ep in episodes) for m in ('hull','deadline')};gain=loss=0
   for ep in episodes:
    for x,y in zip(mapping[(ep,'hull',rate,startup)]['decisions'],mapping[(ep,'deadline',rate,startup)]['decisions']):gain+=int(x['grant'] and not y['grant']);loss+=int(y['grant'] and not x['grant'])
   policies.append(dict(rate=rate,startup=startup,scheduled_queries=11520,grants=g,hull_only=gain,deadline_only=loss))
 assert policies==d['policies'];out=dict(rows=len(d['rows']),actual_packet_checks=packets,trace_checks=len(seen),decision_checks=len(seen)*32,policies=policies,setup_wire_bytes=s['wire_bytes'],grants_referencing_excluded_source=[dict(method=k[0],rate=k[1],startup=k[2],count=v) for k,v in sorted(grants_from_bad.items())],source_sha256=sha(Path(__file__)),analysis_sha256=sha(p/'analysis_sheng.json'),scope='Independent source/input freeze, lighter shared setup, actual byte-identical hulls and direct age packets, complete paid profiles and exhaustive planned three-FIFO traces. Inherits unchanged source geometry/coverage event; no new qualification.');a.out.write_text(json.dumps(out,separators=(',',':'))+'\n');print(json.dumps(policies,indent=2))
if __name__=='__main__':main()
