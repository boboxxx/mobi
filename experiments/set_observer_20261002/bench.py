#!/usr/bin/env python3
import argparse,gzip,hashlib,json,math,os,socket,sys,time
from pathlib import Path
import numpy as np
import observer


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(exist_ok=False);(a.out/'packets').mkdir();(a.out/'states').mkdir()
    body=observer.body;stream=observer.stream
    assert all(os.environ.get(n)=='1' for n in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'])
    t=time.perf_counter();observer.library();stream.library();load_ms=(time.perf_counter()-t)*1000
    profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=body.Contract()
    prior=json.loads((a.source/'study/analysis.json').read_bytes());inputs={};rows=[];contexts=[];rng=np.random.default_rng(20261006)
    root=Path(__file__).resolve().parents[2]
    for f,h in json.loads((a.source/'source_manifest.json').read_bytes())['source_sha256'].items():assert hashlib.sha256((root/f).read_bytes()).hexdigest()==h,f
    def read(p):
        b=p.read_bytes();inputs[str(p)]=hashlib.sha256(b).hexdigest();return b
    read(a.source/'study/analysis.json');read(a.source/'source_manifest.json')
    for ctx in prior['contexts']:
        name=ctx['run'];run=a.capture/name;record=json.loads(gzip.decompress(read(run/'record.json.gz')));decisions={d['id']:d for d in record['decisions']}
        legacy=observer.base.LegacyReceiver(profiles,contract,name,'Carla/Maps/Town10HD_Opt')
        rx=observer.Receiver(profiles,contract);fixed=stream.Receiver(profiles,contract);t=time.perf_counter()
        for identity in ctx['prefix_ids']:
            d=decisions[identity];blob=read(run/'packets'/(identity+'.json'));b=json.loads(blob)
            scope=body.Scope(name,legacy.frame_id,tuple(d['query']),b['raw']['payload']['scope']['plane_z'])
            motion=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
            assert legacy.accept(blob,scope,motion,d['receiver_check_time'])
            anchor=rx.register(legacy,blob,scope,motion);fixed.register(legacy,blob,scope,motion)
        setup_ms=(time.perf_counter()-t)*1000;assert anchor.identity==ctx['anchor']['identity']
        contexts.append(dict(run=name,prefix_ids=ctx['prefix_ids'],anchor=body.asdict(anchor),setup_ms=setup_ms))
        for identity in ['drive_025','drive_039']:
            d=decisions[identity];ref=math.ceil(d['stamp']*1e6)
            ids=['drive_%03d'%i for i in range(20,d['index']+1)]
            steps=[json.loads(read(a.source/'study/source'/(name+'_'+x+'.json'))) for x in ids]
            for repeat in range(3):
                maintenance=[z for z in prior['maintenance'] if z['run']==name and z['repeat']==repeat and z['id'] in ids]
                ready=maintenance[-1]['finish_us'];work=sum(z['generation_ms'] for z in maintenance)
                order=rng.permutation(['fixed_K','position_set']).tolist()
                for method in order:
                    t=time.perf_counter();packet=None;reason=None
                    if method=='fixed_K':
                        end,previous,seq=anchor.endpoint_us,anchor.reference_us,anchor.sequence
                        for raw in steps:
                            p=raw['payload']
                            if not previous<p['reference_us']<end or p['sequence']<=seq or p['reference_us']+p['horizon_us']<=end:reason='no_temporal_cover';break
                            previous,end,seq=p['reference_us'],p['reference_us']+p['horizon_us'],p['sequence']
                        if reason is None:
                            blob=observer.base.wire(anchor,steps)
                            if blob:packet=stream.encode(blob)
                            else:reason='bundle_cap'
                    else:
                        packet=observer.wire(anchor,steps)
                        if not packet:reason='bundle_cap'
                    assembly=(time.perf_counter()-t)*1000;verify=0.;decision=None;state=None
                    if packet:
                        t=time.perf_counter()
                        if method=='fixed_K':decision=fixed.inspect(packet);decision['horizon_us']=decision['endpoint_us']-decision['reference_us']
                        else:decision,state=rx.rebuild(packet)
                        verify=(time.perf_counter()-t)*1000
                    h=decision['horizon_us'] if decision else 0;wire_ms=20+(len(packet)*8/20_000 if packet else 0)
                    total=(ready-ref)/1000+assembly+verify+wire_ms;age=max(50_000,math.ceil(total/50)*50_000)
                    row=dict(run=name,id=identity,repeat=repeat,method=method,order=order,source_ids=ids,
                             ready_us=ready,charged_source_work_ms=work,assembly_ms=assembly,verification_ms=verify,
                             bytes=len(packet) if packet else 0,raw_bytes=len(stream.decode(packet)) if packet else 0,
                             wire_ms=wire_ms,total_ms=total,age_us=age,horizon_us=h,geometry=h>0,
                             horizon475_pass=h>=475_000,timely475=bool(h>=475_000 and age+200_000<475_000),
                             timely_max=bool(h>0 and age+200_000<h),action_slack_us=h-age-200_000 if h>0 else None,
                             reason=reason,decision=decision)
                    rows.append(row);print(json.dumps(row),flush=True)
                    if packet and repeat==0:(a.out/'packets'/(name+'_'+identity+'_'+method+'.bin')).write_bytes(packet)
                    if state and repeat==0:
                        np.savez_compressed(a.out/'states'/(name+'_'+identity+'.npz'),**state.possible)
        # Observer root masks are checkpointed for independent initialization.
        np.savez_compressed(a.out/'states'/(name+'_root.npz'),**rx._states[anchor.identity].possible)
    assert len(rows)==72 and len(contexts)==6
    sources={}
    for m in list(sys.modules.values()):
        f=getattr(m,'__file__',None)
        if f:
            p=Path(f).resolve()
            if root in p.parents and p.is_file() and p.suffix=='.py':sources[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
    report=dict(host=socket.gethostname(),rows=rows,contexts=contexts,source_sha256=sources,input_sha256=inputs,
                library_sha256=hashlib.sha256(Path(os.environ['MOBI_MASK_LIBRARY']).read_bytes()).hexdigest(),library_load_ms=load_ms,
                source_study_sha256=hashlib.sha256((a.source/'study/analysis.json').read_bytes()).hexdigest(),
                protocol_sha256=hashlib.sha256(Path(__file__).with_name('PROTOCOL.md').read_bytes()).hexdigest(),
                scope='Same available saved source steps and charged prior sender pipeline; position-set versus fixed-K; all new receiver cost measured. Fixed region, retrospective/common-clock/persistent conditional model, no novel theory/actual control claim.')
    (a.out/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
