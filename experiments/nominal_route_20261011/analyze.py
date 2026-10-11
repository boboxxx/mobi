"""Nominal task feasibility; no IID or safety certificate."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys

E=Path(__file__).parent;ROOT=E.resolve().parents[1]
sys.path.insert(0,str(ROOT/'experiments/actuator_admission_20261011'));import model as M
R=M.R
parser=argparse.ArgumentParser();parser.add_argument('--capture',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();assert not args.out.exists()
f=json.loads((E/'freeze.json').read_bytes())
for section in ('sources','inputs'):
 for name,digest in f[section].items():assert R.sha(ROOT/name)==digest,name
ctx=json.loads((ROOT/'experiments/actuator_admission_20261011/context.json').read_bytes());reports=[]
for o in json.loads((args.capture/'outcomes.json').read_bytes()):
 path=args.capture/o['file'];assert R.sha(path)==o['sha256'];raw=gzip.decompress(path.read_bytes());assert hashlib.sha256(raw).hexdigest()==o['logical_sha256'];d=json.loads(raw)
 report=dict(id=o['id'],status=o['status'])
 if o['status']=='captured':
  rows=d['rows'];assert len(rows)==830;errors=0
  for i,row in enumerate(rows):
   assert row['step']==i and row['now_us']==i*50000 and row['own']['frame']+1==row['after']['frame']
   q=R.own_position(row['own'],ctx['basis']);domain=math.hypot(*row['own']['velocity'][:2])<=.75 and -10000000<=q[0]<=6000000 and abs(q[1])<=500000
   refused=not domain or (i>0 and rows[i-1]['refused']) or any(e['frame']<=row['own']['frame'] for e in d['collisions'])
   reached=q[0]>=3000000 or (i>0 and rows[i-1]['reached']);expected=bool(3<=i<800 and not refused and not reached)
   errors+=int(expected!=row['go'] or reached!=row['reached'])
   t,b=R.relay(row['own'],expected);a=row['after']['actual'];errors+=int(abs(a['throttle']-t)>1e-6 or abs(a['brake']-b)>1e-6 or not a['manual_gear_shift'] or a['gear']!=1)
  positions=[R.own_position(r['own'],ctx['basis'])[0]/1000000 for r in rows]
  first=next((r['now_us'] for r in rows if r['reached']),None)
  report.update(first_goal_us=first,max_progress_m=max(positions)-positions[0],progress_at_30s_m=positions[600]-positions[0],
   max_speed_mps=max(math.hypot(*r['own']['velocity'][:2]) for r in rows),collisions=len(d['collisions']),refused=any(r['refused'] for r in rows),policy_errors=errors)
 else:report['exception']=d.get('exception')
 reports.append(report)
qualified=len(reports)==6 and all(r['status']=='captured' and r['first_goal_us'] is not None and r['first_goal_us']<=38500000 and not r['refused'] and not r['collisions'] and not r['policy_errors'] for r in reports)
result=dict(scope='six fixed nominal simulations, not evidence safety or risk qualification',freeze_sha256=R.sha(E/'freeze.json'),
 candidate_task_budget_us=40000000,required_headroom_us=1500000,nominal_feasible_for_fixed_40s=qualified,
 episodes=reports,goal_complete=False)
args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(qualified=qualified,first_goal_us=[r.get('first_goal_us') for r in reports],progress_at_30s_m=[r.get('progress_at_30s_m') for r in reports]),sort_keys=True))
