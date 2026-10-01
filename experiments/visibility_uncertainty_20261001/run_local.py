#!/usr/bin/env python3
"""Compare exact local search to every stored exhaustive-reference case."""
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
    reference=list(csv.DictReader(a.reference.open()));rows=[];loaded={};previous=None;projected=None
    for r in reference:
        key=(r['id'],r['scan_period_s'],r['end_phase_rad'])
        if key!=previous:
            if r['id'] not in loaded:loaded[r['id']]=dict(np.load(a.capture/'clouds'/(r['id']+'.npz')))
            d=loaded[r['id']];p=d['xyz'];o=d['origin']
            azimuth=np.arctan2(p[:,1]-o[1],p[:,0]-o[0])
            age=np.mod(float(r['end_phase_rad'])-azimuth,2*np.pi)/(2*np.pi)*float(r['scan_period_s'])
            projected=bounded_witnesses(p,o,d['query'],float(d['probe_z']),.002,.002,.002,age,5.,3.)
            previous=key
        lo,hi=CLASSES[r['model']];profile=Profile(r_min=lo,r_max=hi,step=float(r['step_m']),error=0.)
        begin=time.perf_counter();fast=compare_local(projected['witnesses'],projected['error'],profile)
        cpu=(time.perf_counter()-begin)*1000
        error=max(abs(fast['validity_s']-float(r['validity_s'])),abs(fast['best_uniform_ttl_s']-float(r['best_uniform_ttl_s'])))
        if error>1e-10:
            raise RuntimeError('Local search differs from exhaustive reference: '+str(key))
        rows.append(dict(id=r['id'],scan_period_s=r['scan_period_s'],end_phase_rad=r['end_phase_rad'],model=r['model'],step_m=r['step_m'],
                         validity_s=fast['validity_s'],best_uniform_ttl_s=fast['best_uniform_ttl_s'],max_abs_error_s=error,
                         combined_local_ms=cpu,combined_reference_ms=float(r['certificate_ms'])+float(r['uniform_sweep_ms']),
                         tree_point_queries=fast['tree_point_queries']))
    write(a.out/'local_comparison.csv',rows)
    ratios=[r['combined_reference_ms']/r['combined_local_ms'] for r in rows]
    manifest=dict(host=socket.gethostname(),cases=len(rows),max_abs_error_s=max(r['max_abs_error_s'] for r in rows),
                  median_combined_speed_ratio=float(np.median(ratios)),local_ms_median=float(np.median([r['combined_local_ms'] for r in rows])),
                  local_ms_max=max(r['combined_local_ms'] for r in rows),
                  reference_sha256=hashlib.sha256(a.reference.read_bytes()).hexdigest(),
                  source_sha256={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['local_search.py','run_local.py','test_local_search.py','projection.py','weighted.py']},
                  scope='Exact comparison of the same binned heterogeneous and best-uniform geometry; combined CPU comparison, not complete proof-communication latency.')
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)


if __name__=='__main__':main()
