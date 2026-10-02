#!/usr/bin/env python3
"""Finite causal FIFO simulation; CPU services measured where executed."""
import argparse,collections,hashlib,heapq,json,math,os,time
from pathlib import Path
import numpy as np
import context,repair
G=repair.G;body=repair.body
METHODS={'fixed':('scalar','none'),'fine':('fine','none'),'backfill':('scalar','backfill'),'backward':('scalar','backward'),'backward_fine':('fine','backward')}
PRESETS={'standard':(20.,()),'slow':(.5,()),'blackout':(20.,(27,28,29))}
def us(ms):return max(1,math.ceil(ms*1000))
def measure(f):
    t=time.perf_counter();value=f();return value,(time.perf_counter()-t)*1000

def union(items,start,end):
    out=[]
    for a,b in sorted((max(start,a),min(end,b)) for a,b in items):
        if a>=b:continue
        if out and a<=out[-1][1]:out[-1][1]=max(out[-1][1],b)
        else:out.append([a,b])
    return out

def subtract(intervals,busy):
    out=[]
    for a,b in intervals:
        cur=a
        for x,y in busy:
            if y<=cur:continue
            if x>=b:break
            if x>cur:out.append([cur,x])
            cur=max(cur,y)
        if cur<b:out.append([cur,b])
    return out

class Simulation:
    def __init__(self,ctx,method,preset,repeat,save):
        self.ctx=ctx;self.method=method;self.preset=preset;self.repeat=repeat;self.save=save;self.rate,self.drops=PRESETS[preset];mode,feedback=METHODS[method];rm=ctx['meta'][mode];rd=ctx['root_decision'];rootref=repair.ref(ctx['root']);self.root_sender=rootref+us(rd['acquisition_s']*1000+rd['generation_s']*1000+rm['encoding_ms']);self.link_free=self.root_sender+math.ceil(rm['bytes']*8/self.rate);self.root_arrival=self.link_free+20000;self.receipt=self.root_arrival+us(rm['validation_ms']+rm['registration_ms']);self.up_free=0;self.rx=context.receiver(ctx,mode,self.receipt,feedback);self.source=repair.Source(ctx['profiles'],ctx['contract'],self.rx.core.anchor);self.sender=G.dictionary.Sender();self.events=[];self.serial=0;self.now=rootref;self.queues={k:collections.deque() for k in ('source','receiver')};self.busy=dict(source=True,receiver=True);self.log=[];self.rows=[];self.cpu=[];self.grants=[(self.receipt,rm['anchor']['endpoint_us']-200000)];self.wirebytes=rm['bytes'];self.upbytes=0;self.repairs=[]
        self.schedule(self.root_sender,'root_source',None);self.schedule(self.receipt,'root_receiver',None)
        for i in range(20,40):self.schedule(ctx['sources'][('drive_%03d'%i,repeat)]['arrival_us'],'source_arrival',i)
    def schedule(self,when,kind,data):
        if when<self.now:raise ValueError('Noncausal event')
        self.serial+=1;heapq.heappush(self.events,(when,self.serial,kind,data))
    def enqueue(self,resource,job):
        job['enqueued']=self.now;self.queues[resource].append(job);self.start(resource)
    def transmit(self,wire,direction,kind,data,drop=False):
        field='link_free' if direction=='down' else 'up_free';begin=max(self.now,getattr(self,field));end=begin+math.ceil(len(wire)*8/self.rate);setattr(self,field,end);arrival=end+20000
        record=dict(kind=kind,direction=direction,enqueued_us=self.now,start_us=begin,end_us=end,arrival_us=arrival,bytes=len(wire),sha256=self.save(wire),dropped=drop)
        self.log.append(record)
        if direction=='down':self.wirebytes+=len(wire)
        else:self.upbytes+=len(wire)
        if not drop:self.schedule(arrival,kind,dict(data,wire=wire))
        return record
    def start(self,resource):
        if self.busy[resource] or not self.queues[resource]:return
        job=self.queues[resource].popleft();kind=job['kind'];self.busy[resource]=True;started=self.now
        if kind=='normal_source':
            i=job['index'];raw=self.ctx['original'][i];mode=METHODS[self.method][0];packet=dict(kind='position-flow-v1' if mode=='fine' else 'class-guard-flow-v1',dynamics='observation-speed-age-v1',anchor=self.rx.core.anchor.identity,steps=[raw]);wire,ms=measure(lambda:self.sender.encode(packet,i));src=self.ctx['sources'][('drive_%03d'%i,self.repeat)];job.update(raw=raw,wire=wire,encoding_ms=ms,generation_ms=src['generation_ms']);ms+=src['generation_ms']
        elif kind=='reply_source':
            (wire,stats),ms=measure(lambda:self.source.reply(job['wire']));job.update(reply=wire,stats=stats,request_sha256=self.save(job['wire']))
        elif kind=='normal_receiver':
            try:(decision,state),ms=measure(lambda:self.rx.normal(job['wire'],job['raw'],started));job['decision']=decision
            except (ValueError,KeyError) as e:raise RuntimeError('Normal packet failed: '+repr(e))
        elif kind=='request_receiver':
            wire,ms=measure(lambda:self.rx.request(job['raw']));job['request']=wire
        elif kind=='reply_receiver':
            (decision,state),ms=measure(lambda:self.rx.reply(job['wire'],started));job['decision']=decision
        else:raise ValueError(kind)
        end=started+us(ms);job.update(started=started,end=end,service_ms=ms);self.log.append(dict(kind=kind,resource=resource,enqueued_us=job['enqueued'],start_us=started,end_us=end,service_ms=ms,index=job.get('index'),input_sha256=self.save(job['wire']) if 'wire' in job else None))
        if resource=='receiver':self.cpu.append((started,end))
        self.schedule(end,'complete',dict(resource=resource,job=job))
    def complete(self,resource,job):
        kind=job['kind'];self.busy[resource]=False
        if kind=='normal_source':
            i=job['index'];raw=job['raw'];self.source.add(raw,self.ctx['capture']/'clouds'/('drive_%03d.npz'%i),self.ctx['decisions']['drive_%03d'%i]['stamp']);row=dict(index=i,ref_us=repair.ref(raw),raw_sha256=repair.digest(raw),source_arrival_us=job['enqueued'],sender_start_us=job['started'],sender_end_us=self.now,generation_ms=job['generation_ms'],encoding_ms=job['encoding_ms'],bytes=len(job['wire']),packet_sha256=self.save(job['wire']),dropped=i in self.drops,horizon_us=0,fresh_admission=False)
            row['link']=self.transmit(job['wire'],'down','normal_arrival',dict(index=i,raw=raw,row=row),i in self.drops);self.rows.append(row)
        elif kind=='reply_source':
            event=dict(request_sha256=job['request_sha256'],reply_sha256=self.save(job['reply']),source_start_us=job['started'],source_end_us=self.now,stats=job['stats']);self.repairs.append(event);event['link']=self.transmit(job['reply'],'down','reply_arrival',dict(repair=event))
        elif kind=='normal_receiver':
            d=job['decision'];self.rx.normal_finish(self.now,d);row=job['row'];age=max(50000,math.ceil((self.now-row['ref_us'])/50000)*50000);row.update(receiver_start_us=job['started'],receiver_end_us=self.now,verification_ms=job['service_ms'],decision=d,horizon_us=d['horizon_us'],age_us=age,fresh_admission=bool(d['horizon_us']>age+200000),authority=list(self.rx.core.authority),fact_ref_us=self.rx.core.ref)
            if d['horizon_us']>0:self.grants.append((self.now,d['endpoint_us']-200000))
            if d['horizon_us']<475000 and self.rx.mode!='none':self.enqueue('receiver',dict(kind='request_receiver',raw=job['raw'],index=job['index']))
        elif kind=='request_receiver':
            if job['request'] is not None:self.transmit(job['request'],'up','request_arrival',{})
        elif kind=='reply_receiver':
            self.rx.reply_finish(self.now);d=job['decision'];event=job['repair'];event.update(receiver_start_us=job['started'],receiver_end_us=self.now,verification_ms=job['service_ms'],decision=d,authority=list(self.rx.core.authority),fact_ref_us=self.rx.core.ref)
            if d['horizon_us']>0:self.grants.append((self.now,d['endpoint_us']-200000))
        self.start(resource)
    def run(self):
        while self.events:
            self.now,_,kind,data=heapq.heappop(self.events)
            if kind=='root_source':
                self.source.add(self.ctx['root'],self.ctx['capture']/'clouds'/(self.ctx['root_identity']+'.npz'),self.ctx['root_decision']['stamp']);self.busy['source']=False;self.start('source')
            elif kind=='root_receiver':self.busy['receiver']=False;self.start('receiver')
            elif kind=='source_arrival':self.enqueue('source',dict(kind='normal_source',index=data))
            elif kind=='normal_arrival':self.enqueue('receiver',dict(data,kind='normal_receiver'))
            elif kind=='request_arrival':self.enqueue('source',dict(data,kind='reply_source'))
            elif kind=='reply_arrival':self.enqueue('receiver',dict(data,kind='reply_receiver'))
            elif kind=='complete':self.complete(**data)
            else:raise ValueError(kind)
        start=repair.ref(self.ctx['original'][20]);end=repair.ref(self.ctx['original'][39])+500000;intervals=subtract(union(self.grants,start,end),union(self.cpu,start,end));covered=sum(b-a for a,b in intervals)
        return dict(run=self.ctx['name'],method=self.method,preset=self.preset,repeat=self.repeat,root_sender_end_us=self.root_sender,root_link_end_us=self.root_arrival-20000,root_receipt_us=self.receipt,rows=self.rows,events=self.log,repairs=self.repairs,downlink_bytes=self.wirebytes,uplink_bytes=self.upbytes,coverage=dict(start_us=start,end_us=end,covered_us=covered,coverage=covered/(end-start),intervals=intervals,grants=self.grants,cpu=self.cpu))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--gate',action='store_true');a=ap.parse_args();a.out.mkdir(exist_ok=False);(a.out/'packets').mkdir();assert all(os.environ.get(k)=='1' for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']);runs=[];contexts=[];rng=np.random.default_rng(20261004)
    def save(wire):
        h=hashlib.sha256(wire).hexdigest();p=a.out/'packets'/(h+'.bin')
        if not p.exists():p.write_bytes(wire)
        return h
    for name in (['c0_view0_reference_rate20'] if a.gate else context.RUNS):
        ctx=context.load(name);contexts.append(dict(run=name,prefix=ctx['prefix'],warm_ms=ctx['warm_ms'],root_metadata=ctx['meta'],root_capture=ctx['root_decision']))
        for repeat in range(1 if a.gate else 3):
            for preset in (['standard'] if a.gate else PRESETS):
                for method in rng.permutation(list(METHODS)).tolist():
                    result=Simulation(ctx,method,preset,repeat,save).run();runs.append(result);(a.out/('run_%03d.json'%len(runs))).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(run=name,method=method,preset=preset,repeat=repeat,geometry=sum(x['horizon_us']>0 for x in result['rows']),fresh=sum(x['fresh_admission'] for x in result['rows']),repairs=len(result['repairs']),coverage=result['coverage']['coverage'])),flush=True)
    source={}
    for p in Path(__file__).parent.glob('*.py'):source[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    (a.out/'analysis.json').write_text(json.dumps(dict(contexts=contexts,runs=runs,source_sha256=source,scope='Saved stationary captures; measured services on current host; modeled two-way links; conditional uncalibrated physical bounds; no new CARLA drive'),indent=2)+'\n')
if __name__=='__main__':main()
