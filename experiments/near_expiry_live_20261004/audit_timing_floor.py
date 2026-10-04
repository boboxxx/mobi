#!/usr/bin/env python3
"""Post-result zero-source-compute sensitivity; never rewrite actual driving."""
import argparse,bisect,gzip,json
from pathlib import Path
import runtime as R
E=Path(__file__).resolve().parent

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists()
 outcomes=json.loads((a.capture/'outcomes.json').read_bytes());reports=[];same=different=unresolved=0
 for o in outcomes:
  if o['status']!='captured':reports.append(dict(id=o['request']['id'],status=o['status']));continue
  p=a.capture/o['file'];assert R.sha(p)==o['sha256'];d=json.loads(gzip.decompress(p.read_bytes()));free=0;equal=changed=unknown=0;times=[v['now_us'] for v in d['rows']]
  for s in d['sources']:
   arrival,free=R.source_link(s['source_us'],s['acquisition_us'],0,s['wire_bytes'],o['request']['propagation_us'],free)
   assert arrival<=s['arrival_us']
   if s['dropped']:continue
   k=bisect.bisect_left(times,arrival)
   if k==len(times):unknown+=1;continue
   if s.get('ready_us') is None:unknown+=1;continue
   if times[k]==s['decode_at_us']:equal+=1
   else:changed+=1
  reports.append(dict(id=o['request']['id'],status='captured',same_first_decode_tick=equal,different_first_decode_tick=changed,unresolved=unknown));same+=equal;different+=changed;unresolved+=unknown
 result=dict(post_result_sensitivity=True,source_compute_fee_set_to_zero=True,actual_driving_rewritten=False,zero_compute_is_not_measured_runtime=True,same_first_decode_tick=same,different_first_decode_tick=different,unresolved=unresolved,episodes=reports,outcomes_sha256=R.sha(a.capture/'outcomes.json'),scope='Coarse50ms recorded cadence only; does not certify an optimized implementation or WCET.')
 a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='episodes'},sort_keys=True))
if __name__=='__main__':main()
