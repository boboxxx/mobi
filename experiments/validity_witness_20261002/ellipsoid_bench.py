#!/usr/bin/env python3
import argparse,hashlib,json,os,socket,time
from pathlib import Path
import numpy as np
import ellipsoid
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);a=ap.parse_args();out=a.results/'ellipsoid_study';out.mkdir(exist_ok=False)
    base=a.results/'study/analysis.json';s=json.loads(base.read_bytes());rows=[];ellipsoid.library()
    assert all(os.environ.get(n)=='1' for n in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'])
    for original in s['rows']:
        row={k:v for k,v in original.items() if k not in ['witness','search_ms','native_calls','candidates']};path=a.results/'study'/row['input_file'];assert sha(path)==row['input_sha256']
        with np.load(path) as z:rays=z['rays']
        p=row['profile'];t=time.perf_counter();w,counts=ellipsoid.find(rays,row['scope']['plane_z'],np.asarray(row['scope']['query']),row['motion']['yaw'],row['ref_us'],row['actual_times_us'][-1],p['r_min'],p['r_max'],row['error']);row.update(witness=w,search_ms=(time.perf_counter()-t)*1000,**counts)
        if w:assert w['time_us']>=row['lower_horizon_us'],(row,w)
        rows.append(row);print(json.dumps({k:row[k] for k in ['run','index','klass','witness','search_ms']}),flush=True)
    code=Path(__file__).resolve().parent;sources={str(p.relative_to(ROOT)):sha(p) for p in code.iterdir() if p.name.startswith('ellipsoid') or p.name in ['ELLIPSOID_PROTOCOL.md','test_ellipsoid.py']}
    result=dict(host=socket.gethostname(),rows=rows,sphere_study_sha256=sha(base),source_sha256=sources,library_sha256=sha(Path(os.environ['MOBI_ELLIPSOID_LIBRARY'])),scope='Same36 histories; separately frozen opaque ellipsoid candidates satisfying original core/outer constraints; model-conditional upper bounds, not physical counterfactual or optimality.')
    (out/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
