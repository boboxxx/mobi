"""Additional current-only cache/intersection job after primary wire decoding."""
from kernel import geometry

def key(r):
    return (r['episode_id'],r['blueprint'],r['frame'],r['source_us'])

def cache_job(cache,current):
    if current['layout'] not in (0,1):raise ValueError('View identity')
    k=key(current)
    bucket=cache.setdefault(k,{})
    if current['layout'] in bucket:raise ValueError('Duplicate view')
    bucket[current['layout']]=dict(current,centers_cm=[list(c) for c in current['centers_cm']])
    if len(bucket)<2:return None
    a,b=bucket[0],bucket[1]
    if any(a[n]!=b[n] for n in ('radius_um','body_um','contract_sha256','calibration_sha256')):
        raise ValueError('Incompatible current contracts')
    return geometry(a['centers_cm'],b['centers_cm'],a['radius_um'],a['body_um'])

def replay(rows,pairs,method,bitrate,t0):
    jobs=sorted(rows,key=lambda r:(r['source_us']+r['acquisition_us'],r['layout']))
    source_free=tx_free=rx_free=-10**30
    events=[];jobs_out=[];cache={}
    for r in jobs:
        m=r['methods'][method]
        src_start=max(source_free,r['source_us']+r['acquisition_us']);src_end=src_start+m['source_us'];source_free=src_end
        tx_start=max(tx_free,src_end);tx_end=tx_start+(m['wire_bytes']*8000000+bitrate-1)//bitrate;tx_free=tx_end
        rx_start=max(rx_free,tx_end+20000);decoded_at=rx_start+m['receiver_us']
        k=key(r);bucket=cache.setdefault(k,{})
        if r['layout'] in bucket:raise ValueError('Duplicate transport source')
        partner=bool(bucket);bucket[r['layout']]=r['id']
        branch='combine' if partner else 'store'
        end=decoded_at+r['extra'][method][branch]['us'];rx_free=end
        events.append(dict(kind='single',id=r['id'],source_ids=[r['id']],source_us=r['source_us'],ready_us=decoded_at,
                           deadlines_us=[r['source_us']+b['lower_us'] if r['available'] else -10**30 for b in r['bounds']]))
        status='not_paired'
        if partner:
            pair_id=r['pair_id'];g=pairs[pair_id]['geometry'];status=g['status']
            if status=='bounded':
                events.append(dict(kind='intersection',id=pair_id,source_ids=pairs[pair_id]['source_ids'],source_us=r['source_us'],ready_us=end,
                                   deadlines_us=[r['source_us']+b['lower_us'] for b in g['queries']]))
            elif status=='empty':
                events.append(dict(kind='contradiction',id=pair_id,source_ids=pairs[pair_id]['source_ids'],source_us=r['source_us'],ready_us=end))
        jobs_out.append(dict(id=r['id'],source_us=r['source_us'],source_start_us=src_start,source_end_us=src_end,
                             tx_start_us=tx_start,tx_end_us=tx_end,receiver_start_us=rx_start,decoded_at_us=decoded_at,
                             extra_branch=branch,extra_us=end-decoded_at,receiver_end_us=end,wire_bytes=m['wire_bytes'],pair_status=status))
    events.sort(key=lambda e:(e['ready_us'],e['kind'],e['id']))
    facts={};failed=False;decisions=[];i=0
    for step in range(16):
        now=t0+step*50000
        while i<len(events) and events[i]['ready_us']<=now:
            ev=events[i]
            if ev['kind']=='contradiction':failed=True;facts.clear()
            elif not failed:facts[ev['id']]=ev
            i+=1
        for query in range(2):
            eligible=[(e['deadlines_us'][query],e['id']) for e in facts.values()]
            deadline,fact=max(eligible,default=(-10**30,None))
            decisions.append(dict(step=step,query=query,now_us=now,fact_id=fact,deadline_us=deadline,
                                  grant=deadline>=now+220000,contradiction_seen=failed))
    return dict(jobs=jobs_out,events=events,decisions=decisions,wire_bytes=sum(j['wire_bytes'] for j in jobs_out),
                grants=sum(d['grant'] for d in decisions),scheduled_queries=32,
                contradiction_events=sum(e['kind']=='contradiction' for e in events))
