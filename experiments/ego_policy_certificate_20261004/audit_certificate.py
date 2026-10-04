#!/usr/bin/env python3
"""Independent rational binomial recurrence; compare every whole-episode label."""
import argparse,hashlib,json,math
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name

def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def binomial_tail(k,n,p):
 assert 0<p<1 and 0<=k<=n
 term=(1-p)**n;total=term
 for j in range(k):term=term*F(n-j,j+1)*p/(1-p);total+=term
 return total

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists()
 f=read(E/'freeze.json')
 for sec in ('sources','inputs'):
  for n,h in f[sec].items():assert sha(ROOT/n)==h,n
 policy=read(P/'policy_frozen.json');audit=read(P/'audit_certification_sheng.json');assert policy['freeze_sha256']==sha(E/'freeze.json') and policy['audit_sha256']==sha(P/'audit_certification_sheng.json') and policy['test_capture_absent_when_frozen'] and not policy['production_road_authorized'] and policy['binary_tests']==3
 eps=F(1,20);delta=F(1,60);nzero=next(n for n in range(1000) if (1-eps)**n<=delta);assert nzero==policy['zero_failure_accepted_required']==80
 cells=[]
 for method,c in policy['methods'].items():
  labels=[v for v in audit['risk_labels'] if v['method']==method];assert len(labels)==180 and all(type(v['selected']) is bool and type(v['failed']) is bool and (not v['failed'] or v['selected']) for v in labels)
  n=sum(v['selected'] for v in labels);k=sum(v['failed'] for v in labels);p=binomial_tail(k,n,eps) if n else F(1);assert [p.numerator,p.denominator]==c['p_value'] and n==c['authorized_episodes'] and k==c['failed_authorized_episodes'];accepted=bool(n and p<=delta);assert accepted==c['accepted'];bound=F(*c['conditional_upper'])
  if not n or k==n:assert bound==1
  else:
   assert binomial_tail(k,n,bound)<=delta
   if bound!=eps:assert binomial_tail(k,n,bound-F(1,2**64))>delta
  cells.append(dict(method=method,planned=180,accepted_episodes=n,failed_accepted=k,conditional_upper=[bound.numerator,bound.denominator],accepted=accepted))
 result=dict(cells=cells,policy_sha256=sha(P/'policy_frozen.json'),audit_sha256=sha(P/'audit_certification_sheng.json'),freeze_sha256=sha(E/'freeze.json'),joint_confidence_lower=[19,20],test_capture_absent_when_frozen=True,scope='Exact label/CDF/CI implementation verification. Joint IID and declared body/motion/service assumptions are not verified by this check.',road_or_radio_qualified=False,goal_complete=False)
 a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
