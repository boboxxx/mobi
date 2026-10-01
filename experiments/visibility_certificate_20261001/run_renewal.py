#!/usr/bin/env python3
"""Post-acquisition timing remedy; current-cloud proof renewal on sheng."""
import argparse,csv,hashlib,json,socket,time
from pathlib import Path
from dataclasses import replace
import numpy as np
from scipy.spatial import cKDTree
from geometry import Profile,plane_witnesses
from proof_packet import verify
from renewal import renew
from run_study import CLASSES,write

def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    frames=list(csv.DictReader((a.capture/'frames.csv').open()));labels={r['id']:r for r in csv.DictReader((a.capture/'evaluation_labels.csv').open())}
    index={(r['id'],r['thinning'],r['model']):r for r in frames};rows=[];checks=[];started=time.perf_counter()
    for cloud in sorted((a.capture/'clouds').glob('*.npz')):
        density,layout,scenario,step=cloud.stem.split('_');data=np.load(cloud)
        for thin in [1,8]:
            for model,(lo,hi) in CLASSES.items():
                entry=index[cloud.stem,str(thin),model]
                p=Profile(r_min=lo,r_max=hi,step=float(entry['chosen_step']))
                t=time.perf_counter();w=plane_witnesses(data['xyz'][::thin],data['origin'],data['query'],float(data['probe_z']))
                preprocessing_ms=(time.perf_counter()-t)*1000
                truth=labels[cloud.stem]
                if truth['center_x']:
                    c=np.array([float(truth['center_x']),float(truth['center_y'])])
                    nearest=float(cKDTree(w).query(c)[0]) if len(w) else np.inf
                    checks.append(dict(id=cloud.stem,thinning=thin,model=model,center_excluded=nearest+p.error<p.r_min-1e-9))
                for target in [.1,.2]:
                    # Free-frame-zero is the only template source. Near/far cases
                    # must refresh from their own rays and cannot use free content.
                    template=a.capture/'packets'/('%s_%s_free_00_%d_%s_%s.json'%(density,layout,thin,model,target))
                    if not template.exists():continue
                    if step=='00' and scenario=='free':continue  # Initialization, not held-out renewal.
                    t=time.perf_counter();blob=renew(template.read_bytes(),w,p,cloud.stem+':'+model,0)
                    refresh_ms=(time.perf_counter()-t)*1000;t=time.perf_counter()
                    ok=bool(blob and verify(blob,p,cloud.stem+':'+model,.02,.05));verification_ms=(time.perf_counter()-t)*1000
                    age=(float(entry['acquisition_ms'])+preprocessing_ms+refresh_ms+verification_ms)/1000+.02
                    timed=bool(blob and verify(blob,p,cloud.stem+':'+model,age,.05))
                    rows.append(dict(id=cloud.stem,density=density,layout=layout,scenario=scenario,step=step,thinning=thin,model=model,
                                     target_s=target,geometry_verified=ok,timing_budget_passed=timed,packet_bytes=len(blob) if blob else 0,
                                     preprocessing_ms=preprocessing_ms,refresh_ms=refresh_ms,verification_ms=verification_ms,modeled_total_age_s=age))
        if step=='09':print(json.dumps(dict(completed=density+':'+layout+':'+scenario)),flush=True)
    write(a.out/'renewal.csv',rows);write(a.out/'center_checks.csv',checks)
    manifest=dict(host=socket.gethostname(),attempts=len(rows),positive_geometry=sum(r['geometry_verified'] for r in rows),
                  timing_budget_passes=sum(r['timing_budget_passed'] for r in rows),
                  near_geometry_accepts=sum(r['geometry_verified'] and r['scenario']=='near' for r in rows),
                  false_actual_center_exclusions=sum(r['center_excluded'] for r in checks),elapsed_s=time.perf_counter()-started,
                  source_sha256={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['renewal.py','run_renewal.py','geometry.py','proof_packet.py']},
                  scope='Current-cloud replay measured on sheng plus recorded acquisition times, modeled 20ms transport/50ms action. No physical driving or measured proof-radio transfer.')
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)

if __name__=='__main__':main()
