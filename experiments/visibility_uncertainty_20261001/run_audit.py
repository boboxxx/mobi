#!/usr/bin/env python3
"""Finite, input-box and hypothetical rolling-scan audit on saved CARLA rays."""
import argparse, csv, hashlib, json, platform, socket, sys, time
from pathlib import Path
from dataclasses import replace
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'visibility_certificate_20261001'))
from geometry import Profile, certify
from run_study import CLASSES, write
from projection import bounded_witnesses, select_for_profile


def perturbations(out):
    rng = np.random.default_rng(20261011)
    rows = []
    for batch in range(100):
        p = rng.uniform(-300,300,(1000,3));p[:,2]=rng.uniform(-2,0,1000)
        o = rng.uniform(-300,300,(1000,3));o[:,2]=rng.uniform(2,12,1000)
        q = np.array([150.,-150.]);e=.02;z=.6
        result = bounded_witnesses(p,o,q,z,e,e,e)
        pt = p+rng.uniform(-e,e,p.shape);ot=o+rng.uniform(-e,e,o.shape);qt=q+rng.uniform(-e,e,2)
        t=(ot[:,2]-z)/(ot[:,2]-pt[:,2]);truth=(1-t[:,None])*ot[:,:2]+t[:,None]*pt[:,:2]-qt
        distance=np.linalg.norm(truth-result['witnesses'],axis=1)
        rows.append(dict(batch=batch,draws=len(p),violations=int(np.sum(distance>result['projection_error'])),
                         largest_error_to_bound=float(np.max(distance/result['projection_error']))))
    write(out/'box_perturbations.csv',rows)
    return dict(draws=sum(r['draws'] for r in rows),violations=sum(r['violations'] for r in rows),
                largest_error_to_bound=max(r['largest_error_to_bound'] for r in rows))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False);start=time.perf_counter()
    stress=perturbations(a.out);rows=[];inputs={}
    for cloud in sorted((a.capture/'clouds').glob('*_00.npz')):
        data=np.load(cloud);points=data['xyz'];origin=data['origin'];query=data['query'];plane=float(data['probe_z'])
        inputs[cloud.name]=hashlib.sha256(cloud.read_bytes()).hexdigest()
        azimuth=np.arctan2(points[:,1]-origin[1],points[:,0]-origin[0])
        configs=[('simultaneous',e,0.,0.,np.zeros(len(points))) for e in [0.,.002,.01,.02]]
        for period in [.02,.05]:
            for phase in [0.,np.pi/2,np.pi,3*np.pi/2]:
                age=np.mod(phase-azimuth,2*np.pi)/(2*np.pi)*period
                configs.append(('individual_age',.002,period,phase,age))
                configs.append(('oldest_age',.002,period,phase,np.full(len(points),np.max(age))))
        for method,e,period,phase,ages in configs:
            begin=time.perf_counter()
            result=bounded_witnesses(points,origin,query,plane,e,e,e,ages,5.,3.)
            witnesses=select_for_profile(result,.05)
            pre_ms=(time.perf_counter()-begin)*1000
            for name,(lo,hi) in CLASSES.items():
                for step in ([.1,.05] if name=='small_core' else [.1]):
                    profile=Profile(r_min=lo,r_max=hi,step=step)
                    begin=time.perf_counter();cert=certify(witnesses,profile);cpu=(time.perf_counter()-begin)*1000
                    rows.append(dict(id=cloud.stem,method=method,input_box_m=e,scan_period_s=period,end_phase_rad=phase,
                                     model=name,step_m=step,total_returns=len(points),certain_crossings=len(result['witnesses']),
                                     usable_witnesses=len(witnesses),projected_error_max_m=float(np.max(result['projection_error'])) if len(result['witnesses']) else 0.,
                                     effective_error_max_m=float(np.max(result['error'])) if len(result['witnesses']) else 0.,
                                     validity_s=cert['validity_s'],preprocess_ms=pre_ms,certificate_ms=cpu))
        print(json.dumps(dict(cloud=cloud.stem,completed_rows=len(rows))),flush=True)
    write(a.out/'projection_scan_audit.csv',rows)
    manifest=dict(host=socket.gethostname(),platform=platform.platform(),input_clouds=len(inputs),rows=len(rows),
                  perturbations=stress,elapsed_s=time.perf_counter()-start,
                  source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')},
                  dependency_sha256={n:hashlib.sha256((Path(__file__).resolve().parents[1]/'visibility_certificate_20261001'/n).read_bytes()).hexdigest()
                                     for n in ['geometry.py','run_study.py']},
                  protocol_sha256=hashlib.sha256(Path(__file__).with_name('PROTOCOL.md').read_bytes()).hexdigest(),input_sha256=inputs,
                  scope='Saved static CARLA geometry; upstream boxes supplied; rolling timestamps synthetically assigned by azimuth, not measured sensor times. No driving experiment.')
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)


if __name__=='__main__':main()
