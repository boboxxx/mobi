#!/usr/bin/env python3
"""Finite joint proof, serialization and current-source renewal on sheng."""
import argparse,csv,hashlib,json,socket,time,zlib
from pathlib import Path
import numpy as np
from proof import Contract,Scope,Profile,pack,renew,verify,serialize,encode_source,TIME_SCALE
from run_study import write


def profiles():
    return dict(small_core=Profile(r_min=.2,r_max=.4,step=.05,error=0.),
                vehicle_core=Profile(r_min=.55,r_max=2.5,step=.1,error=0.))


def setup(data,cloud_id,box,period,reference):
    density,layout,_,_=cloud_id.split('_')
    scope=Scope('raw-ray-v2:'+density+':'+layout,'Town10HD_Opt/world',tuple(data['query']),float(data['probe_z']))
    contract=Contract(box,box,box)
    angle=np.arctan2(data['xyz'][:,1]-data['origin'][1],data['xyz'][:,0]-data['origin'][0])
    ages=np.mod(-angle,2*np.pi)/(2*np.pi)*period
    return scope,contract,reference-ages


def name(cloud_id,box,period,mode):return '%s_e%s_t%s_%s'%(cloud_id,box,period,mode)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    for sub in ['cold_packets','renewed_packets']:(a.out/sub).mkdir()
    frame_rows={r['id']:r for r in csv.DictReader((a.capture/'frames.csv').open())}
    p=profiles();cold=[];warm=[];templates={};start=time.perf_counter()
    for cloud in sorted((a.capture/'clouds').glob('*_00.npz')):
        data=np.load(cloud)
        for box in [.002,.01]:
            for period in [0.,.02,.05]:
                scope,contract,observed=setup(data,cloud.stem,box,period,0.)
                o,r,ref=encode_source(data['xyz'],data['origin'],observed,0.)
                full=serialize(o,r,ref,p,scope,contract,.2,0)
                raw_bytes=len(zlib.compress(full,6))
                for mode in ['heterogeneous','uniform']:
                    begin=time.perf_counter();blob=pack(data['xyz'],data['origin'],observed,0.,p,scope,contract,sequence=0,mode=mode)
                    encode_ms=(time.perf_counter()-begin)*1000
                    begin=time.perf_counter();ok=bool(blob and verify(blob,p,scope,contract,.02,.05))
                    verify_ms=(time.perf_counter()-begin)*1000
                    age=float(frame_rows[cloud.stem]['acquisition_ms'])/1000+(encode_ms+verify_ms)/1000+.02
                    timely=bool(blob and verify(blob,p,scope,contract,age,.05))
                    identifier=name(cloud.stem,box,period,mode)
                    if blob:
                        (a.out/'cold_packets'/(identifier+'.json')).write_bytes(blob)
                        if '_free_' in cloud.stem:templates[(cloud.stem.split('_')[0],cloud.stem.split('_')[1],box,period,mode)]=blob
                    cold.append(dict(id=cloud.stem,input_box_m=box,period_s=period,mode=mode,reference_s=0.,
                                     geometry_verified=ok,timing_budget_passed=timely,packet_bytes=len(blob) if blob else 0,
                                     packet_zlib_bytes=len(zlib.compress(blob,6)) if blob else 0,full_ray_zlib_bytes=raw_bytes,
                                     encode_ms=encode_ms,verify_ms=verify_ms,total_modeled_age_s=age))
        print(json.dumps(dict(cold_cloud=cloud.stem)),flush=True)
    write(a.out/'cold.csv',cold)
    for ordinal,cloud in enumerate(sorted((a.capture/'clouds').glob('*.npz'))):
        density,layout,scenario,step=cloud.stem.split('_')
        if scenario=='free' and step=='00':continue
        data=np.load(cloud);reference=1.+ordinal*.05
        for box in [.002,.01]:
            for period in [0.,.02,.05]:
                scope,contract,observed=setup(data,cloud.stem,box,period,reference)
                for mode in ['heterogeneous','uniform']:
                    template=templates.get((density,layout,box,period,mode))
                    begin=time.perf_counter()
                    blob=renew(template,data['xyz'],data['origin'],observed,reference,p,scope,contract,ordinal+1,mode) if template else None
                    refresh_ms=(time.perf_counter()-begin)*1000
                    begin=time.perf_counter();ok=bool(blob and verify(blob,p,scope,contract,reference+.02,.05))
                    verify_ms=(time.perf_counter()-begin)*1000
                    age=float(frame_rows[cloud.stem]['acquisition_ms'])/1000+(refresh_ms+verify_ms)/1000+.02
                    timely=bool(blob and verify(blob,p,scope,contract,reference+age,.05))
                    expiration=(json.loads(blob)['payload']['reference_us']+json.loads(blob)['payload']['horizon_us'])/TIME_SCALE if blob else reference+.2
                    # Advance one time quantum past the encoded expiry to avoid
                    # treating integer timestamp rounding as stale acceptance.
                    expired=bool(blob and verify(blob,p,scope,contract,expiration+1/TIME_SCALE,0.))
                    identifier=name(cloud.stem,box,period,mode)
                    if blob:(a.out/'renewed_packets'/(identifier+'.json')).write_bytes(blob)
                    warm.append(dict(id=cloud.stem,input_box_m=box,period_s=period,mode=mode,reference_s=reference,
                                     template_available=template is not None,geometry_verified=ok,timing_budget_passed=timely,
                                     expired_accepted=expired,packet_bytes=len(blob) if blob else 0,
                                     packet_zlib_bytes=len(zlib.compress(blob,6)) if blob else 0,
                                     refresh_ms=refresh_ms,verify_ms=verify_ms,total_modeled_age_s=age))
        if step=='09':print(json.dumps(dict(renewed_cloud=cloud.stem)),flush=True)
    write(a.out/'renewal.csv',warm)
    manifest=dict(host=socket.gethostname(),cold_trials=len(cold),renewal_trials=len(warm),
                  cold_geometry=sum(r['geometry_verified'] for r in cold),cold_timing=sum(r['timing_budget_passed'] for r in cold),
                  renewal_geometry=sum(r['geometry_verified'] for r in warm),renewal_timing=sum(r['timing_budget_passed'] for r in warm),
                  near_accepted=sum('_near_' in r['id'] and r['geometry_verified'] for r in warm),expired_accepted=sum(r['expired_accepted'] for r in warm),
                  elapsed_s=time.perf_counter()-start,
                  source_sha256={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['proof.py','run_replay.py','test_proof.py']},
                  dependency_sha256={n:hashlib.sha256((Path(__file__).resolve().parents[1]/folder/n).read_bytes()).hexdigest()
                                     for folder,n in [('visibility_certificate_20261001','geometry.py'),('visibility_uncertainty_20261001','projection.py'),('visibility_certificate_20261001','run_study.py')]},
                  protocol_sha256=hashlib.sha256(Path(__file__).with_name('PROTOCOL.md').read_bytes()).hexdigest(),
                  input_sha256={c.name:hashlib.sha256(c.read_bytes()).hexdigest() for c in sorted((a.capture/'clouds').glob('*.npz'))},
                  scope='Static CARLA replay; source input boxes and rolling times are stipulated. Measured CPU/recorded acquisition plus modeled 20ms transport and 50ms action. No whole-vehicle driving claim.')
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)


if __name__=='__main__':main()
