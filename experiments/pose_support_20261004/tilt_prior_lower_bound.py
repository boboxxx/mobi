#!/usr/bin/env python3
"""Exact necessary-condition witnesses against ANY pure-yaw prior."""
import argparse,hashlib,json,math
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results.resolve();pp=ROOT/'results/prospective_expiry_20261003/analysis_sheng.json';d=read(pp);audit=read(p/'audit_sheng.json');road=d['contract_body']['basis']['road'];rows={v['id']:v for v in d['rows']};snapshot={(e['episode']['id'],v['frame']):v['actor_transform']['matrix'] for e in d['episodes'] for v in e.get('trajectory',[])};witnesses=[]
 for c in audit['frame_checks']:
  if not c['tilt_prior_violated']:continue
  r=rows[c['id']];R=snapshot[(r['episode_id'],r['frame'])];v=[sum(F.from_float(float(road[j][i]))*F.from_float(float(R[j][2])) for j in range(3))-(1 if i==2 else 0) for i in range(3)];n=sum(x*x for x in v);scaled=n*10**24;lo=math.isqrt(scaled.numerator//scaled.denominator);assert lo*lo*scaled.denominator<=scaled.numerator<(lo+1)**2*scaled.denominator and lo*1000000>87267*10**12
  witnesses.append(dict(id=r['id'],episode_id=r['episode_id'],blueprint=r['blueprint'],split=r['split'],column_difference=[[x.numerator,x.denominator] for x in v],squared_norm=[n.numerator,n.denominator],norm_lower_num=lo,norm_lower_den=10**12))
 out=dict(witnesses=witnesses,count=len(witnesses),minimum_lower_bound=min(v['norm_lower_num'] for v in witnesses)/1e12,registered_prior=[87267,1000000],source_sha256=sha(Path(__file__)),input_hashes={str(pp.relative_to(ROOT)):sha(pp),str((p/'audit_sheng.json').relative_to(ROOT)):sha(p/'audit_sheng.json')},scope='For EVERY pure yaw U, U*e3=e3, so ||R-U||op >= ||R*e3-e3||. Exact binary-rational registered-road/actor-matrix witnesses prove all archived flags exceed the prior, independent of the chosen yaw or SVD. This is an offline diagnostic, not a truth-based runtime gate.');a.out.write_text(json.dumps(out,separators=(',',':'))+'\n')
if __name__=='__main__':main()
