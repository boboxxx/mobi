#!/usr/bin/env python3
"""Pre-outcome analysis rules; no model/threshold/policy changes."""
import bootstrap
import argparse,statistics
from collections import Counter,defaultdict
from fractions import Fraction as F
from fresh_io import ROOT,E,P,read,write,sha
from fresh_inference import PRIMARY

def quantile(values):
    values=sorted(values)
    if not values:return None
    p=F((len(values)-1)*95,100);j=p.numerator//p.denominator
    return float(values[j]+(values[min(j+1,len(values)-1)]-values[j])*(p-j))
def excluded(scores,family,registry):
    if family.startswith('component_'):
        mode=family[len('component_'):]
        return F(*scores['supported_'+mode])>F(*registry['supported_'+mode]) or F(*scores['fallback_um'])>F(*registry['fallback_um'])
    return F(*scores[family])>F(*registry[family])
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=__import__('pathlib').Path,default=P/'summary_sheng.json');a=ap.parse_args();assert not a.out.exists()
    assert (P/'terminal.txt').read_text()=='FINITE_PROSPECTIVE_COMPONENT_EVALUATION_COMPLETE\n'
    f=read(E/'analysis_freeze.json')
    for n,h in f['sources'].items():assert sha(ROOT/n)==h,n
    d=read(P/'qualification_test_sheng.json');paid=read(P/'paid_test_sheng.json');cal=read(P/'calibration_frozen.json');policy=read(P/'policy_frozen.json');audit=read(P/'audit_sheng.json');episodes=read(P/'capture/episodes.json');manifest=read(P/'capture/manifest.json');plan=read(E/'plan.json');registry=d['registry'];rows=d['rows'];byep=defaultdict(list)
    for r in rows:byep[r['episode_id']].append(r)
    capture=[];source=[]
    for bp in d['catalog']:
        for split in ('calibration','certification','test'):
            eps=[e for e in episodes if e['episode']['blueprint']==bp and e['episode']['split']==split];capture.append(dict(blueprint=bp,split=split,planned=len(eps),statuses=dict(Counter(e['status'] for e in eps))))
        rr=[r for r in rows if r['blueprint']==bp];eps=[e['episode'] for e in episodes if e['episode']['split']=='test' and e['episode']['blueprint']==bp]
        for family in PRIMARY:
            gaps=[];over=[];exclusions=[];above=below=0;status=Counter()
            for ep in eps:
                if any(excluded(r['scores'],family,registry[bp]) for r in byep[ep['id']]):exclusions.append(ep['id'])
            for r in rr:
                g=r['geometries'][family];status[g['status']]+=1;ages=g['lower_us'] if g['status']=='bounded' else [0,0]
                ref=r['geometries'][family.replace('component_','local_')];reference=ref['lower_us'] if ref['status']=='bounded' else [0,0]
                for q,(v,o,old) in enumerate(zip(ages,r['oracle_us'],reference)):
                    gaps.append(max(0,o-v))
                    if v>o:over.append([r['id'],q,v,o])
                    above+=v>old;below+=v<old
            source.append(dict(blueprint=bp,family=family,captured_source_frames=len(rr),source_queries=len(gaps),planned_episodes=len(eps),statuses=dict(status),p95_oracle_gap_us=quantile(gaps),mean_oracle_gap_us=statistics.mean(gaps) if gaps else None,excluded_episodes=exclusions,age_overstatements=over,above_matched_local=above,below_matched_local=below,scope='Source gaps only on captured scans; failed episodes remain in service/query denominator.'))
    cells={(c['family']+'_'+c['kind'],c['rate'],c['startup']):c for c in policy['cells']};service=[]
    for method,rate,startup in cells:
        tr=[t for t in paid['traces'] if (t['method'],t['rate'],t['startup'])==(method,rate,startup)];assert len(tr)==360;c=cells[method,rate,startup];grant_excluded=grant_age_failed=0
        lookup={r['id']:r for r in rows};family=c['family']
        for t in tr:
            for decision in t['decisions']:
                if not decision['grant']:continue
                r=lookup[decision['fact_id']];grant_excluded+=excluded(r['scores'],family,registry[r['blueprint']]);grant_age_failed+=decision['now_us']+220000-r['source_us']>r['oracle_us'][decision['query']]
        raw=sum(t['grants'] for t in tr)
        service.append(dict(method=method,rate=rate,startup=startup,scheduled_queries=360*32,raw_grants=raw,raw_grants_referencing_score_excluded_source=grant_excluded,raw_grants_beyond_source_oracle_age=grant_age_failed,policy_certified=c['accepted'],deployable_grants=raw if c['accepted'] else 0,certification_selected=c['certificates']['center_score']['authorized_episodes'],certification_center_failed=c['certificates']['center_score']['failed_authorized_episodes'],certification_age_failed=c['certificates']['source_action']['failed_authorized_episodes'],conditional_center_upper=float(F(*c['certificates']['center_score']['conditional_upper'])),conditional_age_upper=float(F(*c['certificates']['source_action']['conditional_upper']))))
    fees=[]
    for family in PRIMARY:
        for kind in ('function','deadline'):
            method=family+'_'+kind;mm=[r['methods'][method] for r in paid['rows']];fees.append(dict(method=method,packets=len(mm),source_us_median=statistics.median(v['source_us'] for v in mm),receiver_us_median=statistics.median(v['receiver_us'] for v in mm),wire_bytes_median=statistics.median(v['wire_bytes'] for v in mm),source_us_p95=quantile([v['source_us'] for v in mm]),receiver_us_p95=quantile([v['receiver_us'] for v in mm]),wire_bytes_p95=quantile([v['wire_bytes'] for v in mm])))
    out=dict(manifest=manifest,capture=capture,registry=registry,source=source,service=service,fees=fees,setup=paid['setup'],policy_certified=policy['accepted_policies'],policy_count=48,calibration_confidence_error=float(F(*cal['confidence_error_bound'])),joint_calibration_policy_confidence_lower=1-float(F(*cal['confidence_error_bound']))-.025,audit=audit,freeze_sha256=sha(E/'freeze.json'),analysis_freeze_sha256=sha(E/'analysis_freeze.json'),calibration_receipt_sha256=sha(P/'calibration_frozen.json'),policy_receipt_sha256=sha(P/'policy_frozen.json'),scope='Independent fixed-law calibration/certification/test; observed-source age and initialized measured FIFO. Known registered body/motion assumptions and IID augmented-service law. No unknown actors, real wireless, live ego or claimed new statistical theorem.',goal_complete=False)
    write(a.out,out);print('FINITE_PREDEFINED_SUMMARY_COMPLETE',flush=True)
if __name__=='__main__':main()
