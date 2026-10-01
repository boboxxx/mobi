#!/usr/bin/env python3
import argparse,csv,hashlib,json,math,platform,socket,time
from collections import defaultdict
from pathlib import Path
import numpy as np
from lease import Reader,Handoff,State,Policy,pp,PREFIX
from binary_proof import timing_after_verified


def write(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--previous',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    source=list(csv.DictReader((a.previous/'ablation.csv').open()));source=[r for r in source if r['mode']=='binary_combined'];assert len(source)==1044
    readers={};rows=[];grids=[];start=time.perf_counter()
    for r in source:
        output=dict(id=r['id'],speed=float(r['speed']),horizon=float(r['horizon']),geometry=False,packet_sha256=r['packet_sha256'],acquisition_ms=float(r['acquisition_ms']),generation_ms=float(r['generation_ms']),verification_ms=0.,gate_ms=0.,age_s=0.,old_gate=False,region_gate=False,plus_1ms_old=False,plus_1ms_region=False,physical_movement_authorized=False)
        if r['geometry']=='True':
            blob=(a.previous/'packets'/(r['id']+'.pvx')).read_bytes();assert hashlib.sha256(blob).hexdigest()==r['packet_sha256']
            _,n,_,_=PREFIX.unpack_from(blob);h=json.loads(blob[PREFIX.size:PREFIX.size+n]);s=h['scope'];scope=pp.Scope(s['episode'],s['frame_id'],tuple(s['query']),s['plane_z']);profiles={k:pp.Profile(**v) for k,v in h['profiles'].items()};contract=pp.Contract(**h['contract']);shape=Policy(**h['policy']);ref=h['reference_us']/pp.TIME_SCALE
            key=(s['episode'],s['frame_id'],h['speed'],h['horizon_us']);reader=readers.setdefault(key,Reader(profiles,contract,s['episode'],s['frame_id']));kernel=Handoff(reader)
            start_age=(output['acquisition_ms']+output['generation_ms'])/1000+.02
            t=time.perf_counter();identity=reader.accept(blob,scope,ref+start_age);output['verification_ms']=(time.perf_counter()-t)*1000
            assert identity is not None, r['id'];output['geometry']=True
            def state(age):return State(s['query'][0]+h['speed']*age*math.cos(h['yaw']),s['query'][1]+h['speed']*age*math.sin(h['yaw']),h['yaw'],h['speed'])
            age=start_age+output['verification_ms']/1000
            t=time.perf_counter();kernel.admissible(identity,state(age),ref+age);output['gate_ms']=(time.perf_counter()-t)*1000
            age+=output['gate_ms']/1000;output['age_s']=age
            output['old_gate']=timing_after_verified(blob,shape,h['speed'],ref+age);output['region_gate']=kernel.admissible(identity,state(age),ref+age)
            output['plus_1ms_old']=timing_after_verified(blob,shape,h['speed'],ref+age+.001);output['plus_1ms_region']=kernel.admissible(identity,state(age+.001),ref+age+.001)
            old=[];new=[]
            for ms in range(501):
                age=ms/1000
                if timing_after_verified(blob,shape,h['speed'],ref+age):old.append(ms)
                if kernel.admissible(identity,state(age),ref+age):new.append(ms)
            grids.append(dict(id=r['id'],speed=h['speed'],horizon=h['horizon_us']/pp.TIME_SCALE,old_pass_ms=old,region_pass_ms=new,old_max_ms=max(old) if old else None,region_max_ms=max(new) if new else None,old_contiguous=not old or old==list(range(min(old),max(old)+1)),region_contiguous=not new or new==list(range(min(new),max(new)+1))))
        else:output['age_s']=(output['acquisition_ms']+output['generation_ms'])/1000+.02
        rows.append(output)
    write(a.out/'replay.csv',rows);(a.out/'age_grid.json').write_text(json.dumps(grids,indent=2)+'\n')
    valid=[r for r in rows if r['geometry']];assert len(valid)==87
    summary=dict(cases=len(rows),verified=len(valid),elapsed_s=time.perf_counter()-start,old_gate=sum(r['old_gate'] for r in rows),region_gate=sum(r['region_gate'] for r in rows),moving_old=sum(r['old_gate'] and r['speed']>0 for r in rows),moving_region=sum(r['region_gate'] and r['speed']>0 for r in rows),plus_1ms_old=sum(r['plus_1ms_old'] for r in rows),plus_1ms_region=sum(r['plus_1ms_region'] for r in rows),median_verification_ms=float(np.median([r['verification_ms'] for r in valid])),median_gate_ms=float(np.median([r['gate_ms'] for r in valid])),median_age_ms=1000*float(np.median([r['age_s'] for r in valid])),age_grid_evaluations=len(grids)*501,grid_region_more_points=sum(len(r['region_pass_ms'])>len(r['old_pass_ms']) for r in grids),grid_region_fewer_points=sum(len(r['region_pass_ms'])<len(r['old_pass_ms']) for r in grids),physical_movement_authorized=False)
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    src=Path(__file__).parent;manifest=dict(host=socket.gethostname(),python=platform.python_version(),numpy=np.__version__,source_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(src.glob('*.py'))},protocol_sha256=hashlib.sha256(src.joinpath('REPLAY_PROTOCOL.md').read_bytes()).hexdigest(),input_csv_sha256=hashlib.sha256((a.previous/'ablation.csv').read_bytes()).hexdigest(),scope='Conditional free-region replay; independent hypothetical states, stipulated unvalidated actuation and 20 ms link, no evidence-guided driving.')
    (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
