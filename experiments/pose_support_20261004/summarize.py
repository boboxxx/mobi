#!/usr/bin/env python3
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
import numpy as np
POLICIES=('sphere_hull','pose_hull','joint_hull','joint_raw')
def stats(x):
 a=np.asarray(x);return dict(n=len(x),minimum=float(a.min()),median=float(np.median(a)),p95=float(np.percentile(a,95)),maximum=float(a.max())) if len(x) else dict(n=0)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results;d=json.loads((p/'analysis_sheng.json').read_bytes());au=json.loads((p/'audit_sheng.json').read_bytes());classes=[];checks=au['frame_checks'];test=[r for r in d['rows'] if r['split']=='test']
 for bp in d['context']['catalog']:
  rr=[r for r in test if r['blueprint']==bp];cc=[r for r in checks if r['blueprint']==bp and r['split']=='test'];allc=[r for r in checks if r['blueprint']==bp];record=dict(blueprint=bp,registry=d['registry'][bp],test_frames=len(rr),pose_statuses=dict(Counter(r['pose_geometry']['status'] for r in rr)),joint_excluded_episodes=len({r['episode_id'] for r in cc if not r['joint_covered']}),tilt_violated_frames=sum(r['tilt_prior_violated'] for r in allc),observed_tilt_operator_norm=stats([r['tilt_operator_norm'] for r in allc]),feasible_yaw_cells=stats([r['pose_geometry']['feasible_cells'] for r in rr]),pose_distance_bracket_um=stats([v for r in cc for v in r['pose_bracket_um']]),pose_age_bracket_us=stats([v for r in cc for v in r['pose_bracket_us']]),source_queries_with_joint_gain_us_gt1=sum(a>b+1 for r in cc for a,b in zip(r['joint_us'],r['sphere_us'])),source_joint_gain_us=stats([a-b for r in cc for a,b in zip(r['joint_us'],r['sphere_us'])]),methods={})
  for policy in POLICIES:
   mm=[r['methods'][policy] for r in rr];tt=[t for t in d['traces'] if t['method']==policy and t['blueprint']==bp];field={'sphere_hull':'sphere_us','pose_hull':'pose_us','joint_hull':'joint_us','joint_raw':'joint_us'}[policy];record['methods'][policy]=dict(wire_bytes=stats([r['wire_bytes'] for r in mm]),source_us=stats([r['source_us'] for r in mm]),receiver_us=stats([r['receiver_us'] for r in mm]),oracle_age_gap_us=stats([max(0,oracle[0]-t) for r in cc for t,oracle in zip(r[field],r['oracle_us'])]),policies=[dict(rate=rate,startup=startup,grants=sum(t['grants'] for t in tt if t['rate']==rate and t['startup']==startup),scheduled_queries=sum(t['scheduled_queries'] for t in tt if t['rate']==rate and t['startup']==startup)) for rate in (20000000,2000000) for startup in ('warm','cold')])
  classes.append(record)
 policies=[]
 for rate in (20000000,2000000):
  for startup in ('warm','cold'):
   record=dict(rate=rate,startup=startup,grants={},scheduled_queries=11520,pairwise={});mapping={}
   for method in POLICIES:
    tt=[t for t in d['traces'] if t['method']==method and t['rate']==rate and t['startup']==startup];mapping[method]={t['episode_id']:t for t in tt};record['grants'][method]=sum(t['grants'] for t in tt)
   for base in ('sphere_hull','pose_hull','joint_raw'):
    gain=loss=same=0
    for ep,t in mapping['joint_hull'].items():
     for x,y in zip(t['decisions'],mapping[base][ep]['decisions']):gain+=x['grant'] and not y['grant'];loss+=y['grant'] and not x['grant'];same+=x['grant']==y['grant']
    record['pairwise'][base]=dict(joint_only=int(gain),baseline_only=int(loss),same=int(same))
   policies.append(record)
 out=dict(classes=classes,policies=policies,setup=d['setup'],audit_counts={k:v for k,v in au.items() if k not in ('frame_checks','scope','analysis_sha256','source_sha256')},source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),analysis_sha256=hashlib.sha256((p/'analysis_sheng.json').read_bytes()).hexdigest(),audit_sha256=hashlib.sha256((p/'audit_sheng.json').read_bytes()).hexdigest(),scope=d['scope']);a.out.write_text(json.dumps(out,separators=(',',':'))+'\n');print(json.dumps(policies,indent=2),flush=True)
if __name__=='__main__':main()
