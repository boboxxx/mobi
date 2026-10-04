#!/usr/bin/env python3
"""All planned-episode risk, oracle gaps and matched measured policy totals."""
import math
from fractions import Fraction as F
from collections import defaultdict,Counter
from io_common import E,P,read,write,sha
FAMILIES=('joint','ridge','local_mean','local_modes')
GEOMETRIES=FAMILIES+('local_mean_plain','local_modes_plain','local_modes_clip')
def quantile(values,p):
    if not values:return None
    v=sorted(values);pos=F((len(v)-1)*p,100);i=pos.numerator//pos.denominator;return float(v[i]+(v[min(i+1,len(v)-1)]-v[i])*(pos-i))
def binomial_upper(k,n,alpha):
    if k==n:return [1,1]
    lo=F(0);hi=F(1)
    for _ in range(64):
        p=(lo+hi)/2;cdf=sum(F(math.comb(n,j))*p**j*(1-p)**(n-j) for j in range(k+1))
        if cdf>alpha:lo=p
        else:hi=p
    return [hi.numerator,hi.denominator]
def main():
    d=read(P/'qualification_sheng.json');paid=read(P/'paid_sheng.json');audit=read(P/'audit_sheng.json');assert audit['qualification_sha256']==sha(P/'qualification_sheng.json') and audit['paid_sha256']==sha(P/'paid_sheng.json');byep=defaultdict(list)
    for r in d['rows']:byep[r['episode_id']].append(r)
    source_summary=[];risk_summary=[]
    for bp in d['catalog']:
        eps=[e for e in d['episodes'] if e['episode']['blueprint']==bp and e['episode']['split']=='test'];assert len(eps)==60;rr=[r for e in eps for r in byep[e['episode']['id']]]
        for family in FAMILIES:
            q=F(*d['registry'][bp][family]);excluded=[e['episode']['id'] for e in eps if F(*d['episode_scores'][e['episode']['id']][family])>q];k=len(excluded);risk_summary.append(dict(blueprint=bp,family=family,q=[q.numerator,q.denominator],planned_test_episodes=60,captured_test_episodes=sum(e['status']=='captured' for e in eps),excluded_episodes=excluded,per_family_class_binomial95_upper=binomial_upper(k,60,F(1,20)),simultaneous24_binomial95_upper=binomial_upper(k,60,F(1,480))))
        for key in GEOMETRIES:
            gaps=[];ages=[];over=above=below=0;clip_gain=clip_loss=0
            for r in rr:
                out=r['geometries'][key];aa=out['lower_us'] if out['status']=='bounded' else [0,0];joint=r['geometries']['joint'];jj=joint['lower_us'] if joint['status']=='bounded' else [0,0]
                for t,o,j in zip(aa,r['oracle_us'],jj):gaps.append(max(0,o-t));ages.append(t);over+=t>o;above+=t>j;below+=t<j
                if key=='local_modes_clip':
                    primary=r['geometries']['local_modes'];vv=primary['lower_us'] if primary['status']=='bounded' else [0,0]
                    for t,v in zip(aa,vv):clip_gain+=t>v;clip_loss+=t<v
            source_summary.append(dict(blueprint=bp,method=key,captured_source_frames=len(rr),source_queries=len(ages),statuses=dict(Counter(r['geometries'][key]['status'] for r in rr)),prediction_statuses=dict(Counter(r['prediction']['status'] for r in rr)),age_overstatements=over,above_joint=above,below_joint=below,oracle_gap_us_p50=quantile(gaps,50),oracle_gap_us_p95=quantile(gaps,95),age_us_p50=quantile(ages,50),age_us_p95=quantile(ages,95),clip_improved_queries=clip_gain,clip_worse_queries=clip_loss))
    policies=[]
    for rate in (20000000,2000000):
        for startup in ('warm','cold'):
            for family in FAMILIES:
                methods=[family+'_function',family+'_deadline'];tt={m:{t['episode_id']:t for t in paid['traces'] if t['method']==m and t['rate']==rate and t['startup']==startup} for m in methods};function_only=deadline_only=0;exposure={m:0 for m in methods}
                for ep,t in tt[methods[0]].items():
                    for a,b in zip(t['decisions'],tt[methods[1]][ep]['decisions']):function_only+=int(a['grant'] and not b['grant']);deadline_only+=int(b['grant'] and not a['grant'])
                lookup={r['id']:r for r in d['rows']}
                for m in methods:
                    for t in tt[m].values():
                        for dec in t['decisions']:
                            if not dec['grant']:continue
                            fact=lookup[dec['fact_id']];exposure[m]+=F(*fact['scores'][family])>F(*d['registry'][fact['blueprint']][family])
                assert all(len(tt[m])==360 for m in methods)
                policies.append(dict(family=family,rate=rate,startup=startup,scheduled_queries=11520,grants={m:sum(t['grants'] for t in tt[m].values()) for m in methods},function_only=function_only,deadline_only=deadline_only,grants_referencing_center_excluded_source=exposure))
    profiles=[]
    for method in paid['rows'][0]['methods']:
        vv=[r['methods'][method] for r in paid['rows']];profiles.append(dict(method=method,rows=len(vv),source_us_median=quantile([v['source_us'] for v in vv],50),source_us_p95=quantile([v['source_us'] for v in vv],95),receiver_us_median=quantile([v['receiver_us'] for v in vv],50),receiver_us_p95=quantile([v['receiver_us'] for v in vv],95),wire_bytes_median=quantile([v['wire_bytes'] for v in vv],50),wire_bytes_p95=quantile([v['wire_bytes'] for v in vv],95)))
    out=dict(capture=read(P/'capture/manifest.json'),planned_capture_statuses=dict(Counter(e['status'] for e in d['episodes'])),calibration_confidence_lower=1-24*.95**125,risk=risk_summary,source=source_summary,policies=policies,profiles=profiles,setup={k:paid['setup'][k] for k in ('wire_bytes','source_us','receiver_us')},audit={k:audit[k] for k in ('frames','independent_geometry_checks','actual_packet_checks','trace_checks','decision_checks','observed_future_grid_checks','observed_future_grid_violations','age_overstatements')},qualification_sha256=sha(P/'qualification_sheng.json'),paid_sha256=sha(P/'paid_sheng.json'),audit_sha256=sha(P/'audit_sheng.json'),scope='Independent fixed-law known-actor episode qualification. Source-query gaps relative to exact current-center oracle under the same body/motion model. Actual profiles and FIFO paid counts are descriptive. No conditional-grant risk, continuous road-safety, live ego/radio or established MobiCom novelty.');write(P/'summary_sheng.json',out);print('FINITE_HYPOTHESES_SUMMARY_COMPLETE',flush=True)
if __name__=='__main__':main()
