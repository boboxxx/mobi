#!/usr/bin/env python3
import argparse, copy, gzip, hashlib, json, math, os, socket, sys, time
from pathlib import Path
import numpy as np
import stream
from continuity import LegacyReceiver
from bench import schedule


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True)
    ap.add_argument('--previous',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(exist_ok=False);(a.out/'packets').mkdir();(a.out/'source').mkdir()
    assert all(os.environ.get(n)=='1' for n in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'])
    stream.library();body=stream.body
    profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),
                  vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=body.Contract()
    previous=json.loads(a.previous.read_bytes());sources={};inputs={};maintenance=[];rows=[];contexts=[]
    def read(p):
        b=p.read_bytes();inputs[str(p)]=hashlib.sha256(b).hexdigest();return b
    for run in sorted(a.capture.iterdir()):
        if not (run/'record.json.gz').exists():continue
        record=json.loads(gzip.decompress(read(run/'record.json.gz')))
        if not record['initialized']:continue
        ctx=next(x for x in previous['contexts'] if x['run']==run.name)
        decisions={x['id']:x for x in record['decisions']}
        old=LegacyReceiver(profiles,contract,run.name,'Carla/Maps/Town10HD_Opt');rx=stream.Receiver(profiles,contract)
        setup=time.perf_counter()
        for identity in ctx['prefix_ids']:
            d=decisions[identity];blob=read(run/'packets'/(identity+'.json'));b=json.loads(blob)
            scope=body.Scope(run.name,old.frame_id,tuple(d['query']),b['raw']['payload']['scope']['plane_z'])
            motion=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
            assert old.accept(blob,scope,motion,d['receiver_check_time'])
            anchor=rx.register(old,blob,scope,motion)
        setup_ms=(time.perf_counter()-setup)*1000
        assert anchor.identity==ctx['anchor_packet_sha256']
        contexts.append(dict(run=run.name,prefix_ids=ctx['prefix_ids'],anchor=body.asdict(anchor),setup_ms=setup_ms))
        for repeat in range(3):
            queue_end=anchor.reference_us;buffer=[];cache={};done={};costs={}
            for d in record['decisions']:
                if d['phase']!='drive' or not 20<=d['index']<=39:continue
                path=run/'clouds'/(d['id']+'.npz');read(path)
                with np.load(path) as c:xyz,origin=c['xyz'].copy(),c['origin'].copy()
                ref=math.ceil(d['stamp']*1e6);arrival=ref+math.ceil(d['acquisition_s']*1e6)
                x=dict(id=d['id'],ref=ref,sequence=d['sequence'],stamp=d['stamp']);buffer.append(x)
                start=time.perf_counter();raw=stream.step(xyz,origin,d['stamp'],d['stamp'],profiles,contract,anchor,.475,d['sequence'])
                gen_ms=(time.perf_counter()-start)*1000;begin=max(arrival,queue_end)
                queue_end=begin+math.ceil(gen_ms*1000);cache[d['id']]=raw;done[d['id']]=queue_end;costs[d['id']]=gen_ms
                m=dict(run=run.name,id=d['id'],repeat=repeat,ref_us=ref,arrival_us=arrival,start_us=begin,
                       finish_us=queue_end,generation_ms=gen_ms,queue_wait_us=begin-arrival,geometry=raw is not None)
                maintenance.append(m);print(json.dumps(dict(maintenance=m)),flush=True)
                if raw and repeat==0:(a.out/'source'/(run.name+'_'+d['id']+'.json')).write_bytes(body.canonical(raw))
                if d['id'] not in ['drive_025','drive_039']:continue
                for method in ['stream_fixed','cold_native']:
                    selected=schedule(buffer,anchor,x);packet=None;blob=None;verify=0.;assemble=0.;current_gen=None
                    if method=='stream_fixed':
                        ready=queue_end
                        start=time.perf_counter()
                        if selected is not None and all(cache[z['id']] is not None for z in selected):
                            blob=stream.base.wire(anchor,[cache[z['id']] for z in selected])
                            if blob:packet=stream.encode(blob)
                        assemble=(time.perf_counter()-start)*1000
                        if packet:
                            start=time.perf_counter();fact=rx.inspect(packet);verify=(time.perf_counter()-start)*1000
                            assert fact['endpoint_us']==ref+475_000
                    else:
                        start=time.perf_counter();raw_cold=stream.step(xyz,origin,d['stamp'],d['stamp'],profiles,contract,anchor,.475,d['sequence'],full=True)
                        current_gen=(time.perf_counter()-start)*1000
                        ready=arrival+math.ceil(current_gen*1000)
                        start=time.perf_counter()
                        if raw_cold:
                            blob=body.canonical(dict(kind='body-evidence-v1',prior=None,motion=body.asdict(anchor.motion),raw=raw_cold));packet=stream.encode(blob)
                        assemble=(time.perf_counter()-start)*1000
                        if packet:
                            start=time.perf_counter();decoded=stream.decode(packet);probe=copy.deepcopy(old)
                            assert probe.accept(decoded,anchor.scope,anchor.motion,d['stamp']+.02)
                            copy.deepcopy(rx).register(probe,decoded,anchor.scope,anchor.motion)
                            verify=(time.perf_counter()-start)*1000
                    wire_ms=20+(len(packet)*8/20_000 if packet else 0)
                    total=(ready-ref)/1000+assemble+verify+wire_ms
                    age=max(50_000,math.ceil(total/50)*50_000);geometric=packet is not None
                    passed=bool(geometric and age+200_000<475_000)
                    if packet and method=='stream_fixed':assert copy.deepcopy(rx).accept(packet,(ref+age)/1e6,.2)==passed
                    row=dict(run=run.name,id=d['id'],repeat=repeat,method=method,geometry=geometric,
                             bytes=len(packet) if packet else 0,raw_bytes=len(blob) if blob else 0,
                             planned_ids=[z['id'] for z in selected] if selected and method=='stream_fixed' else [d['id']],
                             steps=len(selected) if selected and geometric and method=='stream_fixed' else int(geometric),
                             ready_us=ready,acquisition_ms=d['acquisition_s']*1000,
                             current_generation_ms=current_gen,assembly_ms=assemble,verification_ms=verify,
                             wire_ms=wire_ms,total_ms=total,age_us=age,
                             cached_work_ms=sum(costs[z['id']] for z in selected) if selected and method=='stream_fixed' else 0.,
                             action_slack_us=475_000-age-200_000 if geometric else None,
                             hypothetical_action_pass=passed)
                    rows.append(row);print(json.dumps(dict(target=row)),flush=True)
                    if packet and repeat==0:(a.out/'packets'/(run.name+'_'+d['id']+'_'+method+'.bin')).write_bytes(packet)
    assert len(maintenance)==360 and len(rows)==72 and len(contexts)==6
    root=Path(__file__).resolve().parents[2]
    for module in list(sys.modules.values()):
        f=getattr(module,'__file__',None)
        if f:
            p=Path(f).resolve()
            if root in p.parents and p.is_file() and p.suffix=='.py':sources[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
    report=dict(host=socket.gethostname(),contexts=contexts,rows=rows,maintenance=maintenance,
                input_sha256=inputs,source_sha256=sources,previous_sha256=hashlib.sha256(a.previous.read_bytes()).hexdigest(),
                library_sha256=hashlib.sha256(Path(os.environ['MOBI_RASTER_LIBRARY']).read_bytes()).hexdigest(),
                protocol_sha256=hashlib.sha256(Path(__file__).with_name('PROTOCOL.md').read_bytes()).hexdigest(),
                scope='Retrospective timestamped FIFO maintenance; all preprocessing charged, all receiver geometry verified; no moving closed-loop/physical/WCET/novelty claim.')
    (a.out/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
