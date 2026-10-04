#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.stats import beta
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def stats(x):
 a=np.asarray(x);return dict(n=len(x),minimum=float(a.min()),median=float(np.median(a)),p95=float(np.percentile(a,95)),maximum=float(a.max())) if len(x) else dict(n=0)
def upper(k,n,alpha):return 1. if k==n else float(beta.ppf(1-alpha,k+1,n-k))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results.resolve();d=read(p/'analysis_sheng.json');au=read(p/'audit_sheng.json');checks=au['frame_checks'];test=[r for r in d['rows'] if r['split']=='test'];methods=('sphere_hull','pose_hull','joint_hull','joint_raw');classes=[]
 for bp in d['context']['catalog']:
  rr=[r for r in test if r['blueprint']==bp];cc=[r for r in checks if r['blueprint']==bp and r['split']=='test'];tt=[t for t in d['traces'] if t['blueprint']==bp];ee=[e for e in d['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='test'];k=len({r['episode_id'] for r in cc if not r['joint_covered']});bad={r['episode_id'] for r in cc if not r['joint_covered']};record=dict(blueprint=bp,registry=d['registry'][bp],scheduled_test_episodes=len(ee),captured_test_episodes=sum(e['status']=='captured' for e in ee),test_frames=len(rr),available_test_frames=sum(r['available'] for r in rr),joint_excluded_episodes=k,single_class_risk_upper95=upper(k,60,.05),simultaneous_six_class_risk_upper95=upper(k,60,.05/6),pose_statuses=dict(Counter(r['pose_geometry']['status'] for r in rr)),test_tilt_violated_frames=sum(r['tilt_prior_violated'] for r in cc),all_tilt_violated_frames=sum(r['tilt_prior_violated'] for r in checks if r['blueprint']==bp),pose_distance_bracket_um=stats([v for r in cc for v in r['pose_bracket_um']]),pose_age_bracket_us=stats([v for r in cc for v in r['pose_bracket_us']]),source_queries_with_joint_gain_gt1us=sum(x>y+1 for r in cc for x,y in zip(r['joint_us'],r['sphere_us'])),methods={})
  for method in methods:
   mm=[r['methods'][method] for r in rr];field={'sphere_hull':'sphere_us','pose_hull':'pose_us','joint_hull':'joint_us','joint_raw':'joint_us'}[method];record['methods'][method]=dict(wire_bytes=stats([v['wire_bytes'] for v in mm]),source_us=stats([v['source_us'] for v in mm]),receiver_us=stats([v['receiver_us'] for v in mm]),oracle_age_gap_us=stats([max(0,o[0]-t) for r in cc for o,t in zip(r['oracle_us'],r[field])]),policies=[dict(rate=rate,startup=startup,grants=sum(t['grants'] for t in tt if t['method']==method and t['rate']==rate and t['startup']==startup),grants_from_center_excluded_episodes=sum(v['grant'] for t in tt if t['method']==method and t['rate']==rate and t['startup']==startup and t['episode_id'] in bad for v in t['decisions']),scheduled_queries=1920) for rate in (20000000,2000000) for startup in ('warm','cold')])
  classes.append(record)
 policies=[]
 for rate in (20000000,2000000):
  for startup in ('warm','cold'):
   record=dict(rate=rate,startup=startup,grants={},scheduled_queries=11520,pairwise={});mapping={}
   for method in methods:
    tt=[t for t in d['traces'] if t['method']==method and t['rate']==rate and t['startup']==startup];mapping[method]={t['episode_id']:t for t in tt};record['grants'][method]=sum(t['grants'] for t in tt)
   for baseline in ('sphere_hull','pose_hull','joint_raw'):
    gain=loss=0
    for ep,t in mapping['joint_hull'].items():
     for x,y in zip(t['decisions'],mapping[baseline][ep]['decisions']):gain+=x['grant'] and not y['grant'];loss+=y['grant'] and not x['grant']
    record['pairwise'][baseline]=dict(joint_only=int(gain),baseline_only=int(loss))
   policies.append(record)
 out=dict(classes=classes,policies=policies,setup=d['setup'],joint_calibration_confidence_lower=d['joint_calibration_confidence_lower'],capture=read(p/'capture/manifest.json'),audit_counts={k:v for k,v in au.items() if k not in ('frame_checks','source_sha256','analysis_sha256','scope')},source_sha256=sha(Path(__file__)),analysis_sha256=sha(p/'analysis_sheng.json'),audit_sha256=sha(p/'audit_sheng.json'),scope=d['scope']);a.out.write_text(json.dumps(out,separators=(',',':'))+'\n');print(json.dumps(policies,indent=2),flush=True)
if __name__=='__main__':main()
