#!/usr/bin/env python3
"""Pre-held-out finite same-input representation diagnostic, not physical recosting."""
import argparse,gzip,hashlib,importlib.util,json
from pathlib import Path
import numpy as np
import runtime as R
_summary_spec=importlib.util.spec_from_file_location('matched_fixed_local_summary',Path(__file__).resolve().parent/'summarize.py');_summary_module=importlib.util.module_from_spec(_summary_spec);_summary_spec.loader.exec_module(_summary_module);stats=_summary_module.stats
ROOT=Path(__file__).resolve().parents[2];E=Path(__file__).resolve().parent;P=ROOT/'results'/E.name
spec=importlib.util.spec_from_file_location('matched_fixed_episode_geometry',E/'audit.py');A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--capture',type=Path);args=ap.parse_args();assert not args.out.exists()
 freeze=read(E/'matched_freeze.json')
 for sec in ('sources','inputs'):
  for n,h in freeze[sec].items():assert sha(ROOT/n)==h,n
 capture=args.capture or P/'test_capture';outcomes=read(capture/'outcomes.json');ctx=read(capture/'context.json');assert len(outcomes)==72 and read(P/'audit_test_sheng.json')['outcomes_sha256']==sha(capture/'outcomes.json')
 models=R.load_models();background=read(ROOT/'results/background_frontend_20261004/background.json');methods=('function','deadline','cone');totals={m:0 for m in methods};cases=[];paired_sources=0;missing_queries=0;incomplete=[];source_groups=[]
 for o in outcomes:
  path=capture/o['file'];assert sha(path)==o['sha256'];data=json.loads(gzip.decompress(path.read_bytes()))
  if o['status']!='captured':incomplete.append(dict(id=o['request']['id'],status=o['status']));continue
  caches={};originals={};body=data['body']
  for s in data['sources']:
   rawpath=capture/'clouds'/s['cloud'];assert sha(rawpath)==s['cloud_sha256']
   with np.load(rawpath) as z:raw=z['raw'];T=z['transform'].copy()
   wires={};metas={}
   for m in methods:
    wire,meta=R.encode(raw,T,s['own'],body,ctx,o['request']['blueprint'],m,s['source_us'],s['frame'],models,background);wires[m]=wire;metas[m]=meta;totals[m]+=len(wire)
   assert wires[o['request']['method']]==(capture/'packets'/s['packet']).read_bytes()
   for m in methods:
    assert metas[m]['original']['hulls_cm']==metas['function']['original']['hulls_cm'] and metas[m]['original']['hypothesis']==metas['function']['original']['hypothesis'] and metas[m]['kept_xyz_sha256']==metas['function']['kept_xyz_sha256']
   original=metas['function']['original'];originals[s['step']]=original;caches[s['step']]={m:R.decode(wires[m],ctx) for m in methods}
   for m in ('deadline','cone'):A.geometry(original,body,ctx,metas[m]['source_proposal'])
   source_groups.append(dict(episode=o['request']['id'],source_step=s['step'],actual_method=o['request']['method'],wire_bytes={m:len(wires[m]) for m in methods}));paired_sources+=1
  for row in data['rows'][:R.DRIVE]:
   sid=row['cache_source_step']
   if sid is None:missing_queries+=1;continue
   proposals={};gates={}
   for m in methods:proposals[m],gates[m]=R.choose(caches[sid][m],row['own'],body,ctx,row['now_us'])
   fp=proposals['function'];cp=proposals['cone'];dp=proposals['deadline'];A.geometry(originals[sid],body,ctx,fp)
   assert fp['status']==cp['status'];gap=fp['lower_us']-cp['lower_us']
   # A valid source bound transports by the triangle inequality. A numerically
   # optimized query lower bound need not itself be a Lipschitz function.
   assert all(v['source_us']==originals[sid]['source_us'] for v in proposals.values())
   if cp['status']=='bounded':
    q=cp['query_um'];sp=R.evidence(originals[sid],ctx).query(R.query_position(next(s['own'] for s in data['sources'] if s['step']==sid),ctx['basis']),0);n=sum((q[k]-sp['query_um'][k])**2 for k in (0,1));d=R.math.isqrt(n);d+=d*d<n;lower=max(0,sp['distance_lower_um']-d);assert lower==cp['distance_lower_um'];t=cp['lower_us'];bp=o['request']['blueprint']
    if t:assert A.G.safe(lower,A.G.radius(ctx['catalog'][bp]),cp['query_radius_um'],t)
    if t<500000:assert not A.G.safe(lower,A.G.radius(ctx['catalog'][bp]),cp['query_radius_um'],t+1)
   cases.append(dict(episode=o['request']['id'],actual_method=o['request']['method'],step=row['step'],source_step=sid,function_us=fp['lower_us'],cone_us=cp['lower_us'],deadline_us=dp['lower_us'],function_minus_cone_us=gap,deadline_domain_valid=gates['deadline']['query_domain_valid']))
 result=dict(matched_freeze_sha256=sha(E/'matched_freeze.json'),planned_episodes=72,complete_episodes=72-len(incomplete),incomplete=incomplete,paired_sources=paired_sources,missing_cached_drive_queries=missing_queries,matched_cached_drive_queries=len(cases),actual_method_packets_reproduced=True,wire_bytes=totals,function_minus_cone_us=stats([c['function_minus_cone_us'] for c in cases]),function_cone_identical_age_queries=sum(c['function_us']==c['cone_us'] for c in cases),cone_age_larger_queries=sum(c['function_us']<c['cone_us'] for c in cases),deadline_invalid_domain_queries=sum(not c['deadline_domain_valid'] for c in cases),sources=source_groups,cases=cases,freeze_sha256=sha(E/'freeze.json'),test_outcomes_sha256=sha(capture/'outcomes.json'),test_audit_sha256=sha(P/'audit_test_sheng.json'),scope='All available test sources and cached drive queries, same observed XYZ/odometry/body/models. Offline repeated encoding only; original fees/actions not rewritten, no alternate-selector certificate and no counterfactual or radio/WCET claim.',goal_complete=False)
 args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('cases','sources')},sort_keys=True))
if __name__=='__main__':main()
