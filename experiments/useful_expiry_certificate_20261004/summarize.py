#!/usr/bin/env python3
"""All held-out drive queries; no subset tuning or unpaired causal claim."""
import argparse,gzip,hashlib,json,math
from fractions import Fraction as F
from pathlib import Path
import numpy as np
import runtime as R
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name

def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(v):
 if not v:return dict(count=0)
 a=sorted(F.from_float(float(x)) for x in v)
 def quantile(p):
  t=(len(a)-1)*p;i=t.numerator//t.denominator;j=min(i+1,len(a)-1)
  return float(a[i]+(a[j]-a[i])*(t-i))
 return dict(count=len(v),min=float(a[0]),median=quantile(F(1,2)),p95=quantile(F(19,20)),max=float(a[-1]))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists()
 f=read(E/'freeze.json')
 for sec in ('sources','inputs'):
  for n,h in f[sec].items():assert sha(ROOT/n)==h,n
 policy=read(P/'policy_frozen.json');audit=read(P/'audit_test_sheng.json');outcomes=read(P/'test_capture/outcomes.json');ctx=read(P/'test_capture/context.json');assert len(outcomes)==72 and audit['split']=='test' and policy['test_capture_absent_when_frozen'] and audit['outcomes_sha256']==sha(P/'test_capture/outcomes.json')
 cells=[];cases=[]
 for method in ('function','deadline','cone'):
  group=[o for o in outcomes if o['request']['method']==method];assert len(group)==24;progress=[];loss=[];slack=[];source_fees=[];rx_fees=[];query_fees=[];wire=[];missing=raweligible=go=0;over=0;episode_reports=[]
  for o in group:
   q=P/'test_capture'/o['file'];assert sha(q)==o['sha256'];d=json.loads(gzip.decompress(q.read_bytes()));rows=d['rows'];sources={v['step']:v for v in d['sources']}
   if o['status']!='captured':episode_reports.append(dict(id=o['request']['id'],status=o['status'],attempted_go=sum(v['engineering_go'] for v in d['attempts'])));continue
   road=np.asarray(ctx['basis']['road']);label=next(v for v in audit['risk_labels'] if v['id']==o['request']['id']);forward=label['progress_um']/1000000;progress.append(forward);episode_reports.append(dict(id=o['request']['id'],status='captured',forward_m=forward))
   for s in sources.values():source_fees.append(s['source_fee_us']);wire.append(s['wire_bytes']);rx_fees.append(s.get('receiver_fee_us',0))
   for row in rows[:R.DRIVE]:
    raweligible+=bool(row['gate']['geometry_eligible'] and row['odom_ok']);go+=bool(row['engineering_go']);query_fees.append(row['query_fee_us']);p=row['proposal']
    if p is None:missing+=1;continue
    s=sources[row['cache_source_step']];q=R.query_position(row['own'],ctx['basis']);r=R.action_radius(d['body']);truth=(np.asarray(s['truth']['center'])-ctx['basis']['anchor'])@road;pt=[F.from_float(float(v))*1000000 for v in truth[:2]];n=sum((pt[k]-q[k])**2 for k in (0,1));distance=math.isqrt(n.numerator//n.denominator);oracle=R.horizon(distance,R.pose.parameters(ctx['catalog'][s['meta']['original']['blueprint']])['body_um'],r);gap=oracle-p['lower_us'];remaining=p['proposal_valid_until_us']-row['decision_us']-R.ACTION;loss.append(gap);slack.append(remaining);over+=gap<0
    cases.append(dict(episode_id=o['request']['id'],method=method,step=row['step'],cache_step=s['step'],source_us=s['source_us'],now_us=row['now_us'],proposal_us=p['lower_us'],oracle_us=oracle,signed_loss_us=gap,remaining_after_query_and_action_us=remaining,raw_geometry_eligible=row['gate']['geometry_eligible'],policy_ok=row['policy_ok'],engineering_go=row['engineering_go']))
  cells.append(dict(method=method,useful_episodes=sum(v['useful'] for v in audit['risk_labels'] if v['method']==method),selected_episodes=sum(v['selected'] for v in audit['risk_labels'] if v['method']==method),failed_selected_episodes=sum(v['failed'] for v in audit['risk_labels'] if v['method']==method),planned=24,captured=len(progress),certificate_accepted=policy['methods'][method]['accepted'],completed_episode_forward_m=stats(progress),planned_drive_queries=24*R.DRIVE,recorded_drive_queries=len(query_fees),missing_cached_proposal=missing,raw_geometry_eligible_drive_queries=raweligible,experimental_go_drive_queries=go,source_oracle_signed_gap_us=stats(loss),remaining_after_query_and_action_us=stats(slack),source_age_overstatements=over,actual_source_fee_us=stats(source_fees),actual_receiver_fee_us=stats(rx_fees),actual_query_fee_us=stats(query_fees),actual_wire_bytes_total=sum(wire),actual_wire_bytes_per_packet=stats(wire),episodes=episode_reports))
 result=dict(cells=cells,cases=cases,policy_sha256=sha(P/'policy_frozen.json'),test_audit_sha256=sha(P/'audit_test_sheng.json'),test_outcomes_sha256=sha(P/'test_capture/outcomes.json'),freeze_sha256=sha(E/'freeze.json'),scope='All72 planned held-out episodes; reported progress uses exact projected progress floored to micrometres. Related queries not independent. Means/gaps use explicitly reported completed/available cases; no failures removed from planned denominators. Independent scene draws, not matched pairs; no per-class/road/radio/WCET guarantee.',goal_complete=False)
 a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='cases'},sort_keys=True))
if __name__=='__main__':main()
