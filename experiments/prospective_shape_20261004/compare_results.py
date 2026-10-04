#!/usr/bin/env python3
"""Post-run presentation of independently audited fixed policies; no fitting."""
import argparse,hashlib,json
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results.resolve()
 d=read(p/'analysis_sheng.json');s=read(p/'summary_sheng.json');l=read(p/'lease_baseline_sheng.json');la=read(p/'lease_audit_sheng.json')
 assert la['analysis_sha256']==sha(p/'lease_baseline_sheng.json') and l['primary_audit_sha256']==sha(p/'audit_sheng.json') and l['primary_analysis_sha256']==sha(p/'analysis_sheng.json')
 policies=[]
 for q in s['policies']:
  rate,start=q['rate'],q['startup'];base={t['episode_id']:t for t in d['traces'] if t['method']=='joint_hull' and t['rate']==rate and t['startup']==start};entry=dict(rate=rate,startup=start,scheduled_queries=q['scheduled_queries'],primary_grants=q['grants'],lease={})
  for reg in ('full','minimal'):
   tt=[t for t in l['traces'] if t['registration']==reg and t['rate']==rate and t['startup']==start];gain=loss=0
   assert len(tt)==len(base)==360
   for t in tt:
    b=base[t['episode_id']];assert len(b['decisions'])==len(t['decisions'])==32
    for x,y in zip(t['decisions'],b['decisions']):
     assert (x['now_us'],x['query'])==(y['now_us'],y['query'])
     gain+=int(x['grant'] and not y['grant']);loss+=int(y['grant'] and not x['grant'])
   entry['lease'][reg]=dict(grants=sum(t['grants'] for t in tt),lease_only=gain,joint_hull_only=loss)
  policies.append(entry)
 out=dict(policies=policies,primary_setup_bytes=d['setup']['wire_bytes'],minimal_lease_setup_bytes=l['minimal_setup']['wire_bytes'],source_sha256=sha(Path(__file__)),analysis_sha256=sha(p/'lease_baseline_sheng.json'),primary_analysis_sha256=sha(p/'analysis_sheng.json'),primary_summary_sha256=sha(p/'summary_sheng.json'),lease_analysis_sha256=sha(p/'lease_baseline_sheng.json'),lease_audit_sha256=sha(p/'lease_audit_sheng.json'),scope='Post-run exact paired descriptive utility comparison of unchanged, audited policies. No refitting, new qualification or attestation claim.')
 a.out.write_text(json.dumps(out,separators=(',',':'))+'\n');print(json.dumps(policies,indent=2))
if __name__=='__main__':main()
