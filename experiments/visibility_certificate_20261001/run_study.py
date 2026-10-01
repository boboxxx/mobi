#!/usr/bin/env python3
"""Bounded model stress, archived-cloud replay, proof serialization study."""
import argparse,csv,hashlib,json,math,platform,re,socket,time
from pathlib import Path
from dataclasses import asdict,replace
import numpy as np
import scipy
from geometry import Profile,grid,plane_witnesses,certify,inverse_travel
from proof_packet import pack,verify

CLASSES={'small_core':(.2,.4),'vehicle_core':(.55,2.5)}

def write(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def location(s):return np.array([float(x) for x in re.search(r'Location\(x=([^,]+), y=([^,]+), z=([^)]+)',s).groups()])

def ray_scene(rng,rmin,rmax):
    centers=rng.uniform(-9,9,(rng.integers(0,9),2));radii=rng.uniform(rmin,rmax,len(centers))
    origin=np.array([-12.,0.]);angles=np.linspace(-math.pi,math.pi,512,endpoint=False)
    directions=np.column_stack([np.cos(angles),np.sin(angles)]);limits=np.full(512,25.)
    for c,r in zip(centers,radii):
        d=c-origin;projection=directions@d;disc=projection**2-np.dot(d,d)+r*r
        valid=(disc>=0)&(projection>0)
        hit=projection-np.sqrt(np.maximum(disc,0))
        limits[valid]=np.minimum(limits[valid],np.maximum(hit[valid],0))
    pts=[]
    for direction,limit in zip(directions,limits):
        distances=np.arange(.1,max(.1,limit-1e-6),.15)
        pts.append(origin+distances[:,None]*direction)
    return np.concatenate(pts),centers,radii

def stress(out,n):
    rng=np.random.default_rng(20261004);rows=[]
    for seed in range(n):
        name=list(CLASSES)[seed%2];lo,hi=CLASSES[name];p=Profile(r_min=lo,r_max=hi)
        points,centers,radii=ray_scene(rng,lo,hi)
        theta=rng.uniform(0,2*math.pi,len(points));norm=rng.uniform(0,p.error,len(points))
        measured=points+norm[:,None]*np.column_stack([np.cos(theta),np.sin(theta)])
        result=certify(measured,p,return_mask=True)
        false_centers=0
        width=round(2*p.domain/p.step)
        for c in centers:
            ix=np.floor((c+p.domain)/p.step).astype(int)
            if np.all((ix>=0)&(ix<width)):false_centers+=int(result['excluded'][ix[0]*width+ix[1]])
        truth_distance=min([p.domain-p.query_radius-p.r_max]+[max(0,float(np.linalg.norm(c)-r-p.query_radius)) for c,r in zip(centers,radii)])
        truth_ttl=inverse_travel(truth_distance,p)
        rows.append(dict(seed=seed,model=name,obstacles=len(centers),witnesses=len(measured),validity_s=result['validity_s'],
                         truth_earliest_s=truth_ttl,false_center_exclusions=false_centers,
                         expiry_overestimate=int(result['validity_s']>truth_ttl+1e-8)))
        if (seed+1)%250==0:print(json.dumps(dict(stress_completed=seed+1)),flush=True)
    write(out/'synthetic.csv',rows)
    return dict(scenes=n,positive_certificates=sum(r['validity_s']>0 for r in rows),
                false_center_exclusions=sum(r['false_center_exclusions'] for r in rows),
                expiry_overestimates=sum(r['expiry_overestimate'] for r in rows))

def replay(archive,out):
    manifest=json.loads((archive/'manifest.json').read_text());rows=[];packets=[]
    for layout in range(2):
        setup=manifest['setup'][layout*2];origin=location(setup['sensor']);target=location(setup['target'])
        for scenario in ['free','occupied']:
            xyz=np.load(archive/('points_%d_%s.npz'%(layout,scenario)))['xyz']
            for thin in [1,8]:
                witnesses=plane_witnesses(xyz[::thin],origin,target[:2],target[2]+.6)
                for name,(lo,hi) in CLASSES.items():
                    for step in [.05,.1,.2]:
                        p=Profile(r_min=lo,r_max=hi,step=step);start=time.perf_counter();r=certify(witnesses,p)
                        rows.append(dict(layout=layout,scenario=scenario,thinning=thin,model=name,step=step,
                                         **r,compute_ms=(time.perf_counter()-start)*1000))
                        if step!=.1:continue
                        for ttl in [.1,.2]:
                            scope='archive:%d:%s:%s'%(layout,scenario,name);t=time.perf_counter();blob=pack(witnesses,p,scope,0,ttl)
                            pack_ms=(time.perf_counter()-t)*1000;t=time.perf_counter()
                            accepted=bool(blob and verify(blob,p,scope,.02,.02));verify_ms=(time.perf_counter()-t)*1000
                            file_name='%d_%s_%d_%s_%s.json'%(layout,scenario,thin,name,ttl)
                            if blob:(out/'packets'/file_name).write_bytes(blob)
                            packets.append(dict(layout=layout,scenario=scenario,thinning=thin,model=name,target_s=ttl,
                                                sent=blob is not None,verified=accepted,packet_bytes=len(blob) if blob else 0,
                                                raw_xyz_bytes=len(xyz[::thin])*12,pack_ms=pack_ms,verify_ms=verify_ms))
    write(out/'archive_replay.csv',rows);write(out/'packet_results.csv',packets)

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--scenes',type=int,default=2000);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);(a.out/'packets').mkdir()
    start=time.perf_counter();summary=stress(a.out,a.scenes);replay(a.archive,a.out)
    manifest=dict(host=socket.gethostname(),platform=platform.platform(),numpy=np.__version__,scipy=scipy.__version__,
                  date='2026-10-01',synthetic=summary,elapsed_s=time.perf_counter()-start,
                  source_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in Path(__file__).parent.glob('*.py') if not f.name.startswith('._')},
                  protocol_sha256=hashlib.sha256(Path(__file__).with_name('PROTOCOL.md').read_bytes()).hexdigest(),
                  scope='Conditional disk-core model tests and replay of archived CARLA clouds; replay is not a new simulator run.')
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)

if __name__=='__main__':main()
