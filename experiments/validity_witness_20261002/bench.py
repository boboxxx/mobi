#!/usr/bin/env python3
"""Finite search on received dictionaries; no simulator or future data."""
import argparse,hashlib,json,math,os,socket,time
from pathlib import Path
import numpy as np
import search
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(exist_ok=False);(a.out/'inputs').mkdir()
    assert all(os.environ.get(n)=='1' for n in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'])
    baseline=ROOT/'results/recursive_validity_20261002/study/analysis.json';old=json.loads(baseline.read_bytes());inputs={str(baseline.relative_to(ROOT)):sha(baseline)};rows=[]
    search.library()
    for ctx in old['contexts']:
        name=ctx['run'];prefix=[]
        for identity in ctx['prefix_ids']:
            p=ROOT/'results/online_evidence_20261002/live'/name/'packets'/(identity+'.json');inputs[str(p.relative_to(ROOT))]=sha(p);prefix.append((str(p.relative_to(ROOT)),json.loads(p.read_bytes())['raw']))
        steps=[]
        for index in range(20,40):
            p=ROOT/'results/streaming_recovery_20261002/study/source'/(name+'_drive_%03d.json'%index);inputs[str(p.relative_to(ROOT))]=sha(p);steps.append((str(p.relative_to(ROOT)),json.loads(p.read_bytes())))
            if index not in [22,25,39]:continue
            received=prefix+steps;raw=steps[-1][1]['payload'];ref=raw['reference_us'];scope=ctx['anchor']['scope'];motion=ctx['anchor']['motion']
            start=time.perf_counter();blocks=[]
            for path,packet in received:
                p=packet['payload'];orig=np.asarray(p['origins'],dtype=np.int64);ray=np.asarray(p['rays'],dtype=np.int64)
                blocks.append(np.column_stack([orig[ray[:,0]],ray[:,1:]]))
            integers=np.unique(np.concatenate(blocks),axis=0);integers=integers[np.argsort(-integers[:,6],kind='stable')]
            back,times,cumulative=search.backwards(integers[:,6],ref,5.,3.);rays=np.column_stack([integers[:,:6]*.001,back]);prep_ms=(time.perf_counter()-start)*1000
            npz=a.out/'inputs'/(name+'_drive_%03d.npz'%index);np.savez_compressed(npz,integers=integers,rays=rays)
            lower=next(r for r in old['rows'] if r['run']==name and r['index']==index and r['method']=='fine_terminal' and r['preset']=='standard' and r['repeat']==0)
            contract=raw['contract'];error=math.sqrt(3)*max(contract['point_error']+.0005,contract['origin_error']+.0005)
            for klass,profile in raw['profiles'].items():
                assert profile['speed']==5. and profile['acceleration']==3.
                t=time.perf_counter();w,counts=search.find(rays,scope['plane_z'],np.asarray(scope['query']),motion['yaw'],ref,int(times[-1]),profile['r_min'],error);ms=(time.perf_counter()-t)*1000
                class_h=lower['decision']['classes'][klass]['horizon_us']
                if w:assert w['time_us']>=class_h,(name,index,klass,class_h,w)
                row=dict(run=name,index=index,klass=klass,ref_us=ref,received_paths=[p for p,_ in received],input_file=str(npz.relative_to(a.out)),input_sha256=sha(npz),rays=len(rays),actual_times_us=times.tolist(),back_distances=cumulative.tolist(),scope=scope,motion=motion,profile=profile,error=error,lower_horizon_us=class_h,joint_lower_horizon_us=lower['horizon_us'],witness=w,search_ms=ms,preparation_ms=prep_ms,**counts)
                rows.append(row);print(json.dumps({k:row[k] for k in ['run','index','klass','lower_horizon_us','witness','search_ms']}),flush=True)
    sources={str(p.relative_to(ROOT)):sha(p) for p in Path(__file__).resolve().parent.iterdir() if p.suffix in ['.py','.cpp','.md']}
    out=dict(host=socket.gethostname(),rows=rows,input_sha256=inputs,source_sha256=sources,library_sha256=sha(Path(os.environ['MOBI_SEGMENT_LIBRARY'])),scope='36 finite ray-consistent kinematic witness searches on saved received dictionaries; conditional model only; no road feasibility, actual vehicle collision, live driving or complete optimality claim.')
    assert len(rows)==36;(a.out/'analysis.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
