#!/usr/bin/env python3
"""Post-result endpoint clarification; no changed labels or certification."""
import gzip,hashlib,json
from fractions import Fraction as F
from pathlib import Path
R=Path(__file__).resolve().parents[2];Q=Path(__file__).resolve().parent;P=R/'results/useful_expiry_certificate_20261004';cases=[];inputs={}
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for split in ('certification','test'):
 capture=P/(split+'_capture');outcomes=read(capture/'outcomes.json');audit=read(P/('audit_'+split+'_sheng.json'));labels={x['id']:x for x in audit['risk_labels']};ctx=read(capture/'context.json')
 for p in (capture/'outcomes.json',capture/'context.json',P/('audit_'+split+'_sheng.json')):inputs[str(p.relative_to(R))]=sha(p)
 for o in outcomes:
  path=capture/o['file'];assert sha(path)==o['sha256'];d=json.loads(gzip.decompress(path.read_bytes()));rows=d['rows'];assert o['status']=='captured' and len(rows)==100
  def progress(index):
   value=sum((F.from_float(float(rows[index]['after']['center'][j]))-F.from_float(float(rows[0]['own']['center'][j])))*F.from_float(float(ctx['basis']['road'][j][0])) for j in range(3))*1000000
   return value.numerator//value.denominator
  p3,p5=progress(59),progress(99);v=labels[o['request']['id']];assert p5==v['progress_um'] and (p5>=50000)==v['useful']
  cases.append(dict(id=o['request']['id'],split=split,method=o['request']['method'],after_60_steps_um=p3,after_100_steps_um=p5,useful_at_drive_end=p3>=50000,frozen_useful_at_episode_end=p5>=50000))
cells=[]
for split in ('certification','test'):
 for method in ('function','deadline','cone'):
  rows=[c for c in cases if c['split']==split and c['method']==method];cells.append(dict(split=split,method=method,planned=len(rows),useful_after_60_steps=sum(c['useful_at_drive_end'] for c in rows),frozen_useful_after_100_steps=sum(c['frozen_useful_at_episode_end'] for c in rows),different_observed_labels=sum(c['useful_at_drive_end']!=c['frozen_useful_at_episode_end'] for c in rows)))
result=dict(input_sha256=inputs,cells=cells,cases=cases,drive_steps=60,brake_steps=40,control_step_us=50000,frozen_progress_endpoint_step=100,scope='Descriptive endpoint check after results. Published certificate concerns full 5s episode progress, not a new 3s population guarantee. No label, policy or count changed.')
out=Q/'episode_endpoint_check.json';assert not out.exists();out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(cells,sort_keys=True))
