#!/usr/bin/env python3
import argparse,csv,hashlib,json,math,socket,time
from pathlib import Path
import numpy as np
import policy_proof as pp
from tube import Policy
from renew_policy import renew
from strict_policy import verify,conditional_stop_gate


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--reference',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False);(a.out/'packets').mkdir();rows=[];inputs={};templates={}
    frames={r['id']:r for r in csv.DictReader((a.capture/'frames.csv').open())}
    profiles=dict(small=pp.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=pp.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.))
    policy=Policy();contract=pp.Contract()
    for ordinal,path in enumerate(sorted((a.capture/'clouds').glob('*.npz'))):
        density,layout,scenario,step=path.stem.split('_')
        if scenario=='free' and step=='00':continue
        inputs[path.name]=hashlib.sha256(path.read_bytes()).hexdigest();data=np.load(path)
        origin=data['origin'];q=data['query'];lat=origin[:2]-q;yaw=math.atan2(-lat[0],lat[1])
        scope=pp.Scope('policy-renew:'+density+':'+layout+':'+scenario,'Town10HD_Opt/world',tuple(q),float(data['probe_z']));stamp=2.+ordinal*.05
        for speed in [0.,.5,1.]:
          for horizon in [.2,.3,.4]:
            name='%s_%s_free_00_v%s_h%s.json'%(density,layout,speed,horizon);template=a.reference/'packets'/name
            blob=template.read_bytes() if template.exists() else None
            if blob:templates[name]=hashlib.sha256(blob).hexdigest()
            outputs={};times={};order=[False,True] if len(rows)%2 else [True,False]
            for fast in order:
                begin=time.perf_counter();outputs[fast]=renew(blob,data['xyz'],origin,stamp,stamp,profiles,scope,contract,policy,speed,yaw,horizon,ordinal+1,fast) if blob else None;times[fast]=(time.perf_counter()-begin)*1000
            fresh=outputs[True];begin=time.perf_counter();valid=bool(fresh and verify(fresh,profiles,scope,contract,policy,speed,yaw,stamp+.02));receiver_ms=(time.perf_counter()-begin)*1000
            acq=float(frames[path.stem]['acquisition_ms']);age=(acq+times[True]+receiver_ms)/1000+.02
            full_age=(acq+times[False]+receiver_ms)/1000+.02
            gate=lambda dt:bool(fresh and conditional_stop_gate(fresh,profiles,scope,contract,policy,speed,yaw,stamp+dt))
            identifier='%s_v%s_h%s'%(path.stem,speed,horizon)
            if fresh:(a.out/'packets'/(identifier+'.json')).write_bytes(fresh)
            rows.append(dict(id=identifier,cloud=path.stem,reference=stamp,speed=speed,horizon=horizon,yaw=yaw,template_available=blob is not None,byte_equal=outputs[False]==fresh,geometry=valid,fast_first=order[0],full_ms=times[False],fast_ms=times[True],receiver_ms=receiver_ms,acquisition_ms=acq,age_s=age,full_age_s=full_age,fast_conditional_stop=gate(age),full_conditional_stop=bool(outputs[False]==fresh and gate(full_age)),physical_movement_authorized=False,packet_bytes=len(fresh) if fresh else 0))
        if ordinal%10==0:print(json.dumps(dict(frame=ordinal,trials=len(rows))),flush=True)
    with (a.out/'renewal.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    src=Path(__file__).parent;names=['tube.py','policy_proof.py','strict_policy.py','renew_policy.py','run_renewal.py']
    manifest=dict(host=socket.gethostname(),trials=len(rows),source_sha256={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in names},input_sha256=inputs,template_sha256=templates,frames_sha256=hashlib.sha256((a.capture/'frames.csv').read_bytes()).hexdigest(),protocol_sha256=hashlib.sha256((src/'RENEWAL_PROTOCOL.md').read_bytes()).hexdigest(),scope='Static current-ray replay; hypothetical ego speed and 20 ms link; historical acquisition timing; physical contracts unvalidated; no movement authorization.')
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:sum(r[k] for r in rows) for k in ['template_available','byte_equal','geometry','fast_conditional_stop','full_conditional_stop','physical_movement_authorized']}),flush=True)


if __name__=='__main__':main()
