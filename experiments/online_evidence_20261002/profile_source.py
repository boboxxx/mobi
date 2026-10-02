#!/usr/bin/env python3
import argparse,cProfile,gzip,hashlib,io,json,math,os,pstats,socket,sys,time
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'evidence_loop_20261001'))
from fast_path import body,Receiver
from repair_renew import renew
from compress import pack

SELECT={'view0_repair_r1':{'root_000','root_001','warm_000','warm_001'},'view1_repair_r0':{'root_000'},'view0_original_r0':{'warm_000'}}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--mode',required=True);a=ap.parse_args();a.out.mkdir(exist_ok=False)
    profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));c=body.Contract();rows=[]
    for name,ids in SELECT.items():
        run=a.capture/name;r=json.loads(gzip.decompress((run/'record.json.gz').read_bytes()));rx=Receiver(profiles,c,name,'Carla/Maps/Town10HD_Opt');template=None
        for d in r['decisions']:
            cl=np.load(run/'clouds'/(d['id']+'.npz'));s=body.Scope(name,'Carla/Maps/Town10HD_Opt',tuple(d['query']),float(cl['plane_z']));m=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
            prior=rx.latest_region()
            if prior and not (prior.established<=d['stamp'] and math.ceil(d['stamp']*1e6)<rx._deadlines[prior.identity]):prior=None
            assert (prior.identity if prior else None)==d['prior']
            old=(run/'packets'/(d['id']+'.json')).read_bytes() if d['geometry'] else None
            if d['id'] in ids:
                def generate():
                    args=(cl['xyz'],cl['origin'],d['stamp'],d['stamp'],profiles,s,c,m,prior)
                    blob=renew(template,*args,.4,d['sequence']) if template else None
                    return blob if blob else pack(*args,.4,d['sequence'])
                for repeat in range(4):
                    begin=time.perf_counter();blob=generate();source_ms=(time.perf_counter()-begin)*1000
                    begin=time.perf_counter();accepted=bool(blob and body.verify(blob,profiles,s,c,m,prior,d['stamp']+.02,0));verify_ms=(time.perf_counter()-begin)*1000
                    assert blob==old and bool(blob)==accepted
                    row=dict(run=name,id=d['id'],repeat=repeat,source_ms=source_ms,verify_ms=verify_ms,geometry=accepted,packet_bytes=len(blob) if blob else 0);rows.append(row);print(json.dumps(row),flush=True)
                if name=='view0_repair_r1' and d['id'] in ['root_001','warm_001']:
                    profiler=cProfile.Profile();profiler.enable();generate();profiler.disable();stream=io.StringIO();pstats.Stats(profiler,stream=stream).sort_stats('cumtime').print_stats(30);(a.out/(d['id']+'_profile.txt')).write_text(stream.getvalue())
            if old:template=old
            if d['receiver_accepted']:assert rx.accept(old,s,m,d['receiver_check_time'])
    cfg=io.StringIO()
    import contextlib
    with contextlib.redirect_stdout(cfg):np.show_config()
    (a.out/'numpy_config.txt').write_text(cfg.getvalue())
    report=dict(host=socket.gethostname(),mode=a.mode,rows=rows,thread_environment={n:os.environ.get(n) for n in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']},source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Selected post-analysis fixed archived states; no new scenario or WCET claim.')
    (a.out/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
