#!/usr/bin/env python3
"""Separate posthoc expiry-gap audit; no changes to frozen predictor/policy."""
import argparse,hashlib,json,math,statistics
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def stats(values):
    x=sorted(values);n=len(x)
    return dict(n=n,median_us=statistics.median(x) if n else None,mean_us=sum(x)/n if n else None,p95_us=x[max(0,math.ceil(.95*n)-1)] if n else None,p99_us=x[max(0,math.ceil(.99*n)-1)] if n else None,max_us=max(x) if n else None,at_most_10ms=sum(v<=10000 for v in x))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results;d=read(p/'action_functional_sheng.json');audit=read(p/'action_functional_audit_sheng.json');assert audit['action_functional_sha256']==sha(p/'action_functional_sheng.json');rows={r['id']:r for r in d['rows']};groups=[]
    for rate in (20000000,2000000):
        for method in ('union','lossless_centers','full_xyz'):
            gaps=[];over=[];remaining=[];orc=[];byclass={bp:[] for bp in d['registry']};source_ids=set();authority_episodes=set()
            for tr in d['traces']:
                if tr['bitrate']!=rate or tr['method']!=method:continue
                for dec in tr['decisions']:
                    if not dec['grant']:continue
                    r=rows[dec['fact_id']];q=dec['query'];l=r['bounds'][q]['lower_us'];g=r['grid_oracle_us'][q];assert dec['deadline_us']==r['source_us']+l
                    gaps.append(max(0,g-l));over.append(max(0,l-g));remaining.append(dec['deadline_us']-dec['now_us']-220000);orc.append(r['source_us']+g-dec['now_us']-220000);byclass[r['blueprint']].append(max(0,g-l));source_ids.add((r['id'],q));authority_episodes.add(tr['episode_id'])
            groups.append(dict(bitrate=rate,method=method,scheduled_queries=11520,grants=len(gaps),distinct_authorizing_source_query_pairs=len(source_ids),episodes_with_any_grant=len(authority_episodes),positive_expiry_slack=stats(gaps),deadline_overstatement=stats(over),paid_remaining_after_reserve=stats(remaining),oracle_remaining_after_reserve=stats(orc),classes=[dict(blueprint=bp,positive_expiry_slack=stats(x)) for bp,x in byclass.items()]))
    result=dict(comparisons=groups,source_sha256=sha(Path(__file__)),functional_sha256=sha(p/'action_functional_sheng.json'),functional_audit_sha256=sha(p/'action_functional_audit_sheng.json'),scope='Descriptive conditional-on-observed-grant expiry gaps against independently audited finite future-grid contact labels. Selection and repeated grants are explicit; quantiles have no distribution-free conditional-risk guarantee. 500ms cap causes saturation ties. No new policy, tuning, WCET, full-raw optimality or continuous physical safety claim.')
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(groups))
if __name__=='__main__':main()
