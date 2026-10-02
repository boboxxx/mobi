#!/usr/bin/env python3
import argparse,gzip,hashlib,json,math,os,socket,sys,time
from pathlib import Path
import numpy as np
import compact
body=compact.body


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(exist_ok=False);(a.out/'packets').mkdir();(a.out/'states').mkdir()
    assert all(os.environ.get(n)=='1' for n in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'])
    compact.library();compact.observer.library();compact.stream.library()
    root=Path(__file__).resolve().parents[2]
    for f,h in json.loads((a.baseline/'source_manifest.json').read_bytes())['source_sha256'].items():assert sha(root/f)==h,f
    previous=json.loads((a.baseline/'study/analysis.json').read_bytes());pipeline=json.loads((a.source/'study/analysis.json').read_bytes())
    profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=body.Contract();windows=dict(small=9.,vehicle=11.5)
    rng=np.random.default_rng(20261007);rows=[];contexts=[];inputs={}
    for ctx in previous['contexts']:
        name=ctx['run'];run=a.capture/name;record=json.loads(gzip.decompress((run/'record.json.gz').read_bytes()));decisions={d['id']:d for d in record['decisions']}
        legacy=compact.base.LegacyReceiver(profiles,contract,name,'Carla/Maps/Town10HD_Opt')
        receivers=dict(fixed_K=compact.FixedReceiver(profiles,contract),coarse_set=compact.PositionReceiver(profiles,contract,windows,1),fine_set=compact.PositionReceiver(profiles,contract,windows,2));t=time.perf_counter()
        for identity in ctx['prefix_ids']:
            d=decisions[identity];blob=(run/'packets'/(identity+'.json')).read_bytes();b=json.loads(blob)
            scope=body.Scope(name,legacy.frame_id,tuple(d['query']),b['raw']['payload']['scope']['plane_z']);motion=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
            assert legacy.accept(blob,scope,motion,d['receiver_check_time'])
            for rx in receivers.values():anchor=rx.register(legacy,blob,scope,motion)
        setup=(time.perf_counter()-t)*1000;assert anchor.identity==ctx['anchor']['identity'];contexts.append(dict(run=name,prefix_ids=ctx['prefix_ids'],anchor=body.asdict(anchor),setup_ms=setup))
        for method in ['coarse_set','fine_set']:np.savez_compressed(a.out/'states'/(name+'_root_'+method+'.npz'),**receivers[method]._states[anchor.identity].possible)
        for identity in ['drive_025','drive_039']:
            d=decisions[identity];ids=['drive_%03d'%i for i in range(20,d['index']+1)];paths=[a.source/'study/source'/(name+'_'+x+'.json') for x in ids];steps=[json.loads(p.read_bytes()) for p in paths]
            for p in paths:inputs[str(p)]=sha(p)
            ref=math.ceil(d['stamp']*1e6)
            for repeat in range(3):
                m=[x for x in pipeline['maintenance'] if x['run']==name and x['repeat']==repeat and x['id'] in ids];ready=m[-1]['finish_us'];order=rng.permutation(list(receivers)).tolist()
                for method in order:
                    t=time.perf_counter();reason=None;packet=None;end,previous_ref,seq=anchor.endpoint_us,anchor.reference_us,anchor.sequence
                    if method=='fixed_K':
                        for raw in steps:
                            p=raw['payload']
                            if not previous_ref<p['reference_us']<end or p['sequence']<=seq or p['reference_us']+p['horizon_us']<=end:reason='no_temporal_cover';break
                            previous_ref,end,seq=p['reference_us'],p['reference_us']+p['horizon_us'],p['sequence']
                    if reason is None:packet=compact.encode(dict(kind='center-continuity-v1' if method=='fixed_K' else 'position-observations-v1',dynamics='observation-speed-age-v1',anchor=anchor.identity,steps=steps))
                    assembly=(time.perf_counter()-t)*1000;verify=0.;decision=None;state=None
                    if packet:
                        t=time.perf_counter()
                        if method=='fixed_K':decision=receivers[method].inspect(packet)
                        else:decision,state=receivers[method].rebuild(packet)
                        verify=(time.perf_counter()-t)*1000
                    h=decision['horizon_us'] if decision else 0;wire=20+(len(packet)*8/20_000 if packet else 0);total=(ready-ref)/1000+assembly+verify+wire;age=max(50000,math.ceil(total/50)*50000)
                    row=dict(run=name,id=identity,repeat=repeat,method=method,order=order,source_ids=ids,ready_us=ready,charged_source_work_ms=sum(x['generation_ms'] for x in m),
                             assembly_ms=assembly,verification_ms=verify,bytes=len(packet) if packet else 0,wire_ms=wire,total_ms=total,age_us=age,horizon_us=h,
                             geometry=h>0,timely475=bool(h>=475000 and age+200000<475000),timely_max=bool(h>0 and age+200000<h),reason=reason,decision=decision)
                    rows.append(row);print(json.dumps(row),flush=True)
                    if packet and repeat==0:(a.out/'packets'/(name+'_'+identity+'_'+method+'.bin')).write_bytes(packet)
                    if state and repeat==0:np.savez_compressed(a.out/'states'/(name+'_'+identity+'_'+method+'.npz'),**state.possible)
    sources={}
    for mod in list(sys.modules.values()):
        f=getattr(mod,'__file__',None)
        if f:
            p=Path(f).resolve()
            if root in p.parents and p.is_file() and p.suffix=='.py':sources[str(p.relative_to(root))]=sha(p)
    report=dict(host=socket.gethostname(),rows=rows,contexts=contexts,input_sha256=inputs,source_sha256=sources,
                source_study_sha256=sha(a.source/'study/analysis.json'),baseline_manifest_sha256=sha(a.baseline/'source_manifest.json'),protocol_sha256=sha(Path(__file__).with_name('PROTOCOL.md')),
                propagation_library_sha256=sha(Path(os.environ['MOBI_PROPAGATE_LIBRARY'])),scope='108 finite saved-source calls, common exact transport/cache, conservative local-grid observers. Same prior charged FIFO inputs, all new cost paid; no new CARLA/control/wireless or novelty claim.')
    assert len(rows)==108 and len(contexts)==6;(a.out/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
