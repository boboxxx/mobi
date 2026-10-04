#!/usr/bin/env python3
"""Post-run scope check for actual membership failures, without threshold repair."""
import argparse,hashlib,json
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results.resolve();d=read(p/'analysis_sheng.json');au=read(p/'audit_sheng.json');assert au['analysis_sha256']==sha(p/'analysis_sheng.json');checks={r['id']:r for r in au['frame_checks']};bad={r['id'] for r in au['frame_checks'] if r['split']=='test' and not r['joint_covered']};episodes={r['episode_id'] for r in au['frame_checks'] if r['id'] in bad};failures=[]
 for r in d['rows']:
  if r['id'] not in bad:continue
  c=checks[r['id']];v={k:r[k] for k in ('id','episode_id','blueprint','joint_score_um','body_score_um','pose_score_um','true_xy','available')};v.update(joint_lower_us=c['joint_us'],same_body_oracle_bracket_us=c['oracle_us'],vertical_tilt_lower_bound=c['vertical_tilt_lower_bound'],tilt_prior_violated=c['tilt_prior_violated']);failures.append(v)
 grants=[]
 for method in ('sphere_hull','pose_hull','joint_hull','joint_raw'):
  for rate in (20000000,2000000):
   for startup in ('warm','cold'):
    tt=[t for t in d['traces'] if (t['method'],t['rate'],t['startup'])==(method,rate,startup)];grants.append(dict(method=method,rate=rate,startup=startup,grants_referencing_excluded_source=sum(v['grant'] and v['fact_id'] in bad for t in tt for v in t['decisions']),grants_in_excluded_episode=sum(v['grant'] for t in tt if t['episode_id'] in episodes for v in t['decisions'])))
 over={}
 for method,field in [('sphere_hull','sphere_us'),('pose_hull','pose_us'),('joint_hull','joint_us')]:
  excess=[dict(id=r['id'],query=i,excess_us=max(0,v-o[1])) for r in au['frame_checks'] if r['split']=='test' for i,(v,o) in enumerate(zip(r[field],r['oracle_us'])) if v>o[1]];over[method]=dict(source_queries_with_positive_overstatement=len(excess),maximum_us=max((v['excess_us'] for v in excess),default=0),details=excess)
 out=dict(failures=failures,grants=grants,source_age_overstatement=over,source_sha256=sha(Path(__file__)),analysis_sha256=sha(p/'analysis_sheng.json'),audit_sha256=sha(p/'audit_sheng.json'),scope='Descriptive audit of failed current-center sources and same-body/motion oracle; no threshold update, zero-risk proof, conditional-grant guarantee or continuous physical validation.');a.out.write_text(json.dumps(out,separators=(',',':'))+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
