#!/usr/bin/env python3
import argparse,csv,hashlib,json,socket,time
from pathlib import Path
import numpy as np
from local_search import compare_local
from geometry import Profile
from run_study import CLASSES,write
from projection import bounded_witnesses


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True)
    ap.add_argument('--reference',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    reference=list(csv.DictReader(a.reference.open()));rows=[];loaded={}
    for error in [.01,.02]:
        previous=None;projected=None
        for r in reference:
            key=(r['id'],r['scan_period_s'],r['end_phase_rad'])
            if key!=previous:
                if r['id'] not in loaded:loaded[r['id']]=dict(np.load(a.capture/'clouds'/(r['id']+'.npz')))
                d=loaded[r['id']];p=d['xyz'];o=d['origin']
                angle=np.arctan2(p[:,1]-o[1],p[:,0]-o[0])
                age=np.mod(float(r['end_phase_rad'])-angle,2*np.pi)/(2*np.pi)*float(r['scan_period_s'])
                projected=bounded_witnesses(p,o,d['query'],float(d['probe_z']),error,error,error,age,5.,3.)
                previous=key
            lo,hi=CLASSES[r['model']];profile=Profile(r_min=lo,r_max=hi,step=float(r['step_m']),error=0.)
            start=time.perf_counter();result=compare_local(projected['witnesses'],projected['error'],profile)
            rows.append(dict(id=r['id'],input_box_m=error,scan_period_s=r['scan_period_s'],end_phase_rad=r['end_phase_rad'],
                             model=r['model'],step_m=r['step_m'],validity_s=result['validity_s'],best_uniform_ttl_s=result['best_uniform_ttl_s'],
                             combined_ms=1000*(time.perf_counter()-start),
                             monotonicity_violation=result['validity_s']>float(r['validity_s'])+1e-10 or result['best_uniform_ttl_s']>float(r['best_uniform_ttl_s'])+1e-10))
    write(a.out/'sensitivity.csv',rows)
    manifest=dict(host=socket.gethostname(),rows=len(rows),monotonicity_violations=sum(r['monotonicity_violation'] for r in rows),
                  near_positive=sum('_near_' in r['id'] and r['validity_s']>0 for r in rows),
                  source_sha256={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['run_sensitivity.py','local_search.py','projection.py','weighted.py']},
                  protocol_sha256=hashlib.sha256(Path(__file__).with_name('LARGER_ERRORS.md').read_bytes()).hexdigest(),
                  reference_sha256=hashlib.sha256(a.reference.read_bytes()).hexdigest(),
                  scope='Larger supplied coordinate boxes, same hypothetical scan phases and static geometry. Not physical calibration or closed-loop driving.')
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)


if __name__=='__main__':main()
