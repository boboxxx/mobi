"""Paid measured FIFO reconstruction, unchanged original source epochs."""
import math

def replay(rows,method,rate,t0,setup=None):
 sf=tf=rf=-10**30;events=[];jobs=[]
 if setup:
  s0=t0;se=s0+setup['source_us'];ts=se;te=ts+math.ceil(setup['wire_bytes']*8*1000000/rate);rs=te+20000;re=rs+setup['receiver_us'];sf=se;tf=te;rf=re;jobs.append(dict(id='setup',source_start_us=s0,source_end_us=se,tx_start_us=ts,tx_end_us=te,receiver_start_us=rs,arrival_us=re,wire_bytes=setup['wire_bytes']))
 for r in sorted(rows,key=lambda r:(r['source_us']+r['acquisition_us'],r['layout'])):
  m=r['methods'][method];ss=max(sf,r['source_us']+r['acquisition_us']);se=ss+m['source_us'];sf=se;ts=max(tf,se);te=ts+math.ceil(m['wire_bytes']*8*1000000/rate);tf=te;rs=max(rf,te+20000);re=rs+m['receiver_us'];rf=re
  event=dict(id=r['id'],source_us=r['source_us'],source_start_us=ss,source_end_us=se,tx_start_us=ts,tx_end_us=te,receiver_start_us=rs,arrival_us=re,wire_bytes=m['wire_bytes'],status=m['status'],deadlines_us=[r['source_us']+v for v in m['lower_us']] if m['status']=='bounded' else [-10**30,-10**30]);events.append(event);jobs.append(event)
 decisions=[];i=0;active=[(-10**30,None),(-10**30,None)];revoked=False
 for step in range(16):
  now=t0+step*50000
  while i<len(events) and events[i]['arrival_us']<=now:
   e=events[i]
   if e['status']=='empty':revoked=True;active=[(-10**30,None),(-10**30,None)]
   if not revoked:
    for q,d in enumerate(e['deadlines_us']):
     if d>active[q][0]:active[q]=(d,e['id'])
   i+=1
  for q,(deadline,key) in enumerate(active):decisions.append(dict(step=step,query=q,now_us=now,fact_id=key,deadline_us=deadline,grant=not revoked and deadline>=now+220000))
 return dict(jobs=jobs,events=events,decisions=decisions,grants=sum(d['grant'] for d in decisions),scheduled_queries=32,wire_bytes=sum(j['wire_bytes'] for j in jobs))
