#!/usr/bin/env python3
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
import numpy as np
E=Path(__file__).resolve().parent

def stats(x):
 a=np.asarray(x);return dict(n=len(x),minimum=float(a.min()),median=float(np.median(a)),p95=float(np.percentile(a,95)),maximum=float(a.max())) if len(x) else dict(n=0)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();d=json.loads((a.results/'analysis_sheng.json').read_bytes());au=json.loads((a.results/'audit_sheng.json').read_bytes());rows=d['rows'];checks=au['frame_checks'];summary=[]
 for bp in d['context']['catalog']:
  rr=[r for r in rows if r['blueprint']==bp];cc=[r for r in checks if r['blueprint']==bp];bounded=[r for r in rr if r['geometry']['status']=='bounded'];sample=dict(blueprint=bp,frames=len(rr),statuses=dict(Counter(r['geometry']['status'] for r in rr)),excluded_episodes=len({r['episode_id'] for r in cc if not r['covered']}),source_horizon_us=stats([q['lower_us'] for r in bounded for q in r['geometry']['queries']]),expiry_gap_to_truth_oracle_us=stats([max(0,o[0]-t[1]) for r in cc for o,t in zip(r['oracle_us'],r['expiry_us'])]),uncapped_distance_gap_to_truth_oracle_um=stats([v for r in cc for v in r['distance_gap_um']]),geometry_bracket_um=stats([q['upper_um']-q['lower_um'] for r in bounded for q in r['geometry']['queries']]),expiry_bracket_us=stats([q['upper_us']-q['lower_us'] for r in bounded for q in r['geometry']['queries']]),methods={})
  for method in ('active','hull','points','raw'):
   mm=[r['methods'][method] for r in rr];tt=[t for t in d['traces'] if t['blueprint']==bp and t['method']==method];sample['methods'][method]=dict(wire_bytes=stats([m['wire_bytes'] for m in mm]),source_us=stats([m['source_us'] for m in mm]),receiver_us=stats([m['receiver_us'] for m in mm]),policies=[dict(rate=rate,startup=startup,grants=sum(t['grants'] for t in tt if t['rate']==rate and t['startup']==startup),scheduled_queries=sum(t['scheduled_queries'] for t in tt if t['rate']==rate and t['startup']==startup)) for rate in (20000000,2000000) for startup in ('warm','cold')])
  summary.append(sample)
 policies=[]
 for rate in (20000000,2000000):
  for startup in ('warm','cold'):
   record=dict(rate=rate,startup=startup,grants={},scheduled_queries=11520,pairwise={});method_traces={}
   for method in ('active','hull','points','raw'):
    tt=[t for t in d['traces'] if t['method']==method and t['rate']==rate and t['startup']==startup];record['grants'][method]=sum(t['grants'] for t in tt);method_traces[method]={t['episode_id']:t for t in tt}
   for base in ('hull','points','raw'):
    gain=loss=same=0
    for ep,t in method_traces['active'].items():
     for x,y in zip(t['decisions'],method_traces[base][ep]['decisions']):
      gain+=x['grant'] and not y['grant'];loss+=y['grant'] and not x['grant'];same+=x['grant']==y['grant']
    record['pairwise'][base]=dict(active_only=int(gain),baseline_only=int(loss),same=int(same))
   policies.append(record)
 out=dict(classes=summary,policies=policies,setup=d['setup'],frames=len(rows),statuses=dict(Counter(r['geometry']['status'] for r in rows)),excluded_episodes=len({r['episode_id'] for r in checks if not r['covered']}),bracket_distance_um=stats([q['upper_um']-q['lower_um'] for r in rows if r['geometry']['status']=='bounded' for q in r['geometry']['queries']]),bracket_age_us=stats([q['upper_us']-q['lower_us'] for r in rows if r['geometry']['status']=='bounded' for q in r['geometry']['queries']]),audit_counts={k:v for k,v in au.items() if k not in ('frame_checks','source_sha256','analysis_sha256','scope')},source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),analysis_sha256=hashlib.sha256((a.results/'analysis_sheng.json').read_bytes()).hexdigest(),audit_sha256=hashlib.sha256((a.results/'audit_sheng.json').read_bytes()).hexdigest(),scope=d['scope']);a.out.write_text(json.dumps(out,separators=(',',':'))+'\n');print(json.dumps(policies,indent=2),flush=True)
if __name__=='__main__':main()
