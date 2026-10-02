#!/usr/bin/env python3
import argparse,gzip,hashlib,json,math,os,socket,sys,time
from pathlib import Path
import numpy as np
import dictionary as flow
body=flow.body;compact=flow.compact
PRESETS={'standard':(20.,()),'slow':(.5,()),'blackout':(20.,(27,28,29))}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def charge(ms):return math.ceil(ms*1000)
def union(intervals,start,end):
    merged=[]
    for a,b in sorted((max(a,start),min(b,end)) for a,b in intervals):
        if a>=b:continue
        if merged and a<=merged[-1][1]:merged[-1][1]=max(b,merged[-1][1])
        else:merged.append([a,b])
    return sum(b-a for a,b in merged),merged

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(exist_ok=False);(a.out/'packets').mkdir();(a.out/'states').mkdir()
    assert all(os.environ.get(n)=='1' for n in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'])
    compact.library();compact.observer.library();compact.stream.library();root=Path(__file__).resolve().parents[2]
    previous=json.loads((a.baseline/'study/analysis.json').read_bytes());pipeline=json.loads((a.source/'study/analysis.json').read_bytes())
    profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=body.Contract();windows=dict(small=9.,vehicle=11.5)
    rng=np.random.default_rng(20261008);rows=[];contexts=[];coverage=[];inputs={};state_files={}
    def save_state(state):
        data=b''.join(n.encode()+str(x.shape).encode()+x.tobytes() for n,x in sorted(state.possible.items()));key=hashlib.sha256(data).hexdigest()
        if key not in state_files:
            path=a.out/'states'/(key+'.npz');np.savez_compressed(path,**state.possible);state_files[key]=sha(path)
        return key
    for ctx in previous['contexts']:
        name=ctx['run'];run=a.capture/name;record=json.loads(gzip.decompress((run/'record.json.gz').read_bytes()));decisions={d['id']:d for d in record['decisions']}
        legacy=compact.base.LegacyReceiver(profiles,contract,name,'Carla/Maps/Town10HD_Opt');receivers={m:flow.Receiver(m,profiles,contract,windows) for m in flow.METHODS};t=time.perf_counter()
        for identity in ctx['prefix_ids']:
            d=decisions[identity];blob=(run/'packets'/(identity+'.json')).read_bytes();b=json.loads(blob)
            scope=body.Scope(name,legacy.frame_id,tuple(d['query']),b['raw']['payload']['scope']['plane_z']);motion=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
            assert legacy.accept(blob,scope,motion,d['receiver_check_time'])
            for rx in receivers.values():anchor=rx.register(legacy,blob,scope,motion)
        setup=(time.perf_counter()-t)*1000;assert anchor.identity==ctx['anchor']['identity'];receipt=math.ceil(d['receiver_check_time']*1e6)
        roots={m:save_state(rx.root_state) for m,rx in receivers.items() if rx.position}
        contexts.append(dict(run=name,prefix_ids=ctx['prefix_ids'],anchor=body.asdict(anchor),setup_ms=setup,root_receipt_us=receipt,root_states=roots))
        steps={}
        for index in range(20,40):
            identity='drive_%03d'%index;p=a.source/'study/source'/(name+'_'+identity+'.json');inputs[str(p)]=sha(p);steps[index]=json.loads(p.read_bytes())
        start=steps[20]['payload']['reference_us'];end=steps[39]['payload']['reference_us']+500000
        for repeat in range(3):
            for preset,(rate,drops) in PRESETS.items():
                order=rng.permutation(flow.METHODS).tolist()
                for method in order:
                    rx=receivers[method];t=time.perf_counter();rx.reset(receipt);reset=(time.perf_counter()-t)*1000;sender=flow.Sender()
                    send_end=link_end=0;receive_end=receipt+charge(reset);intervals=[(receipt,anchor.endpoint_us-200000)]
                    for index in range(20,40):
                        identity='drive_%03d'%index;raw=steps[index];ref=raw['payload']['reference_us'];src=next(x for x in pipeline['maintenance'] if x['run']==name and x['repeat']==repeat and x['id']==identity)
                        t=time.perf_counter();packet=sender.encode(dict(kind='position-flow-v1' if rx.position else 'center-flow-v1',dynamics='observation-speed-age-v1',anchor=anchor.identity,steps=[raw]),index);encoding=(time.perf_counter()-t)*1000
                        sender_start=max(src['arrival_us'],send_end);gen_end=sender_start+charge(src['generation_ms']);send_end=gen_end+charge(encoding)
                        link_start=max(send_end,link_end);link_end=link_start+math.ceil(len(packet)*8/rate);arrival=link_end+20000
                        dropped=index in drops;verify=0.;decision=None;state=None;rxstart=None;rxend=None
                        if not dropped:
                            rxstart=max(arrival,receive_end);t=time.perf_counter();decision,state=rx.advance(packet,rxstart);verify=(time.perf_counter()-t)*1000
                            rxend=rxstart+charge(verify);rx.finish(rxend);receive_end=rxend
                        available=arrival if dropped else rxend;age=max(50000,math.ceil((available-ref)/50000)*50000);tick=ref+age
                        h=decision['horizon_us'] if decision else 0;fresh=bool(not dropped and h>0 and age+200000<h)
                        if h>0:intervals.append((tick,ref+h-200000))
                        blob_sha=hashlib.sha256(packet).hexdigest();state_key=save_state(state) if state and repeat==0 else None
                        if repeat==0:
                            path=a.out/'packets'/(blob_sha+'.bin')
                            if not path.exists():path.write_bytes(packet)
                        row=dict(run=name,id=identity,index=index,repeat=repeat,preset=preset,method=method,order=order,reset_ms=reset,
                                 ref_us=ref,source_arrival_us=src['arrival_us'],generation_ms=src['generation_ms'],sender_start_us=sender_start,generation_end_us=gen_end,
                                 encoding_ms=encoding,sender_end_us=send_end,link_start_us=link_start,link_end_us=link_end,receiver_arrival_us=arrival,
                                 dropped=dropped,receiver_start_us=rxstart,verification_ms=verify,receiver_end_us=rxend,bytes=len(packet),packet_sha256=blob_sha,
                                 total_ms=(available-ref)/1000,age_us=age,tick_us=tick,horizon_us=h,fresh_admission=fresh,
                                 current_authority=rx.can_act(tick),authority=list(rx.authority),fact_ref_us=rx.ref,decision=decision,state_key=state_key)
                        rows.append(row)
                    covered,merged=union(intervals,start,end);coverage.append(dict(run=name,method=method,preset=preset,repeat=repeat,start_us=start,end_us=end,covered_us=covered,coverage=covered/(end-start),intervals=merged))
                print(json.dumps(dict(run=name,repeat=repeat,preset=preset,rows=len(rows))),flush=True)
    sources={}
    for mod in list(sys.modules.values()):
        f=getattr(mod,'__file__',None)
        if f:
            p=Path(f).resolve()
            if root in p.parents and p.is_file() and p.suffix=='.py':sources[str(p.relative_to(root))]=sha(p)
    report=dict(host=socket.gethostname(),rows=rows,contexts=contexts,coverage=coverage,input_sha256=inputs,state_files_sha256=state_files,source_sha256=sources,
                source_study_sha256=sha(a.source/'study/analysis.json'),baseline_manifest_sha256=sha(a.baseline/'source_manifest.json'),protocol_sha256=sha(Path(__file__).with_name('DICTIONARY_PROTOCOL.md')),
                propagation_library_sha256=sha(Path(os.environ['MOBI_PROPAGATE_LIBRARY'])),scope='7560 additional inter-message-dictionary saved-source modeled paid FIFO rows; warm initialized facts, no fresh CARLA/actual wireless/WCET/physical safety/driving/novelty claim.')
    assert len(rows)==7560 and len(coverage)==378;(a.out/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
