#!/usr/bin/env python3
import argparse,csv,hashlib,json,socket,time,sys
from pathlib import Path
import numpy as np
from body import *
from run_study import write
from stopping import admit
from compress import pack


def profiles():
    return dict(small=Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    (a.out/'packets').mkdir();rows=[];p=profiles();c=Contract();sources={}
    for path in sorted((a.capture/'clouds').glob('*_00.npz')):
        data=np.load(path);sources[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
        origin=data['origin'];q=data['query'];lateral=origin[:2]-q;yaw=math.atan2(-lateral[0],lateral[1])
        scope=Scope('body-probe:'+path.stem,'Town10HD_Opt/world',tuple(q),float(data['probe_z']))
        o,r,ref=encode_source(data['xyz'],origin,1.,1.);res=projections(o,r,ref,p,scope,c)
        for speed in [0.,.5,1.]:
          m=Motion(acceleration=8.,vx=speed*math.cos(yaw),vy=speed*math.sin(yaw),yaw=yaw)
          for horizon in [.2,.4,.6]:
            for seeded in [False,True]:
                prior=Region(tuple(q),yaw,(-m.half_length,-m.half_width),(m.half_length,m.half_width),0.,1.,1.,'explicit-initial-condition',scope.episode) if seeded else None
                begin=time.perf_counter();direct=all(coverage(res[n],pr,scope,m,horizon,prior,1.)[0] for n,pr in p.items());direct_ms=(time.perf_counter()-begin)*1000
                begin=time.perf_counter();blob=pack(data['xyz'],origin,1.,1.,p,scope,c,m,prior,horizon);source_ms=(time.perf_counter()-begin)*1000
                begin=time.perf_counter();valid=bool(blob and verify(blob,p,scope,c,m,prior,1.02,0));receiver_ms=(time.perf_counter()-begin)*1000
                identifier='%s_v%s_h%s_prior%s'%(path.stem,speed,horizon,int(seeded))
                if blob:(a.out/'packets'/(identifier+'.json')).write_bytes(blob)
                age=(source_ms+receiver_ms)/1000+.02;action=action_duration(speed,age)
                admitted=bool(blob and admit(blob,p,scope,c,m,prior,1.+age))
                rows.append(dict(id=identifier,cloud=path.stem,speed=speed,horizon=horizon,bootstrap=seeded,direct_coverage=direct,packet_valid=valid,compression_failure=direct and not valid,packet_bytes=len(blob) if blob else 0,direct_ms=direct_ms,source_ms=source_ms,receiver_ms=receiver_ms,modeled_age_without_acquisition=age,action_to_stop_s=action,gate_without_acquisition=admitted))
        print(json.dumps(dict(cloud=path.stem,rows=len(rows))),flush=True)
    write(a.out/'probe.csv',rows)
    manifest=dict(host=socket.gethostname(),trials=len(rows),direct=sum(x['direct_coverage'] for x in rows),packet_valid=sum(x['packet_valid'] for x in rows),compression_failures=sum(x['compression_failure'] for x in rows),gate_without_acquisition=sum(x['gate_without_acquisition'] for x in rows),source_sha256={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['body.py','test_body.py','stopping.py','test_stopping.py','compress.py','test_compress.py','run_braking_probe.py']},protocol_sha256=hashlib.sha256(Path(__file__).with_name('BRAKING_FOLLOWUP.md').read_bytes()).hexdigest(),input_sha256=sources,scope='Corrected braking contract; static no-ego replay of full-body envelope; explicit bootstrap optional; link/braking contracts stipulated; acquisition excluded from gate diagnostic.')
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)


if __name__=='__main__':main()
