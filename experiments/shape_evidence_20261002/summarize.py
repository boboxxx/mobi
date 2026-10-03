#!/usr/bin/env python3
"""Derive report totals from archived outputs, never hand-entered results."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.stats import beta
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();p=a.results;main=json.loads((p/'analysis_sheng.json').read_bytes());follow=json.loads((p/'availability_followup/analysis_sheng.json').read_bytes());vehicles={k:v for k,v in main['summary'].items() if k.startswith('vehicle.')};totals={}
    for method in ('solid_box','full_only','joint'):
        n=sum(x[method]['test_episodes'] for x in vehicles.values());k=sum(x[method]['false_exclusion_episodes'] for x in vehicles.values());u=sum(x[method]['translated_rejections'] for x in vehicles.values());den=sum(x[method]['translated_total'] for x in vehicles.values());totals[method]=dict(false_exclusions=k,episodes=n,translated_rejected=u,translated_total=den,translated_rejection_fraction=u/den)
    pedestrian={}
    for method,stats in follow['summary']['walker.pedestrian.0001'].items():
        k=stats['false_exclusion_episodes'];n=stats['test_episodes'];available=stats['available_episodes'];pedestrian[method]=dict(false_exclusions=k,scheduled=n,available=available,refused=n-available,unconditional_one_sided_95_upper=1. if k==n else float(beta.ppf(.95,k+1,n-k)),conditional_available_one_sided_95_upper=1. if k==available else float(beta.ppf(.95,k+1,available-k)),translated_rejected=stats['translated_rejections'],translated_total=stats['translated_total'],translated_rejection_fraction=stats['translated_rejections']/stats['translated_total'])
    audits=[json.loads((d/'audit_sheng.json').read_bytes()) for d in (p,p/'availability_followup')];timings={}
    for name,d in [('initial',p),('availability_followup',p/'availability_followup')]:
        t=json.loads((d/'timings_sheng.json').read_bytes());timings[name]={str(s):dict(median_ms=float(np.median([x['truth_score_ns']/1e6 for x in t if x['stride']==s])),p95_ms=float(np.percentile([x['truth_score_ns']/1e6 for x in t if x['stride']==s],95))) for s in (1,4,16)}
    result=dict(total_new_frames=sum(x['frames'] for x in audits),total_raw_rays=sum(x['raw_rays'] for x in audits),independent_box_checks=sum(x['independent_box_checks'] for x in audits),vehicles_initial=totals,pedestrian_followup=pedestrian,score_only_cpu=timings,analysis_sha256=[hashlib.sha256((d/'analysis_sheng.json').read_bytes()).hexdigest() for d in (p,p/'availability_followup')],scope='Descriptive stratified totals; no pooled binomial guarantee. Pedestrian follow-up is a separate fresh experiment after inspecting initial results. CPU excludes transforms, hypothesis construction, acquisition, links and control.')
    (p/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
