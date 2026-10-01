#!/usr/bin/env python3
import argparse,csv,hashlib,json,math
from collections import Counter
from pathlib import Path
import numpy as np
from lease import Reader,Handoff,State,Policy,Actuation,maneuver,contains,ticks,pp,PREFIX
from binary_proof import decode,BinaryVerifier,timing_after_verified


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return list(csv.DictReader(p.open()))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--previous',type=Path,required=True);ap.add_argument('--capture',type=Path,required=True);a=ap.parse_args();src=Path(__file__).parent
    manifest=json.loads((a.results/'replay/manifest.json').read_text())
    for name,digest in manifest['source_hashes'].items():assert sha(src/name)==digest,name
    assert sha(src/'REPLAY_PROTOCOL.md')==manifest['protocol_sha256'];assert sha(a.previous/'ablation.csv')==manifest['input_csv_sha256']
    old={r['id']:r for r in read(a.previous/'ablation.csv') if r['mode']=='binary_combined'};rows=read(a.results/'replay/replay.csv');grid={r['id']:r for r in json.loads((a.results/'replay/age_grid.json').read_text())};assert len(rows)==len(old)==1044 and len(grid)==87
    reasons=Counter();checked=0;by_speed={};maximums={}
    for row in rows:
        r=old[row['id']];assert row['geometry']==r['geometry'] and row['physical_movement_authorized']=='False'
        for name in ['packet_sha256','acquisition_ms','generation_ms']:assert row[name]==r[name]
        age=(float(row['acquisition_ms'])+float(row['generation_ms'])+float(row['verification_ms'])+float(row['gate_ms']))/1000+.02
        assert abs(age-float(row['age_s']))<1e-12
        if row['geometry']=='False':
            assert all(row[k]=='False' for k in ['old_gate','region_gate','plus_1ms_old','plus_1ms_region']);reasons['no_packet_geometry']+=1;continue
        blob=(a.previous/'packets'/(row['id']+'.pvx')).read_bytes();assert hashlib.sha256(blob).hexdigest()==row['packet_sha256']
        _,n,_,_=PREFIX.unpack_from(blob);h=json.loads(blob[PREFIX.size:PREFIX.size+n]);s=h['scope'];scope=pp.Scope(s['episode'],s['frame_id'],tuple(s['query']),s['plane_z']);profiles={k:pp.Profile(**v) for k,v in h['profiles'].items()};contract=pp.Contract(**h['contract']);shape=Policy(**h['policy']);ref=h['reference_us']/pp.TIME_SCALE
        data=np.load(a.capture/'clouds'/(r['cloud']+'.npz'));o,rr,reference=pp.encode_source(data['xyz'],data['origin'],float(r['reference']),float(r['reference']));p,oo,sr=decode(blob,profiles,scope,contract,shape,h['speed'],h['yaw']);assert reference==p['reference_us'] and np.array_equal(o,oo);source=set(map(tuple,rr));assert all(tuple(x) in source for x in sr)
        assert BinaryVerifier(False).verify(blob,profiles,scope,contract,shape,h['speed'],h['yaw'],ref+.02)
        reader=Reader(profiles,contract,s['episode'],s['frame_id']);identity=reader.accept(blob,scope,ref+.02);assert identity;kernel=Handoff(reader);region=reader.regions[identity]
        def state(age):return State(s['query'][0]+h['speed']*age*math.cos(h['yaw']),s['query'][1]+h['speed']*age*math.sin(h['yaw']),h['yaw'],h['speed'])
        for extra,old_col,new_col in [(0.,'old_gate','region_gate'),(.001,'plus_1ms_old','plus_1ms_region')]:
            assert timing_after_verified(blob,shape,h['speed'],ref+age+extra)==(row[old_col]=='True')
            assert kernel.admissible(identity,state(age+extra),ref+age+extra)==(row[new_col]=='True')
        lo,hi,margin,duration=maneuver(state(age),Actuation());time_ok=ticks(ref+age)+ticks(duration)<region.expires_us;space_ok=contains(region,state(age),lo,hi,margin)
        reasons['admitted' if time_ok and space_ok else 'deadline' if not time_ok and space_ok else 'space' if time_ok else 'deadline_and_space']+=1
        g=grid[row['id']];old_ms=[];new_ms=[]
        for ms in range(501):
            if timing_after_verified(blob,shape,h['speed'],ref+ms/1000):old_ms.append(ms)
            if kernel.admissible(identity,state(ms/1000),ref+ms/1000):new_ms.append(ms)
        assert old_ms==g['old_pass_ms'] and new_ms==g['region_pass_ms']
        assert set(old_ms)<=set(new_ms) # An observed property of this fixed diagnostic, not universal policy dominance.
        key=(h['speed'],row['horizon'],g['old_max_ms'],g['region_max_ms']);maximums[str(key)]=maximums.get(str(key),0)+1;checked+=1
    for speed in [0.,.5,1.]:
        subset=[r for r in rows if float(r['speed'])==speed];by_speed[str(speed)]={k:sum(r[k]=='True' for r in subset) for k in ['geometry','old_gate','region_gate','plus_1ms_old','plus_1ms_region']};by_speed[str(speed)]['cases']=len(subset)
    report=dict(validation='passed',source_backed_current_ray_packets=checked,paired_cases=len(rows),grid_pair_checks=checked*501,reason_counts=dict(reasons),by_speed=by_speed,grid_maximum_groups=maximums,old_grid_subset_new_on_this_dataset=True,physical_movement_authorized=False,scope='Current raw-ray provenance and full reference geometry; deterministic conditional model and hybrid timing only. No safe waiting or actual control guarantee.')
    (a.results/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
