#!/usr/bin/env python3
"""Post-result hypothesis audit; no production geometry/threshold changes."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
E=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results;d=read(p/'analysis_sheng.json');au=read(p/'audit_sheng.json');raw=read(p/'raw_optimized_sheng.json');checks={v['id']:v for v in au['frame_checks']};classes=[]
 for bp in d['context']['catalog']:
  c=[v for v in checks.values() if v['blueprint']==bp];record=dict(blueprint=bp,tilt_by_split={},joint_oracle_gap_p95_ms=None)
  for split in ('calibration','test'):
   bad=[v for v in c if v['split']==split and v['tilt_prior_violated']];record['tilt_by_split'][split]=dict(frames=len(bad),episodes=len({v['episode_id'] for v in bad}),ids=[v['id'] for v in bad])
  gap=[max(0,o[0]-t)/1000 for v in c if v['split']=='test' for t,o in zip(v['joint_us'],v['oracle_us'])];record['joint_oracle_gap_p95_ms']=float(np.percentile(gap,95));rr=[v for v in raw['rows'] if v['blueprint']==bp];record['optimized_raw_receiver_p95_us']=float(np.percentile([v['receiver_us'] for v in rr],95));classes.append(record)
 policies=[]
 for rate in (20000000,2000000):
  for startup in ('warm','cold'):
   tt=[t for t in d['traces'] if t['method']=='joint_hull' and t['rate']==rate and t['startup']==startup];gg=[v for t in tt for v in t['decisions'] if v['grant']];bad=[v for v in gg if checks[v['fact_id']]['tilt_prior_violated']];record=dict(rate=rate,startup=startup,joint_grants=len(gg),grants_referencing_tilt_violated_source=len(bad),episodes_referencing_tilt_violated_source=len({checks[v['fact_id']]['episode_id'] for v in bad}),optimized_raw_grants=next(v['grants'] for v in raw['policies'] if v['rate']==rate and v['startup']==startup));policies.append(record)
 out=dict(classes=classes,policies=policies,total_tilt_violated_frames=sum(v['tilt_prior_violated'] for v in checks.values()),source_sha256=sha(Path(__file__)),input_hashes={n:sha(p/n) for n in ['analysis_sheng.json','audit_sheng.json','raw_optimized_sheng.json']},scope='Retrospective diagnostic, no truth-based receiver gate or recalibration. Violated sufficient tilt prior need not imply center exclusion; observed coverage does not validate that prior. Source solver precision is not model correctness.');a.out.write_text(json.dumps(out,separators=(',',':'))+'\n')
if __name__=='__main__':main()
