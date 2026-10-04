#!/usr/bin/env python3
"""Independent rational recurrence plus exact stored-progress label verification."""
import argparse,gzip,hashlib,json
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def cdf(k,n,p):
 term=(1-p)**n;total=term
 for j in range(k):term*=F(n-j,j+1)*p/(1-p);total+=term
 return total
def tail(k,n,p):return F(1) if k==0 else 1-cdf(k-1,n,p)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists()
 f=read(E/'freeze.json')
 for sec in ('sources','inputs'):
  for n,h in f[sec].items():assert sha(ROOT/n)==h,n
 c=read(P/'policy_frozen.json');audit=read(P/'audit_certification_sheng.json');assert c['freeze_sha256']==sha(E/'freeze.json') and c['audit_sha256']==sha(P/'audit_certification_sheng.json') and c['test_capture_absent_when_frozen'] and c['binary_tests']==6 and c['zero_failure_accepted_required']==94 and not c['production_road_authorized']
 outcomes=read(P/'certification_capture/outcomes.json');ctx=read(P/'certification_capture/context.json');labels=audit['risk_labels'];assert len(labels)==len(outcomes)==540
 for o,v in zip(outcomes,labels):
  assert o['request']['id']==v['id'];d=json.loads(gzip.decompress((P/'certification_capture'/o['file']).read_bytes()))
  if o['status']!='captured':assert not v['useful'] and v['progress_um'] is None
  else:
   rows=d['rows'];z=sum((F.from_float(float(rows[-1]['after']['center'][j]))-F.from_float(float(rows[0]['own']['center'][j])))*F.from_float(float(ctx['basis']['road'][j][0])) for j in range(3))*1000000;um=z.numerator//z.denominator;assert um==v['progress_um'] and v['useful']==(um>=50000)
 delta=F(1,120);eps=F(1,20);minimum=F(1,4);assert (1-eps)**93>delta>=(1-eps)**94;cells=[]
 for name,x in c['methods'].items():
  rows=[v for v in labels if v['method']==name];assert len(rows)==180
  n=sum(v['selected'] for v in rows);k=sum(v['failed'] for v in rows);pv=cdf(k,n,eps) if n else F(1);assert [pv.numerator,pv.denominator]==x['p_value'] and n==x['authorized_episodes'] and k==x['failed_authorized_episodes'];ok=bool(n and pv<=delta);assert ok==x['risk_accepted'];upper=F(*x['conditional_upper'])
  if not n or k==n:assert upper==1
  else:
   assert cdf(k,n,upper)<=delta
   if upper!=eps:assert cdf(k,n,upper-F(1,2**64))>delta
  u=x['utility'];m=sum(v['useful'] for v in rows);q=tail(m,180,minimum);lower=F(*u['lower']);assert u['planned']==180 and u['useful']==m and u['p_value']==[q.numerator,q.denominator] and u['accepted']==bool(m and q<=delta)
  if not m:assert lower==0
  else:
   assert tail(m,180,lower)<=delta
   if lower!=minimum:assert tail(m,180,lower+F(1,2**64))>delta
  assert x['accepted']==(ok and u['accepted']);cells.append(dict(method=name,selected=n,failed=k,risk_upper=x['conditional_upper'],useful=m,utility_lower=u['lower'],accepted=x['accepted']))
 result=dict(cells=cells,policy_sha256=sha(P/'policy_frozen.json'),audit_sha256=sha(P/'audit_certification_sheng.json'),freeze_sha256=sha(E/'freeze.json'),joint_confidence_lower=[19,20],all_progress_labels_independently_checked=True,scope='Six standard exact tests under declared joint IID; no proof of that assumption or road/radio/continuous risk.',goal_complete=False)
 a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
