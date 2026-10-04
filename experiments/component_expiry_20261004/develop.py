#!/usr/bin/env python3
"""Finite two-component post-test development; no new certification."""
import hashlib,json
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
from method import ROOT,FAMILIES,COMPONENTS,conformity,infer
from scores import load_models,predictions
E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name;OLD=ROOT/'results/prospective_hypotheses_20261004'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,d):p.write_text(json.dumps(d,separators=(',',':'))+'\n')
def pair(v):return [v.numerator,v.denominator]
def quantile(v):
 v=sorted(v);pos=F((len(v)-1)*95,100);j=pos.numerator//pos.denominator
 return float(v[j]+(v[min(j+1,len(v)-1)]-v[j])*(pos-j))
def main():
 frozen=read(E/'freeze.json')
 for section in ('sources','inputs'):
  for n,h in frozen[section].items():assert sha(ROOT/n)==h,n
 assert not (P/'development_sheng.json').exists()
 data=read(OLD/'qualification_sheng.json');models=load_models();events=defaultdict(lambda:F(0));rows=[]
 for i,r in enumerate(data['rows']):
  pred,centre=predictions(r['hulls_cm'],r['layout'],r['blueprint'],models);assert pred==r['prediction'] and centre==r['ridge_center_um']
  ss=conformity(r['hulls_cm'],data['catalog'][r['blueprint']],pred,r['true_xy'])
  rows.append(dict(id=r['id'],episode_id=r['episode_id'],blueprint=r['blueprint'],split=r['split'],scores={m:pair(s) for m,s in ss.items()}))
  for m,s in ss.items():events[r['episode_id'],m]=max(events[r['episode_id'],m],s)
  if (i+1)%500==0:print('development scored',i+1,flush=True)
 registry={}
 for bp in data['catalog']:
  eps=[e['episode'] for e in data['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='calibration'];assert len(eps)==125
  registry[bp]={m:pair(max(events[e['id'],m] for e in eps)) for m in COMPONENTS}
 source={r['id']:r for r in data['rows']}
 for row in rows:
  if row['split']!='test':continue
  r=source[row['id']];bp=r['blueprint'];row['methods']={}
  for m in FAMILIES:
   thresholds=dict(supported=F(*registry[bp]['supported_'+m[len('component_'):]]),fallback_um=int(F(*registry[bp]['fallback_um'])))
   row['methods'][m]=infer(r['hulls_cm'],data['catalog'][bp],r['prediction'],thresholds,m)
 summary=[]
 for bp in data['catalog']:
  eps=[e['episode'] for e in data['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='test'];rr=[r for r in rows if r['split']=='test' and r['blueprint']==bp]
  for m in FAMILIES:
   mode=m[len('component_'):];qs=F(*registry[bp]['supported_'+mode]);qf=F(*registry[bp]['fallback_um']);gaps=[];over=[];above=below=0
   for row in rr:
    original=source[row['id']];v=row['methods'][m];ages=v['lower_us'] if v['status']=='bounded' else [0,0];reference=original['geometries']['local_'+mode];old_ages=reference['lower_us'] if reference['status']=='bounded' else [0,0]
    for j,(age,oracle,old) in enumerate(zip(ages,original['oracle_us'],old_ages)):
     gaps.append(max(0,oracle-age));above+=age>old;below+=age<old
     if age>oracle:over.append([row['id'],j,age,oracle])
   excluded=[e['id'] for e in eps if events[e['id'],'supported_'+mode]>qs or events[e['id'],'fallback_um']>qf]
   summary.append(dict(blueprint=bp,family=m,supported_threshold=pair(qs),fallback_um=int(qf),planned_test_episodes=60,captured_test_episodes=len(rr)//6,excluded_episodes=excluded,age_overstatements=over,source_queries=len(gaps),oracle_gap_us_p95=quantile(gaps),above_old=above,below_old=below))
 write(P/'development_sheng.json',dict(rows=rows,registry=registry,summary=summary,freeze_sha256=sha(E/'freeze.json'),parent_sha256=sha(OLD/'qualification_sheng.json'),fresh_qualification=False,scope='Two-component candidate designed after reading prior test results. Entire corpus is development; no independent risk certification, timing or novelty claim. Fixed predictor replay shared.'))
 print('FINITE_COMPONENT_DEVELOPMENT_COMPLETE',len(rows),flush=True)
if __name__=='__main__':main()
