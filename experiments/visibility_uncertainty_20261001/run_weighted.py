#!/usr/bin/env python3
import argparse,csv,hashlib,json,socket,time
from pathlib import Path
import numpy as np
from weighted import certify_weighted,best_uniform
from geometry import Profile
from run_study import CLASSES,write
from projection import bounded_witnesses


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    labels={r['id']:r for r in csv.DictReader((a.capture/'evaluation_labels.csv').open())}
    rows=[];start=time.perf_counter()
    for cloud in sorted((a.capture/'clouds').glob('*_00.npz')):
        d=np.load(cloud);p=d['xyz'];o=d['origin'];q=d['query'];z=float(d['probe_z'])
        azimuth=np.arctan2(p[:,1]-o[1],p[:,0]-o[0])
        for period in [.02,.05]:
            for phase in [0.,np.pi/2,np.pi,3*np.pi/2]:
                age=np.mod(phase-azimuth,2*np.pi)/(2*np.pi)*period
                projected=bounded_witnesses(p,o,q,z,.002,.002,.002,age,5.,3.)
                for name,(lo,hi) in CLASSES.items():
                    for step in ([.1,.05] if name=='small_core' else [.1]):
                        profile=Profile(r_min=lo,r_max=hi,step=step,error=0.)
                        begin=time.perf_counter();cert=certify_weighted(projected['witnesses'],projected['error'],profile,return_mask=True)
                        cpu=(time.perf_counter()-begin)*1000;label=labels[cloud.stem];false_center=False
                        begin=time.perf_counter();uniform=best_uniform(projected['witnesses'],projected['error'],profile)
                        uniform_cpu=(time.perf_counter()-begin)*1000
                        if label['center_x']:
                            c=np.array([float(label['center_x']),float(label['center_y'])]);ix=np.floor((c+profile.domain)/step).astype(int)
                            width=round(2*profile.domain/step)
                            if np.all((ix>=0)&(ix<width)):false_center=bool(cert['excluded'][ix[0]*width+ix[1]])
                        rows.append(dict(id=cloud.stem,method='heterogeneous',input_box_m=.002,scan_period_s=period,end_phase_rad=phase,
                                         model=name,step_m=step,validity_s=cert['validity_s'],usable_witnesses=cert['witnesses'],
                                         error_bins=cert['error_bins'],certificate_ms=cpu,false_actual_center_exclusion=false_center,
                                         best_uniform_ttl_s=uniform['validity_s'],best_uniform_budget_m=uniform['error_budget_m'],uniform_sweep_ms=uniform_cpu))
        print(json.dumps(dict(cloud=cloud.stem,rows=len(rows))),flush=True)
    write(a.out/'weighted.csv',rows)
    manifest=dict(host=socket.gethostname(),rows=len(rows),positive=sum(r['validity_s']>0 for r in rows),
                  false_actual_center_exclusions=sum(r['false_actual_center_exclusion'] for r in rows),elapsed_s=time.perf_counter()-start,
                  source_sha256={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['run_weighted.py','weighted.py','projection.py','test_weighted.py']},
                  protocol_sha256=hashlib.sha256(Path(__file__).with_name('WEIGHTED_FOLLOWUP.md').read_bytes()).hexdigest(),
                  scope='Post-diagnostic heterogeneous-error replay of the same static clouds with hypothetical rolling timestamps; no proof-packet or dynamic CARLA claim.')
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)


if __name__=='__main__':main()
