#!/usr/bin/env python3
"""Post-analysis paired repair diagnostic on an identified archived failure."""
import argparse,gzip,hashlib,json,time
from pathlib import Path
import numpy as np
from fast_path import body,Receiver
from compress import pack
from repair_renew import renew as repair


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(exist_ok=True)
    name='view0_history';root=a.capture/name;record=json.loads(gzip.decompress((root/'record.json.gz').read_bytes()));p=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));c=body.Contract();rx=Receiver(p,c,name,'Carla/Maps/Town10HD_Opt');template=None
    for d in record['decisions']:
        cl=np.load(root/'clouds'/(d['id']+'.npz'));sc=body.Scope(name,'Carla/Maps/Town10HD_Opt',tuple(d['query']),float(cl['plane_z']));m=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
        if d['phase']=='warm' and d['index']==1:
            prior=rx.latest_region();rows=[];blobs={}
            for repeat in range(8):
                row=dict(repeat=repeat)
                for kind in (['compressed','repair'] if repeat%2==0 else ['repair','compressed']):
                    args=(cl['xyz'],cl['origin'],d['stamp'],d['stamp'],p,sc,c,m,prior);start=time.perf_counter();b=pack(*args,.4,d['sequence']) if kind=='compressed' else repair(template,*args,.4,d['sequence']);row[kind+'_ms']=(time.perf_counter()-start)*1000
                    assert b is not None and body.verify(b,p,sc,c,m,prior,d['stamp']+.02,0)
                    payload,o,r=body.decode(body.canonical(json.loads(b)['raw']),p,sc,c);source_o,source_r,_=body.encode_source(cl['xyz'],cl['origin'],d['stamp'],d['stamp']);assert np.array_equal(o,source_o);source_set={tuple(x) for x in source_r};assert all(tuple(x) in source_set for x in r)
                    row[kind+'_rays']=len(r);row[kind+'_bytes']=len(b);blobs[kind]=b
                rows.append(row)
            for kind,b in blobs.items():(a.out/(kind+'.json')).write_bytes(b)
            report=dict(rows=rows,median_ms={k:float(np.median([r[k+'_ms'] for r in rows])) for k in ['compressed','repair']},all_proofs_fully_verified=True,current_ray_provenance_verified=True,source_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in Path(__file__).parent.glob('*.py')},scope='Post-analysis repair of one identified archived transition, eight alternating-order repeats. Not independent scenarios, fresh closed-loop evidence, or a worst-case timing bound.')
            (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['rows','source_sha256']},indent=2));return
        if d['packet_sha256']:template=(root/'packets'/(d['id']+'.json')).read_bytes()
        if d['receiver_accepted']:assert rx.accept(template,sc,m,d['receiver_check_time'])
    raise RuntimeError('Expected transition missing')


if __name__=='__main__':main()
