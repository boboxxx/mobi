#!/usr/bin/env python3
import argparse,gzip,hashlib,json,math,os,socket,time
from pathlib import Path
import numpy as np
import observer,refined


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(exist_ok=False);(a.out/'packets').mkdir();(a.out/'states').mkdir()
    body=observer.body;prior=json.loads((a.source/'study/analysis.json').read_bytes());baseline=json.loads(a.baseline.read_bytes())
    profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=body.Contract();rows=[]
    assert all(os.environ.get(n)=='1' for n in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'])
    for ctx in baseline['contexts']:
        name=ctx['run'];run=a.capture/name;record=json.loads(gzip.decompress((run/'record.json.gz').read_bytes()));decisions={x['id']:x for x in record['decisions']}
        old=observer.base.LegacyReceiver(profiles,contract,name,'Carla/Maps/Town10HD_Opt');rx=refined.Receiver(profiles,contract);t=time.perf_counter()
        for identity in ctx['prefix_ids']:
            d=decisions[identity];blob=(run/'packets'/(identity+'.json')).read_bytes();b=json.loads(blob)
            scope=body.Scope(name,old.frame_id,tuple(d['query']),b['raw']['payload']['scope']['plane_z']);motion=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
            assert old.accept(blob,scope,motion,d['receiver_check_time']);anchor=rx.register(old,blob,scope,motion)
        setup_ms=(time.perf_counter()-t)*1000;assert anchor.identity==ctx['anchor']['identity']
        np.savez_compressed(a.out/'states'/(name+'_root.npz'),**rx._states[anchor.identity].possible)
        for identity in ['drive_025','drive_039']:
            d=decisions[identity];ids=['drive_%03d'%i for i in range(20,d['index']+1)]
            source_paths=[a.source/'study/source'/(name+'_'+x+'.json') for x in ids]
            steps=[json.loads(p.read_bytes()) for p in source_paths];ref=math.ceil(d['stamp']*1e6)
            m=[x for x in prior['maintenance'] if x['run']==name and x['repeat']==0 and x['id'] in ids]
            ready=m[-1]['finish_us'];t=time.perf_counter();packet=observer.wire(anchor,steps);assert packet;assembly=(time.perf_counter()-t)*1000
            t=time.perf_counter();decision,state=rx.rebuild(packet);verify=(time.perf_counter()-t)*1000
            wire_ms=20+len(packet)*8/20_000;total=(ready-ref)/1000+assembly+verify+wire_ms;age=max(50000,math.ceil(total/50)*50000);h=decision['horizon_us']
            row=dict(run=name,id=identity,source_ids=ids,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
                     ready_us=ready,charged_source_work_ms=sum(x['generation_ms'] for x in m),setup_ms=setup_ms,grid_factor=2,
                     assembly_ms=assembly,verification_ms=verify,wire_ms=wire_ms,total_ms=total,age_us=age,
                     bytes=len(packet),raw_bytes=len(observer.stream.decode(packet)),horizon_us=h,geometry=h>0,horizon475_pass=h>=475000,
                     timely475=bool(h>=475000 and age+200000<475000),timely_max=bool(h>0 and age+200000<h),decision=decision)
            rows.append(row);print(json.dumps(row),flush=True)
            (a.out/'packets'/(name+'_'+identity+'.bin')).write_bytes(packet);np.savez_compressed(a.out/'states'/(name+'_'+identity+'.npz'),**state.possible)
    assert len(rows)==12
    modules=[Path(observer.__file__),Path(refined.__file__),Path(__file__).resolve()];root=Path(__file__).resolve().parents[2]
    result=dict(host=socket.gethostname(),rows=rows,baseline_sha256=hashlib.sha256(a.baseline.read_bytes()).hexdigest(),source_study_sha256=hashlib.sha256((a.source/'study/analysis.json').read_bytes()).hexdigest(),
                loaded_additional_sources={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in modules},
                protocol_sha256=hashlib.sha256(Path(__file__).with_name('REFINEMENT_PROTOCOL.md').read_bytes()).hexdigest(),
                scope='Post-baseline one factor2 sensitivity on all12 targets; same physical metadata/raw sources/charged sender work; full new receiver cost; no new held-out evaluation or timely advantage claim.')
    (a.out/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
