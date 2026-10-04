#!/usr/bin/env python3
"""Predeclared same-input TTL loss, not a counterfactual driving trial."""
import argparse,gzip,json,math
from fractions import Fraction as F
from pathlib import Path
import numpy as np
import runtime as R
import audit as A
E=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_bytes())
def stats(v):
 a=np.asarray(v,dtype=float)
 return dict(count=len(v),min=float(a.min()),median=float(np.median(a)),p95=float(np.quantile(a,.95)),max=float(a.max())) if v else dict(count=0)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists()
 for sec in ('sources','inputs'):
  for n,h in read(E/'freeze.json')[sec].items():assert R.sha(R.ROOT/n)==h,n
 ctx=read(a.capture/'context.json');outcomes=read(a.capture/'outcomes.json');assert len(outcomes)==18
 cases=[];summaries=[]
 for o in outcomes:
  p=a.capture/o['file'];assert R.sha(p)==o['sha256'];d=read_gzip(p)
  if o['status']!='captured':summaries.append(dict(id=o['request']['id'],status=o['status']));continue
  local=[]
  for s in d['sources']:
   original=s['meta']['original'];bp=original['blueprint'];ext=ctx['catalog'][bp];hyp=original['hypothesis'];h=original['hulls_cm'];q=R.query_position(s['own'],ctx['basis']);r=R.action_radius(d['body'])
   proposal=R.evidence(original,ctx).query(q,r);A.geometry(original,d['body'],ctx,proposal)
   oldQ=F(*ctx['registry'][bp]['local_mean']);rects=A.G.rectangles(h,ext,A.G.up(oldQ*10000)) if h else []
   oldlower=None
   if rects:
    v=min(A.G.rect_distance(rect,q) for rect in rects);oldlower=math.isqrt(v.numerator//v.denominator)
    if hyp.get('status')=='supported':
     rr=A.G.up(oldQ*hyp['single_scale_um']);other=max(0,math.isqrt(sum((hyp['mean_um'][k]-q[k])**2 for k in (0,1)))-rr);oldlower=max(oldlower,other)
   oldage=R.horizon(oldlower,A.G.radius(ext),r) if oldlower is not None else 0
   truth=(np.asarray(s['truth']['center'])-ctx['basis']['anchor'])@np.asarray(ctx['basis']['road']);xy=[F.from_float(float(v))*1000000 for v in truth[:2]];n=sum((xy[k]-q[k])**2 for k in (0,1));distance=math.isqrt(n.numerator//n.denominator);oracle=R.horizon(distance,A.G.radius(ext),r)
   age=proposal['lower_us'];lower=proposal.get('distance_lower_um');bound=None
   if lower is not None and lower<=distance:
    bound=(distance-lower+4)//5+1
    assert oracle-age<=bound
   row=dict(id=o['request']['id'],step=s['step'],source_us=s['source_us'],blueprint=bp,method=o['request']['method'],start_x_m=o['request']['start_x_m'],supported=hyp.get('status')=='supported',component_status=proposal['status'],component_lower_um=lower,historical_local_lower_um=oldlower,oracle_floor_distance_um=distance,component_us=age,historical_local_us=oldage,oracle_us=oracle,component_signed_loss_us=oracle-age,historical_signed_loss_us=oracle-oldage,component_overstatement=age>oracle,historical_overstatement=oldage>oracle,component_directional_loss_bound_us=bound)
   local.append(row);cases.append(row)
  summaries.append(dict(id=o['request']['id'],status='captured',sources=len(local),component_loss_us=stats([v['component_signed_loss_us'] for v in local]),historical_loss_us=stats([v['historical_signed_loss_us'] for v in local]),component_shorter=sum(v['component_us']<v['historical_local_us'] for v in local),component_longer=sum(v['component_us']>v['historical_local_us'] for v in local),component_cap=sum(v['component_us']==500000 for v in local),component_zero=sum(v['component_us']==0 for v in local),component_overstatements=sum(v['component_overstatement'] for v in local),historical_overstatements=sum(v['historical_overstatement'] for v in local)))
 result=dict(planned=18,captured=sum(v['status']=='captured' for v in summaries),source_queries=len(cases),freeze_sha256=R.sha(E/'freeze.json'),outcomes_sha256=R.sha(a.capture/'outcomes.json'),episodes=summaries,cases=cases,scope='Predeclared same-input source TTL/oracle diagnostic; no old-baseline driving or policy risk qualification.',goal_complete=False)
 a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('episodes','cases')},sort_keys=True))
def read_gzip(p):return json.loads(gzip.decompress(p.read_bytes()))
if __name__=='__main__':main()
