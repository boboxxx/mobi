#!/usr/bin/env python3
"""Matched bytes and historical decision semantics, never recost physical driving."""
import base64,gzip,hashlib,json
from pathlib import Path
import runtime as R
import compact_deadline as C
E=Path(__file__).resolve().parent;P=R.ROOT/'results'/E.name
def main():
 f=json.loads((E/'compact_freeze.json').read_bytes())
 for section in ('sources','inputs'):
  for n,h in f[section].items():assert R.sha(R.ROOT/n)==h,n
 ctx=json.loads((P/'capture/context.json').read_bytes());outcomes=json.loads((P/'capture/outcomes.json').read_bytes());path=P/'compact_cases.jsonl';assert not path.exists() and not (P/'compact_sheng.json').exists()
 count=gate_checks=function_total=compact_total=deadline_original_total=0;rows=[]
 with path.open('x') as stream:
  for outcome in outcomes:
   file=P/'capture'/outcome['file'];assert R.sha(file)==outcome['sha256']
   logical=gzip.decompress(file.read_bytes());assert len(logical)==outcome['logical_bytes'] and hashlib.sha256(logical).hexdigest()==outcome['logical_sha256']
   data=json.loads(logical);assert outcome['status']=='captured';body=data['body'];by_source={}
   for s in data['sources']:
    original=s['meta']['original'];proposal=s['meta']['source_proposal']
    if proposal is None:proposal=R.evidence(original,ctx).query(R.query_position(s['own'],ctx['basis']),R.action_radius(body)+150000)
    function_wire=R.pack(dict(original,kind='function'));compact_wire=C.encode(original,proposal);decoded=C.decode(compact_wire,ctx)
    for k,v in decoded['obj']['proposal'].items():assert proposal[k]==v,k
    by_source[s['step']]=decoded
    if original['kind']=='function':assert function_wire==(P/'capture/packets'/s['packet']).read_bytes()
    else:deadline_original_total+=s['wire_bytes']
    function_total+=len(function_wire);compact_total+=len(compact_wire);count+=1
    stream.write(json.dumps(dict(episode=outcome['request']['id'],step=s['step'],function_bytes=len(function_wire),function_sha256=hashlib.sha256(function_wire).hexdigest(),compact_deadline_bytes=len(compact_wire),compact_deadline_sha256=hashlib.sha256(compact_wire).hexdigest(),compact_deadline_base64=base64.b64encode(compact_wire).decode()),separators=(',',':'),sort_keys=True)+'\n')
   if outcome['request']['method']=='deadline':
    for row in data['rows']:
     if row['cache_source_step'] is None:continue
     _,gate=R.choose(by_source[row['cache_source_step']],row['own'],body,ctx,row['now_us']+row['query_fee_us'])
     assert gate==row['gate'];gate_checks+=1
   rows.append(dict(episode=outcome['request']['id'],sources=len(data['sources'])))
 assert count==1920
 result=dict(matched_source_observations=count,original_deadline_gates_verified=gate_checks,function_bytes=function_total,compact_deadline_bytes=compact_total,original_deadline_bytes_on_its960_scans=deadline_original_total,cases_sha256=R.sha(path),freeze_sha256=R.sha(E/'compact_freeze.json'),all_source_expiry_and_domain_semantics_preserved=True,old_driving_or_timing_rewritten=False,new_risk_or_radio_or_driving_qualified=False,goal_complete=False,scope='All paired same-input serialization and historical gate regression; no new physical outcome or latency inference.')
 (P/'compact_sheng.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
