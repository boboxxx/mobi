#!/usr/bin/env python3
import argparse,cProfile,hashlib,io,json,pstats,socket,sys,time
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'policy_evidence_20261001'))
import policy_proof as pp
from renew_policy import renew


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--templates',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    name='dense_0_free_00_v0.5_h0.4.json';b=(a.templates/'packets'/name).read_bytes();packet=json.loads(b);s=packet['raw']['payload']['scope'];scope=pp.Scope(s['episode'],s['frame_id'],tuple(s['query']),s['plane_z'])
    path=a.capture/'clouds/dense_0_free_01.npz';d=np.load(path);profiles={k:pp.Profile(**v) for k,v in packet['raw']['payload']['profiles'].items()}
    call=lambda:renew(b,d['xyz'],d['origin'],2.,2.,profiles,scope,pp.Contract(),pp.Policy(),.5,packet['yaw'],.4,1,True)
    call();times=[]
    for i in range(10):
        start=time.perf_counter();result=call();times.append((time.perf_counter()-start)*1000);assert result is not None
    pr=cProfile.Profile();pr.enable();call();pr.disable();output=io.StringIO();pstats.Stats(pr,stream=output).sort_stats('cumulative').print_stats(30)
    (a.out/'profile.txt').write_text(output.getvalue());threadpool=None
    try:
        from threadpoolctl import threadpool_info
        threadpool=threadpool_info()
    except ImportError:pass
    data=dict(host=socket.gethostname(),milliseconds=times,median_ms=float(np.median(times)),threadpool=threadpool,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),scope='Ten warmed repeated calls on one saved cloud for bottleneck diagnosis; not independent performance evaluation.')
    (a.out/'manifest.json').write_text(json.dumps(data,indent=2)+'\n');print(output.getvalue());print(json.dumps(data),flush=True)


if __name__=='__main__':main()
