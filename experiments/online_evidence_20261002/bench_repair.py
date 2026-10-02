#!/usr/bin/env python3
import argparse,gzip,hashlib,json,math,socket,sys,time
from pathlib import Path
import numpy as np
from efficient_renew import body,repair,reference_repair
from profile_source import SELECT
from fast_path import Receiver
from repair_renew import renew as old_repair
from compress import pack


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(exist_ok=False)
    profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));c=body.Contract();rows=[];proofs=0
    for name,ids in SELECT.items():
        run=a.capture/name;r=json.loads(gzip.decompress((run/'record.json.gz').read_bytes()));rx=Receiver(profiles,c,name,'Carla/Maps/Town10HD_Opt');template=None
        for d in r['decisions']:
            cl=np.load(run/'clouds'/(d['id']+'.npz'));s=body.Scope(name,'Carla/Maps/Town10HD_Opt',tuple(d['query']),float(cl['plane_z']));m=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
            prior=rx.latest_region()
            if prior and not (prior.established<=d['stamp'] and math.ceil(d['stamp']*1e6)<rx._deadlines[prior.identity]):prior=None
            assert (prior.identity if prior else None)==d['prior']
            old=(run/'packets'/(d['id']+'.json')).read_bytes() if d['geometry'] else None
            if d['id'] in ids:
                for horizon in [.4,.45,.475]:
                    args=(template,cl['xyz'],cl['origin'],d['stamp'],d['stamp'],profiles,s,c,m,prior,horizon,d['sequence'])
                    def generate(method):
                        blob=method(*args) if template else None
                        return blob if blob else pack(*args[1:])
                    for repeat in range(3):
                        costs={};blobs={}
                        for kind in (['reference','reuse'] if repeat%2==0 else ['reuse','reference']):
                            begin=time.perf_counter();blobs[kind]=generate(reference_repair if kind=='reference' else repair);costs[kind]=(time.perf_counter()-begin)*1000
                        b=blobs['reuse'];assert b==blobs['reference'],(name,d['id'],horizon)
                        if horizon==.4:
                            assert b==generate(old_repair)==old,(name,d['id'],'original mismatch')
                        verify_ms=None;rays=0
                        if b:
                            begin=time.perf_counter();assert body.verify(b,profiles,s,c,m,prior,d['stamp']+.02,0);verify_ms=(time.perf_counter()-begin)*1000;proofs+=1
                            p,o,rs=body.decode(body.canonical(json.loads(b)['raw']),profiles,s,c);source_o,source_r,_=body.encode_source(cl['xyz'],cl['origin'],d['stamp'],d['stamp']);assert np.array_equal(o,source_o)
                            source_set={tuple(x) for x in source_r};assert all(tuple(x) in source_set for x in rs);rays=len(rs)
                            if repeat==0:(a.out/(name+'_'+d['id']+'_'+str(round(horizon*1000))+'.json')).write_bytes(b)
                        row=dict(run=name,id=d['id'],horizon_ms=horizon*1000,repeat=repeat,reference_ms=costs['reference'],reuse_ms=costs['reuse'],verify_ms=verify_ms,geometry=b is not None,packet_bytes=len(b) if b else 0,rays=rays);rows.append(row);print(json.dumps(row),flush=True)
            if old:template=old
            if d['receiver_accepted']:assert rx.accept(old,s,m,d['receiver_check_time'])
    assert len(rows)==6*3*3
    (a.out/'analysis.json').write_text(json.dumps(dict(host=socket.gethostname(),rows=rows,full_reference_proofs=proofs,byte_equivalence=True,current_ray_provenance=True,source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(__file__).with_name('efficient_renew.py')]},protocol_sha256=hashlib.sha256(Path(__file__).with_name('REPAIR_PROTOCOL.md').read_bytes()).hexdigest()),indent=2)+'\n')


if __name__=='__main__':main()
