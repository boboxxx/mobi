#!/usr/bin/env python3
"""Summarize audited joint lifetime brackets; do not manufacture authority."""
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();r=a.results;audits={}
    for label,prefix in [('sphere','audit'),('extension','extension_audit'),('extra','extra_ray_audit')]:
        p=r/(prefix+'_sheng.json');assert p.read_bytes()==(r/(prefix+'_local.json')).read_bytes();audits[label]=json.loads(p.read_bytes())
    base=json.loads((r/'study/analysis.json').read_bytes());groups={};candidates=audits['sphere']['summaries']+audits['extension']['summaries'];rows=[]
    for row in base['rows']:groups.setdefault((row['run'],row['index']),[]).append(row)
    for (run,index),g in groups.items():
        assert {x['klass'] for x in g}=={'small','vehicle'} and len(g)==2;lower=min(x['lower_horizon_us'] for x in g);assert all(x['joint_lower_horizon_us']==lower for x in g)
        choices=[x for x in candidates if (x['run'],x['index'])==(run,index) and x['upper_horizon_us'] is not None];upper=min(x['upper_horizon_us'] for x in choices);assert lower<=upper
        rows.append(dict(run=run,index=index,reference_us=g[0]['ref_us'],lower_us=lower,upper_us=upper,absolute_conservatism_bound_us=upper-lower,relative_conservatism_bound=None if lower==0 else 1-lower/upper,resolved_zero=False if lower==0 else None,maximum_strict_admission_age_us=lower-200000 if lower>200000 else None))
    positive=[x for x in rows if x['lower_us']>0];stats={}
    for study in ['study','ellipsoid_study','heading_study','extra_ray_study']:
        data=json.loads((r/study/'analysis.json').read_bytes());field='selection_ms' if study=='extra_ray_study' else 'search_ms';cost=[x[field] for x in data['rows']];stats[study]=dict(cases=len(cost),milliseconds_min=min(cost),milliseconds_median=float(np.median(cost)),milliseconds_max=max(cost))
    extra=audits['extra']['summaries'];out=dict(joint_queries=len(rows),positive_queries=len(positive),unresolved_zero_queries=len(rows)-len(positive),witnesses=audits['sphere']['witnesses']+audits['extension']['witnesses'],segment_checks=audits['sphere']['independent_segment_checks']+audits['extension']['segment_checks'],maximum_positive_absolute_gap_us=max(x['absolute_conservatism_bound_us'] for x in positive),maximum_positive_relative_gap=max(x['relative_conservatism_bound'] for x in positive),extra_ray_refutations=audits['extra']['refuted'],extra_ray_margin_min_m=min(x['independent_core_exclusion_margin_m'] for x in extra),extra_ray_bytes_range=[min(x['bytes'] for x in extra),max(x['bytes'] for x in extra)],costs=stats,rows=rows,audit_sha256={prefix:sha(r/(prefix+'_sheng.json')) for prefix in ['audit','extension_audit','extra_ray_audit']},scope='Audited source-time continuous stationary rectangle lifetime bounds, conditional on stated core/error/motion/source contracts. Positive gap bounds are relative to original RECEIVED information; unreceived extra facts cannot extend them without recertification. No controller grant/physical confidence/global optimality.')
    (r/'joint_bounds.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['rows','scope','audit_sha256']}))
if __name__=='__main__':main()
