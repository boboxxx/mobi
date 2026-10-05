#!/usr/bin/env python3
"""Post-result descriptive diagnosis; no fitting, changed control, or inference."""
import argparse,gzip,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=R/'results'/E.name
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);a=a.parse_args()
 audit=json.loads((P/'audit_sheng.json').read_text());outcomes=json.loads((P/'capture/outcomes.json').read_text());by={x['request']['id']:x for x in outcomes};rows=[]
 for ep in audit['episodes']:
  o=by[ep['id']];p=P/'capture'/o['file'];assert sha(p)==o['sha256'];d=json.loads(gzip.decompress(p.read_bytes()));s=d['sources'];assert len(s) in (20,30)
  fees=sorted(x['receiver_fee_us'] for x in s if x['receiver_fee_us'] is not None)
  runs=[];run=0
  for x in d['attempts']:
   if x['engineering_go']:run+=1
   elif run:runs.append(run);run=0
  if run:runs.append(run)
  row={k:ep[k] for k in ('id','variant','blueprint','method','forward_m','engineering_go','wire_bytes','received','dropped','collisions','source_sets_not_containing_target','engineering_go_from_uncovered_source')}
  row.update(source_packets=len(s),max_consecutive_go_steps=max(runs,default=0),receiver_fee_max_us=max(fees,default=0));rows.append(row)
 result=dict(audit_sha256=sha(P/'audit_sheng.json'),outcomes_sha256=sha(P/'capture/outcomes.json'),episodes=rows,scope='Post-result finite development diagnosis; nine single-run cells per variant; no statistical, deployment or novel-method claim.',joint_risk_certificate=False)
 assert not a.out.exists();a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
