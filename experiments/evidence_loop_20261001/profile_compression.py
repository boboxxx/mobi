#!/usr/bin/env python3
import argparse,gzip,json,sys,time,hashlib,socket
from pathlib import Path
import numpy as np
from fast_path import body
from strict import Receiver
from compress import pack as eager
from lazy_compress import pack as lazy


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    p=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));c=body.Contract();rows=[]
    for name in ['view0_current','view0_history']:
        root=a.capture/name;rec=json.loads(gzip.decompress((root/'record.json.gz').read_bytes()));rx=Receiver(p,c,name,'Carla/Maps/Town10HD_Opt')
        for d in rec['decisions']:
            if d['phase'] not in ['root','warm'] or (d['phase']=='warm' and (not rec['history'] or d['index']>0)):break
            cl=np.load(root/'clouds'/(d['id']+'.npz'));sc=body.Scope(name,'Carla/Maps/Town10HD_Opt',tuple(d['query']),float(cl['plane_z']));m=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
            prior=rx.latest_region() if rec['history'] else None
            if prior and not prior.established<=d['stamp']<prior.expires:prior=None
            for repeat in range(4):
                blobs={};timings={}
                for kind,fn in ([('eager',eager),('lazy',lazy)] if repeat%2==0 else [('lazy',lazy),('eager',eager)]):
                    start=time.perf_counter();blobs[kind]=fn(cl['xyz'],cl['origin'],d['stamp'],d['stamp'],p,sc,c,m,prior,.4,d['sequence']);timings[kind]=(time.perf_counter()-start)*1000
                assert blobs['eager']==blobs['lazy'];rows.append(dict(run=name,id=d['id'],repeat=repeat,geometry=blobs['eager'] is not None,identical_bytes=True,**timings))
            if d['receiver_accepted']:assert rx.accept((root/'packets'/(d['id']+'.json')).read_bytes(),sc,m,d['receiver_check_time'])
    report=dict(host=socket.gethostname(),paired_comparisons=len(rows),all_bytes_equal=True,median_ms={k:float(np.median([r[k] for r in rows])) for k in ['eager','lazy']},first_warm_median_ms={k:float(np.median([r[k] for r in rows if r['id']=='warm_000'])) for k in ['eager','lazy']},rows=rows,source_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in Path(__file__).parent.glob('*.py')},scope='Alternating-order saved-data profile, same packets; not new live driving or statistical independent trials.')
    a.out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['rows','source_sha256']},indent=2))


if __name__=='__main__':main()
