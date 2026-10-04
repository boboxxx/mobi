#!/usr/bin/env python3
"""Independent hull-equivalence and unchanged-source FIFO follow-up audit."""
import argparse,hashlib,importlib.util,json,math
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('independent_hull',ROOT/'experiments/body_expiry_20261004/audit.py');ind=importlib.util.module_from_spec(spec);spec.loader.exec_module(ind)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results;f=read(E/'raw_optimization_freeze.json');d=read(p/'analysis_sheng.json');x=read(p/'raw_optimized_sheng.json');assert x['freeze_sha256']==sha(E/'raw_optimization_freeze.json')
 for sec in ('sources','inputs'):
  for n,h in f[sec].items():assert sha(ROOT/n)==h,n
 au=read(p/'audit_sheng.json');assert au['analysis_sha256']==sha(p/'analysis_sheng.json') and au['source_sha256']==sha(E/'audit.py')
 old={r['id']:r for r in d['rows'] if r['split']=='test'};support={r['id']:r for r in read(ROOT/'results/background_frontend_20261004/body_support_sheng.json')['rows']};byep=defaultdict(list);seen=set();points=0
 for r in x['rows']:
  assert r['id'] not in seen;seen.add(r['id']);o=old[r['id']];m=o['methods']['joint_raw'];assert r['episode_id']==o['episode_id'] and r['blueprint']==o['blueprint'];expected=dict(status=m['status'],lower_us=m['lower_us'],class_index=list(d['context']['catalog']).index(o['blueprint']),frame=o['frame'],source_us=o['source_us'],layout=o['layout']);assert r['decoded']==expected and r['hulls_cm']==o['hulls_cm']
  gs=support[r['id']]['groups_cm'];assert len(gs)==len(r['hulls_cm'])
  for g,h in zip(gs,r['hulls_cm']):ind.check_hull(g,h);points+=len(g)
  for k in ('packet','wire_sha256','wire_bytes','source_us'):assert r[k]==m[k]
  path=ROOT/r['packet'];assert sha(path)==r['wire_sha256'] and path.stat().st_size==r['wire_bytes'];assert len(r['receiver_samples_s'])==3 and min(r['receiver_samples_s'])>0 and r['receiver_us']==math.ceil(max(r['receiver_samples_s'])*1e6)
  byep[r['episode_id']].append(dict(o,methods={'joint_raw':dict(m,receiver_us=r['receiver_us'])}))
 assert seen==set(old) and len(x['traces'])==1440;traces=set()
 orig={(t['episode_id'],t['rate'],t['startup']):t for t in d['traces'] if t['method']=='joint_raw'}
 for t in x['traces']:
  key=(t['episode_id'],t['rate'],t['startup']);assert key not in traces;traces.add(key);o=orig[key];assert all(t[k]==o[k] for k in ('episode_id','blueprint','capture_status','method','rate','startup','t0'));rr=byep[t['episode_id']];v=ind.independent_replay(rr,'joint_raw',t['rate'],t['t0'],d['setup'] if t['startup']=='cold' else None);assert all(t[k]==value for k,value in v.items())
 policies=[dict(rate=rate,startup=startup,grants=sum(t['grants'] for t in x['traces'] if t['rate']==rate and t['startup']==startup),scheduled_queries=11520) for rate in (20000000,2000000) for startup in ('warm','cold')];assert policies==x['policies']
 out=dict(frames=len(seen),all_quantized_point_checks=points,trace_checks=len(traces),decision_checks=len(traces)*32,policies=policies,source_sha256=sha(Path(__file__)),analysis_sha256=sha(p/'raw_optimized_sheng.json'),primary_audit_sha256=sha(p/'audit_sheng.json'),scope='Independent full-group hull checks and immutable primary audited geometry/RAW provenance; new receiver maxima and full three-FIFO replay.');a.out.write_text(json.dumps(out,separators=(',',':'))+'\n');print(json.dumps(policies),flush=True)
if __name__=='__main__':main()
