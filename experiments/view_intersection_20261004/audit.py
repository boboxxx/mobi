#!/usr/bin/env python3
"""Independent integer certificate, timeline and saved-truth audit.

No production geometry, cache, or replay module is imported.
"""
import argparse,hashlib,json,math
from pathlib import Path
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[2]
PS=10**12;NS=10**6
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def rootup(n):
    r=math.isqrt(n)
    return r if r*r==n else r+1
def certificate(c,left,right,q,radius):
    a,b=left[c['i']],right[c['j']]
    sep=sum((a[k]-b[k])**2 for k in range(2))
    if c['kind']=='disjoint':assert sep>4*radius**2;return None
    assert sep<=4*radius**2
    p=c['point'];assert len(p)==2 and all(type(v) is int for v in p)
    for center in (a,b):assert sum((p[k]-center[k]*PS)**2 for k in range(2))<=(radius*PS)**2
    n=sum((p[k]-q[k]*PS)**2 for k in range(2));hi=(rootup(n)+PS-1)//PS
    if c['kind']=='inside':assert p==[v*PS for v in q];lo=0
    elif c['kind']=='tangent':
        assert sep==4*radius**2 and p==[(a[k]+b[k])*PS//2 for k in range(2)]
        lo=math.isqrt(n)//PS
    else:
        assert c['kind']=='dual';w=c['weights'];assert len(w)==2 and all(type(v) is int and v>=0 for v in w)
        directions=[[p[k]-center[k]*PS for k in range(2)] for center in (a,b)]
        normal=[-sum(w[i]*directions[i][k] for i in range(2)) for k in range(2)]
        num=0
        for i,center in enumerate((a,b)):
            dot=sum(directions[i][k]*(q[k]-center[k]) for k in range(2))
            num+=w[i]*(dot*NS-radius*rootup(sum(v*v for v in directions[i])*NS**2))
        denom=rootup(sum(v*v for v in normal)*NS**2)
        lo=max(0,num//denom) if denom else 0
    assert (lo,hi)==(c['lower_um'],c['upper_um']) and lo<=hi
    return lo,hi
def distance(d,left,right,q,radius):
    proofs=d['proofs'];seen={(c['i'],c['j']) for c in proofs};assert len(seen)==len(proofs)
    assert all(0<=i<len(left) and 0<=j<len(right) for i,j in seen)
    values=[certificate(c,left,right,q,radius) for c in proofs]
    if len(proofs)==1 and proofs[0]['kind']=='inside':
        assert d['status']=='bounded' and d['lower_um']==d['upper_um']==0;return
    assert seen=={(i,j) for i in range(len(left)) for j in range(len(right))}
    valid=[v for v in values if v is not None]
    if not valid:assert d['status']=='empty';return
    low=min(v[0] for v in valid);high=min(v[1] for v in valid)
    assert (d['lower_um'],d['upper_um'])==(low,high)
    assert d['status']==('bounded' if high-low<=2 else 'precision_gap')
def age(distance,body,claimed):
    def safe(t):return 2000000*(distance-body)>10000000*t+3*t*t
    if distance<=body:assert claimed==0;return
    assert 0<=claimed<=500000 and safe(claimed)
    if claimed<500000:assert not safe(claimed+1)
def queues(rows,pairs,method,rate,t0):
    ordered=sorted(rows,key=lambda r:(r['source_us']+r['acquisition_us'],r['layout']))
    source=wire=receiver=-10**30;known={};events=[];jobs=[]
    for r in ordered:
        m=r['methods'][method];ss=max(source,r['source_us']+r['acquisition_us']);se=ss+m['source_us'];source=se
        ws=max(wire,se);we=ws+(8000000*m['wire_bytes']+rate-1)//rate;wire=we
        rs=max(receiver,we+20000);de=rs+m['receiver_us'];k=(r['episode_id'],r['blueprint'],r['frame'],r['source_us'])
        layouts=known.setdefault(k,set());assert r['layout'] not in layouts
        branch='combine' if layouts else 'store';layouts.add(r['layout']);end=de+r['extra'][method][branch]['us'];receiver=end
        events.append(dict(kind='single',id=r['id'],source_ids=[r['id']],source_us=r['source_us'],ready_us=de,deadlines_us=[r['source_us']+b['lower_us'] if r['available'] else -10**30 for b in r['bounds']]))
        status='not_paired'
        if branch=='combine':
            p=pairs[r['pair_id']];g=p['geometry'];status=g['status']
            if status=='bounded':events.append(dict(kind='intersection',id=p['id'],source_ids=p['source_ids'],source_us=r['source_us'],ready_us=end,deadlines_us=[r['source_us']+b['lower_us'] for b in g['queries']]))
            elif status=='empty':events.append(dict(kind='contradiction',id=p['id'],source_ids=p['source_ids'],source_us=r['source_us'],ready_us=end))
        jobs.append(dict(id=r['id'],source_us=r['source_us'],source_start_us=ss,source_end_us=se,tx_start_us=ws,tx_end_us=we,receiver_start_us=rs,decoded_at_us=de,extra_branch=branch,extra_us=end-de,receiver_end_us=end,wire_bytes=m['wire_bytes'],pair_status=status))
    events.sort(key=lambda e:(e['ready_us'],e['kind'],e['id']));decisions=[]
    for step in range(16):
        now=t0+step*50000;prefix=[e for e in events if e['ready_us']<=now];failed=any(e['kind']=='contradiction' for e in prefix)
        for q in range(2):
            candidates=[] if failed else [(e['deadlines_us'][q],e['id']) for e in prefix if e['kind']!='contradiction']
            deadline,fact=max(candidates,default=(-10**30,None))
            decisions.append(dict(step=step,query=q,now_us=now,fact_id=fact,deadline_us=deadline,grant=deadline>=now+220000,contradiction_seen=failed))
    return dict(jobs=jobs,events=events,decisions=decisions,wire_bytes=sum(j['wire_bytes'] for j in jobs),grants=sum(d['grant'] for d in decisions),scheduled_queries=32,contradiction_events=sum(e['kind']=='contradiction' for e in events))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--parent',type=Path,required=True);ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    d=read(a.results/'analysis_sheng.json');parent=read(a.parent/'analysis_sheng.json');assert d['parent_analysis_sha256']==sha(a.parent/'analysis_sheng.json') and d['parent_audit_sha256']==sha(a.parent/'audit_sheng.json')
    for mapping in (d['source_hashes'],d['input_hashes']):
        for name,h in mapping.items():assert sha(ROOT/name)==h,name
    original={r['id']:r for r in parent['rows']};pairs=d['pairs'];outrows={r['id']:r for r in d['rows']};eps={e['episode']['id']:e for e in parent['episodes']}
    assert set(outrows)=={r['id'] for r in parent['rows'] if r['split']=='test'}
    checked=[];proof_count=0
    for p in pairs.values():
        first,second=[original[i] for i in p['source_ids']];assert first['layout']==0 and second['layout']==1
        for k in ('episode_id','blueprint','source_us','frame','radius_um'):assert first[k]==second[k]==p[k]
        assert first['step']==second['step']==p['step'] and first['true_xy']==second['true_xy']
        assert p['left_cm']==first['centers_cm'] and p['right_cm']==second['centers_cm']
        body=math.ceil(math.sqrt(sum(x*x for x in parent['contract_body']['catalog'][p['blueprint']]))*1e6);assert body==p['body_um']
        left=[[v*10000 for v in c] for c in p['left_cm']];right=[[v*10000 for v in c] for c in p['right_cm']];g=p['geometry']
        if not left or not right:assert g==dict(status='missing_view',queries=[])
        else:
            for index,z in enumerate(g['queries']):
                q=[(-6000000,6000000)[index],0];assert z['query']==q
                distance(z['distance'],left,right,q,p['radius_um']);proof_count+=len(z['distance']['proofs'])
                age(z['distance']['lower_um'],body+750000,z['lower_us']);age(z['distance']['upper_um'],body+750000,z['upper_us']);assert z['upper_us']-z['lower_us']<=1
                assert z['lower_us']+1>=max(first['bounds'][index]['lower_us'],second['bounds'][index]['lower_us'])
            if g['status']=='bounded':assert len(g['queries'])==2
            else:
                assert g['status'] in ('empty','precision_gap');f=g['failed_query'];assert f['query']==[(-6000000,6000000)[len(g['queries'])],0]
                distance(f['distance'],left,right,f['query'],p['radius_um']);proof_count+=len(f['distance']['proofs']);assert f['distance']['status']==g['status']
        covered=first['covered'] and second['covered']
        if covered and left and right:
            for centers in (left,right):
                truth=[Decimal(str(x))*1000000 for x in first['true_xy']]
                assert any(sum((truth[k]-c[k])**2 for k in range(2))<=p['radius_um']**2 for c in centers)
            assert g['status']!='empty'
        checked.append(dict(id=p['id'],blueprint=p['blueprint'],status=g['status'],both_views_covered=covered,
                            horizon_gains_us=[z['lower_us']-max(first['bounds'][q]['lower_us'],second['bounds'][q]['lower_us']) for q,z in enumerate(g['queries'])]))
    for r in d['rows']:
        old=original[r['id']]
        for k in ('id','episode_id','blueprint','step','layout','frame','source_us','acquisition_us','available','bounds','methods'):assert r[k]==old[k]
        for m in ('union','lossless_centers','full_xyz'):
            for b in ('store','combine'):
                t=r['extra'][m][b];assert len(t['samples_s'])==3 and all(math.isfinite(x) and x>=0 for x in t['samples_s']);assert t['us']==math.ceil(max(t['samples_s'])*1e6)
    tracechecks=[]
    for t in d['traces']:
        rows=[r for r in d['rows'] if r['episode_id']==t['episode_id']];t0=min((r['source_us'] for r in rows),default=0);expected=queues(rows,pairs,t['method'],t['bitrate'],t0)
        for k,v in expected.items():assert t[k]==v,(t['episode_id'],k)
        base=next(x for x in parent['traces'] if x['episode_id']==t['episode_id'] and x['method']==t['method'] and x['bitrate']==t['bitrate']);unsafe=bad=intersection_grants=0
        events={e['id']:e for e in t['events']}
        excluded=any(not r['covered'] for r in parent['rows'] if r['episode_id']==t['episode_id'])
        for dec in t['decisions']:
            if not dec['grant']:continue
            ev=events[dec['fact_id']];assert ev['ready_us']<=dec['now_us'] and dec['now_us']+220000<=dec['deadline_us']<=ev['source_us']+500000
            intersection_grants+=ev['kind']=='intersection';bad+=excluded;ep=eps[t['episode_id']];hit=False
            body=math.ceil(math.sqrt(sum(x*x for x in parent['contract_body']['catalog'][t['blueprint']]))*1e6)/1e6;q=(-6.,6.)[dec['query']];basis=parent['contract_body']['basis'];anchor=basis['anchor'];road=basis['road']
            for s in ep.get('trajectory',[]):
                if not dec['now_us']<=math.floor(s['timestamp']*1e6)<=dec['now_us']+220000:continue
                delta=[s['center'][i]-anchor[i] for i in range(3)];x=sum(delta[i]*road[i][0] for i in range(3));y=sum(delta[i]*road[i][1] for i in range(3));hit|=math.hypot(x-q,y)<=body+.75
            unsafe+=hit
        tracechecks.append(dict(episode_id=t['episode_id'],blueprint=t['blueprint'],method=t['method'],bitrate=t['bitrate'],grants=t['grants'],primary_grants=base['grants'],intersection_chosen_grants=intersection_grants,grants_on_parent_excluded_episode=bad,observed_occupied_grid_grants=unsafe,contradictions=t['contradiction_events']))
    result=dict(pair_checks=checked,trace_checks=tracechecks,certificate_checks=proof_count,source_sha256=sha(Path(__file__)),analysis_sha256=sha(a.results/'analysis_sheng.json'),parent_analysis_sha256=sha(a.parent/'analysis_sheng.json'),scope='Independent exact integer primal/dual lens proofs and all component pairs, strict age endpoints, paid timeline and prefix, inherited test coverage failures and offline observed occupancy. Post-result development, no new risk fit/holdout or physical safety/novelty guarantee.')
    a.out.write_text(json.dumps(result,separators=(',',':'))+'\n');print(json.dumps(dict(pairs=len(checked),proofs=proof_count,traces=len(tracechecks),status_counts={s:sum(c['status']==s for c in checked) for s in ('bounded','empty','precision_gap','missing_view')})))
if __name__=='__main__':main()
