#!/usr/bin/env python3
"""Validate manifests and every saved proof against captured current raw rays."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
import policy_proof as pp
from tube import Policy
from strict_policy import verify,conditional_stop_gate


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return list(csv.DictReader(path.open()))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--capture',type=Path,required=True);a=ap.parse_args();src=Path(__file__).parent;report={};checked=0
    profiles=dict(small=pp.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=pp.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=pp.Contract();policy=Policy()
    for folder,table,protocol,positive in [('geometry','geometry.csv','GEOMETRY_PROTOCOL.md','packet_verified'),('renewal','renewal.csv','RENEWAL_PROTOCOL.md','geometry')]:
        root=a.results/folder;m=json.loads((root/'manifest.json').read_text());rows=read(root/table)
        assert len(rows)==m['trials']
        for name,digest in m['source_sha256'].items():assert sha(src/name)==digest,name
        assert sha(src/protocol)==m['protocol_sha256']
        for name,digest in m['input_sha256'].items():assert sha(a.capture/'clouds'/name)==digest,name
        if folder=='renewal':
            assert sha(a.capture/'frames.csv')==m['frames_sha256']
            for name,digest in m['template_sha256'].items():assert sha(a.results/'geometry/packets'/name)==digest
            assert all(r['byte_equal']=='True' for r in rows)
        count=0
        for row in rows:
            exists=(root/'packets'/(row['id']+'.json')).exists();assert exists==(row[positive]=='True')
            assert row['physical_movement_authorized']=='False'
            if not exists:continue
            blob=(root/'packets'/(row['id']+'.json')).read_bytes();p=json.loads(blob);s=p['raw']['payload']['scope']
            scope=pp.Scope(s['episode'],s['frame_id'],tuple(s['query']),s['plane_z']);speed=float(row['speed']);yaw=float(row['yaw'])
            payload,o,r=pp.decode(pp.canonical(p['raw']),profiles,scope,contract)
            d=np.load(a.capture/'clouds'/(row['cloud']+'.npz'));reference=float(row.get('reference',1.))
            assert tuple(d['query'])==scope.query and float(d['probe_z'])==scope.plane_z
            so,sr,stamp=pp.encode_source(d['xyz'],d['origin'],reference,reference)
            assert np.array_equal(so,o) and stamp==payload['reference_us']
            source=set(map(tuple,sr));assert all(tuple(x) in source for x in r)
            assert verify(blob,profiles,scope,contract,policy,speed,yaw,reference+.02)
            if folder=='renewal':
                for col,age in [('fast_conditional_stop','age_s'),('full_conditional_stop','full_age_s')]:
                    assert conditional_stop_gate(blob,profiles,scope,contract,policy,speed,yaw,reference+float(row[age]))==(row[col]=='True')
            else:
                for col,age in [('minimum_age_gate',.02),('measured_compute_gate',float(row['modeled_age_without_acquisition'])),('with_50ms_acquisition_gate',float(row['modeled_age_without_acquisition'])+.05)]:
                    assert conditional_stop_gate(blob,profiles,scope,contract,policy,speed,yaw,1.+age)==(row[col]=='True')
            count+=1
        assert count==len(list((root/'packets').glob('*.json')));checked+=count
        columns=['arbitrary_geometry','policy_geometry','packet_verified','minimum_age_gate','measured_compute_gate','with_50ms_acquisition_gate'] if folder=='geometry' else ['template_available','byte_equal','geometry','fast_conditional_stop','full_conditional_stop']
        summary={col:sum(r[col]=='True' for r in rows) for col in columns}
        summary.update(trials=len(rows),source_backed_packets=count,near_geometry=sum(r[positive]=='True' and '_near_' in r['cloud'] for r in rows))
        if folder=='renewal':
            positive_rows=[r for r in rows if r['geometry']=='True']
            summary['medians_on_geometry_positive']={k:float(np.median([float(r[k]) for r in positive_rows])) for k in ['full_ms','fast_ms','receiver_ms','acquisition_ms','age_s','full_age_s']}
            summary['timely_by_speed']={str(v):sum(r['fast_conditional_stop']=='True' and float(r['speed'])==v for r in rows) for v in [0.,.5,1.]}
        report[folder]=summary
    report.update(validation='passed',source_backed_packets=checked,physical_movement_authorized=0,scope='Conditional computational artifact; supplied contracts are not physical calibration.')
    (a.results/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
