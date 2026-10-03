"""Causal sender/link/receiver queues and source-aged query deadlines."""
import math

def replay(rows,method,bitrate,t0_us,query_steps=range(16)):
    jobs=sorted(rows,key=lambda r:(r['source_us']+r['acquisition_us'],r['layout']))
    source_free=tx_free=rx_free=-10**30;events=[]
    for r in jobs:
        timing=r['methods'][method];src_start=max(source_free,r['source_us']+r['acquisition_us']);src_end=src_start+timing['source_us'];source_free=src_end
        tx_start=max(tx_free,src_end);tx_end=tx_start+math.ceil(timing['wire_bytes']*8*1000000/bitrate);tx_free=tx_end
        rx_start=max(rx_free,tx_end+20000);rx_end=rx_start+timing['receiver_us'];rx_free=rx_end
        # A refused current frame never creates a new grant. Previously received
        # evidence retains only its original absolute expiry, never a refreshed TTL.
        horizons=[min(200000,b['lower_us']) for b in r['bounds']] if method=='fixed200' else [b['lower_us'] for b in r['bounds']]
        events.append(dict(id=r['id'],source_us=r['source_us'],source_start_us=src_start,source_end_us=src_end,tx_start_us=tx_start,tx_end_us=tx_end,receiver_start_us=rx_start,arrival_us=rx_end,wire_bytes=timing['wire_bytes'],deadlines_us=[r['source_us']+h if r['available'] else -10**30 for h in horizons]))
    decisions=[];active=[(-10**30,None),(-10**30,None)];i=0
    for step in query_steps:
        now=t0_us+step*50000
        while i<len(events) and events[i]['arrival_us']<=now:
            ev=events[i]
            for q,d in enumerate(ev['deadlines_us']):
                if d>active[q][0]:active[q]=(d,ev['id'])
            i+=1
        for q,(deadline,key) in enumerate(active):
            decisions.append(dict(step=step,query=q,now_us=now,fact_id=key,deadline_us=deadline,grant=deadline>=now+220000))
    return dict(events=events,decisions=decisions,wire_bytes=sum(e['wire_bytes'] for e in events),grants=sum(d['grant'] for d in decisions),scheduled_queries=len(decisions))
