#!/usr/bin/env python3
import argparse,csv,hashlib,json,math,socket,time
from pathlib import Path
import numpy as np
import policy_proof as pp
import body
from tube import Policy,policy_limits


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False);(a.out/'packets').mkdir();rows=[];inputs={}
    profiles=dict(small=pp.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=pp.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.))
    policy=Policy();contract=pp.Contract()
    for path in sorted((a.capture/'clouds').glob('*_00.npz')):
        inputs[path.name]=hashlib.sha256(path.read_bytes()).hexdigest();data=np.load(path)
        origin=data['origin'];q=data['query'];lateral=origin[:2]-q;yaw=math.atan2(-lateral[0],lateral[1])
        scope=pp.Scope('policy-probe:'+path.stem,'Town10HD_Opt/world',tuple(q),float(data['probe_z']))
        o,r,ref=pp.encode_source(data['xyz'],origin,1.,1.);res=pp.projections(o,r,ref,profiles,scope,contract)
        for speed in [0.,.5,1.]:
          motion=body.Motion(acceleration=8.,vx=speed*math.cos(yaw),vy=speed*math.sin(yaw),yaw=yaw)
          for horizon in [.2,.3,.4,.5,.6]:
            old=all(body.coverage(res[n],pr,scope,motion,horizon,None,1.)[0] for n,pr in profiles.items())
            direct=all(pp.coverage(res[n],pr,policy,speed,yaw,horizon)[0] for n,pr in profiles.items())
            begin=time.perf_counter();blob=pp.pack(data['xyz'],origin,1.,1.,profiles,scope,contract,policy,speed,yaw,horizon) if direct else None;generation=(time.perf_counter()-begin)*1000
            begin=time.perf_counter();verified=bool(blob and pp.verify(blob,profiles,scope,contract,policy,speed,yaw,1.02));verification=(time.perf_counter()-begin)*1000
            age=(generation+verification)/1000+.02;identifier='%s_v%s_h%s'%(path.stem,speed,horizon)
            if blob:(a.out/'packets'/(identifier+'.json')).write_bytes(blob)
            gate=lambda dt:bool(blob and pp.conditional_stop_gate(blob,profiles,scope,contract,policy,speed,yaw,1.+dt))
            rows.append(dict(id=identifier,cloud=path.stem,speed=speed,horizon=horizon,yaw=yaw,arbitrary_geometry=old,policy_geometry=direct,packet_verified=verified,packet_bytes=len(blob) if blob else 0,generation_ms=generation,verification_ms=verification,modeled_age_without_acquisition=age,minimum_age_gate=gate(.02),measured_compute_gate=gate(age),with_50ms_acquisition_gate=gate(age+.05),physical_movement_authorized=False,policy_completion_at_hold_budget=policy_limits(speed,policy.hold_budget,policy)[1]))
        print(json.dumps(dict(cloud=path.stem,trials=len(rows))),flush=True)
    with (a.out/'geometry.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    src=Path(__file__).parent
    manifest=dict(host=socket.gethostname(),trials=len(rows),input_sha256=inputs,source_sha256={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in ['tube.py','test_tube.py','policy_proof.py','run_geometry.py']},protocol_sha256=hashlib.sha256((src/'GEOMETRY_PROTOCOL.md').read_bytes()).hexdigest(),scope='Conditional static geometry; stipulated hypothetical speed and physical contracts; no bootstrap, no action, no measured communication link.')
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({name:sum(r[name] for r in rows) for name in ['arbitrary_geometry','policy_geometry','packet_verified','minimum_age_gate','measured_compute_gate','with_50ms_acquisition_gate','physical_movement_authorized']}),flush=True)


if __name__=='__main__':main()
