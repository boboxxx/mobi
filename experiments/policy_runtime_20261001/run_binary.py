#!/usr/bin/env python3
import argparse,csv,hashlib,json,math,socket,time
from pathlib import Path
import numpy as np
from incremental import pp,Verifier,timing_after_verified
from local_renew import Renewer
from binary_renew import BinaryRenewer
from binary_proof import BinaryVerifier,decode as binary_decode,timing_after_verified as binary_timing
from strict_policy import verify as reference_verify


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--reference',type=Path,required=True);ap.add_argument('--templates',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False);(a.out/'packets').mkdir();rows=[];inputs={};templates={}
    modes={'json_combined':(True,True),'binary_full':(False,False),'binary_combined':(True,True)}
    source={name:(BinaryRenewer if name.startswith('binary') else Renewer)(*settings) for name,settings in modes.items()};receiver={name:(BinaryVerifier(hints=modes[name][1]) if name.startswith('binary') else Verifier()) for name in modes}
    profiles=dict(small=pp.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=pp.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));policy=pp.Policy();contract=pp.Contract()
    frames={r['id']:r for r in csv.DictReader((a.capture/'frames.csv').open())}
    old={r['id']:r for r in csv.DictReader((a.reference/'renewal.csv').open())};trial=0
    for ordinal,path in enumerate(sorted((a.capture/'clouds').glob('*.npz'))):
        density,layout,scenario,step=path.stem.split('_')
        if scenario=='free' and step=='00':continue
        inputs[path.name]=hashlib.sha256(path.read_bytes()).hexdigest();d=np.load(path);q=d['query'];origin=d['origin'];lat=origin[:2]-q;yaw=math.atan2(-lat[0],lat[1]);stamp=2.+ordinal*.05
        scope=pp.Scope('policy-renew:'+density+':'+layout+':'+scenario,'Town10HD_Opt/world',tuple(q),float(d['probe_z']))
        for speed in [0.,.5,1.]:
          for horizon in [.2,.3,.4]:
            identifier='%s_v%s_h%s'%(path.stem,speed,horizon);assert identifier in old
            name='%s_%s_free_00_v%s_h%s.json'%(density,layout,speed,horizon);template=a.templates/'packets'/name;blob=template.read_bytes() if template.exists() else None
            if blob:templates[name]=hashlib.sha256(blob).hexdigest()
            expected_path=a.reference/'packets'/(identifier+'.json');expected=expected_path.read_bytes() if expected_path.exists() else None
            order=list(modes);order=order[trial%3:]+order[:trial%3]
            for position,mode in enumerate(order):
                begin=time.perf_counter();fresh=source[mode].renew(blob,d['xyz'],origin,stamp,stamp,profiles,scope,contract,policy,speed,yaw,horizon,ordinal+1) if blob else None;generation=(time.perf_counter()-begin)*1000
                begin=time.perf_counter();check=receiver[mode].verify
                valid=bool(fresh and check(fresh,profiles,scope,contract,policy,speed,yaw,stamp+.02));verification=(time.perf_counter()-begin)*1000
                timing=binary_timing if mode.startswith('binary') else timing_after_verified
                acq=float(frames[path.stem]['acquisition_ms']);age=(acq+generation+verification)/1000+.02
                begin=time.perf_counter();initial=bool(valid and timing(fresh,policy,speed,stamp+age));bookkeeping=(time.perf_counter()-begin)*1000
                age+=bookkeeping/1000
                timely=bool(valid and timing(fresh,policy,speed,stamp+age));guarded=bool(valid and timing(fresh,policy,speed,stamp+age+.001))
                equal=fresh==expected
                if mode.startswith('binary') and fresh is not None:
                    equal=False
                    if expected is not None:
                        p,o,r=binary_decode(fresh,profiles,scope,contract,policy,speed,yaw)
                        oldp,oldo,oldr=pp.decode(pp.canonical(json.loads(expected)['raw']),profiles,scope,contract)
                        equal=np.array_equal(o,oldo) and np.array_equal(r,oldr) and all(p[k]==oldp[k] for k in ['reference_us','horizon_us','sequence'])
                    if mode=='binary_combined':(a.out/'packets'/(identifier+'.pvx')).write_bytes(fresh)
                rows.append(dict(id=identifier,cloud=path.stem,reference=stamp,speed=speed,horizon=horizon,mode=mode,order=position,template_available=blob is not None,geometry=valid,semantic_equal=bool(equal),packet_bytes=len(fresh) if fresh else 0,packet_sha256=hashlib.sha256(fresh).hexdigest() if fresh else '',generation_ms=generation,verification_ms=verification,bookkeeping_ms=bookkeeping,acquisition_ms=acq,age_s=age,conditional_stop=timely,plus_1ms_conditional_stop=guarded,physical_movement_authorized=False))
            trial+=1
        if ordinal%10==0:print(json.dumps(dict(frame=ordinal,cases=trial,rows=len(rows))),flush=True)
    with (a.out/'ablation.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    manifest=dict(host=socket.gethostname(),cases=trial,rows=len(rows),source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')},protocol_sha256=hashlib.sha256(Path(__file__).with_name('BINARY_PROTOCOL.md').read_bytes()).hexdigest(),input_sha256=inputs,template_sha256=templates,frames_sha256=hashlib.sha256((a.capture/'frames.csv').read_bytes()).hexdigest(),reference_csv_sha256=hashlib.sha256((a.reference/'renewal.csv').read_bytes()).hexdigest(),counts={name:dict(local=source[name].local_hits,fallback=source[name].fallbacks) for name in modes},scope='Lossless binary transport and runtime follow-up on repeated static saved scans; unchanged unvalidated physical contracts; no movement authorization.')
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({name:{key:sum(r[key] for r in rows if r['mode']==name) for key in ['geometry','semantic_equal','conditional_stop','plus_1ms_conditional_stop']} for name in modes}),flush=True)


if __name__=='__main__':main()
