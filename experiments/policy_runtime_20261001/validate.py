#!/usr/bin/env python3
import argparse,csv,hashlib,json,math
from pathlib import Path
import numpy as np
from incremental import pp,Verifier,timing_after_verified
from binary_proof import decode as binary_decode,BinaryVerifier,timing_after_verified as binary_timing
from strict_policy import verify as strict_verify


def read(path):return list(csv.DictReader(path.open()))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--previous',type=Path,required=True);a=ap.parse_args();src=Path(__file__).parent;report={}
    profiles=dict(small=pp.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=pp.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=pp.Contract();policy=pp.Policy()
    old={r['id']:r for r in read(a.previous/'renewal/renewal.csv')};frames={r['id']:r for r in read(a.capture/'frames.csv')};source_backed=set();decoded={}
    for folder,protocol in [('ablation','PROTOCOL.md'),('binary','BINARY_PROTOCOL.md'),('proposal','PROPOSAL_PROTOCOL.md')]:
        root=a.results/folder;manifest=json.loads((root/'manifest.json').read_text());rows=read(root/'ablation.csv')
        assert len(rows)==manifest['rows'] and manifest['cases']==1044
        for name,digest in manifest['source_sha256'].items():assert sha(src/name)==digest,(folder,name)
        assert sha(src/protocol)==manifest['protocol_sha256']
        for name,digest in manifest['input_sha256'].items():assert sha(a.capture/'clouds'/name)==digest
        for name,digest in manifest['template_sha256'].items():assert sha(a.previous/'geometry/packets'/name)==digest
        assert sha(a.capture/'frames.csv')==manifest['frames_sha256'] and sha(a.previous/'renewal/renewal.csv')==manifest['reference_csv_sha256']
        modes=sorted({r['mode'] for r in rows});out={};hashes={}
        for row in rows:
            mode=row['mode'];identifier=row['id'];positive=old[identifier]['geometry']=='True';assert (row['geometry']=='True')==positive
            assert row['physical_movement_authorized']=='False'
            equal='byte_equal' if folder=='ablation' else 'semantic_equal';assert row[equal]=='True'
            expected=a.previous/'renewal/packets'/(identifier+'.json');emitted=bool(row['packet_sha256'])
            if folder=='proposal':assert emitted==(row['emitted']=='True')
            else:assert emitted==positive
            if not emitted:
                assert row['conditional_stop']==row['plus_1ms_conditional_stop']=='False';continue
            is_binary=mode.startswith('binary');path=root/'packets'/(identifier+'.pvx') if is_binary else expected
            blob=path.read_bytes();assert hashlib.sha256(blob).hexdigest()==row['packet_sha256']
            if 'packet_bytes' in row:assert len(blob)==int(row['packet_bytes'])
            hashes.setdefault(identifier,{}).setdefault(is_binary,set()).add(row['packet_sha256'])
            data=np.load(a.capture/'clouds'/(row['cloud']+'.npz'));q=data['query'];origin=data['origin'];lat=origin[:2]-q;yaw=math.atan2(-lat[0],lat[1]);speed=float(row['speed']);horizon=float(row['horizon']);stamp=float(row['reference']);density,layout,scenario,_=row['cloud'].split('_')
            scope=pp.Scope('policy-renew:'+density+':'+layout+':'+scenario,'Town10HD_Opt/world',tuple(q),float(data['probe_z']))
            if is_binary:p,o,r=binary_decode(blob,profiles,scope,contract,policy,speed,yaw)
            else:p,o,r=pp.decode(pp.canonical(json.loads(blob)['raw']),profiles,scope,contract)
            if (folder,identifier,is_binary) not in source_backed:
                so,sr,ref=pp.encode_source(data['xyz'],origin,stamp,stamp);assert np.array_equal(so,o) and ref==p['reference_us'];source=set(map(tuple,sr));assert all(tuple(x) in source for x in r)
                valid=(BinaryVerifier(False).verify(blob,profiles,scope,contract,policy,speed,yaw,stamp+.02) if is_binary else strict_verify(blob,profiles,scope,contract,policy,speed,yaw,stamp+.02))
                assert valid==positive
                if positive and is_binary:
                    op,oo,orr=pp.decode(pp.canonical(json.loads(expected.read_bytes())['raw']),profiles,scope,contract)
                    assert np.array_equal(o,oo) and np.array_equal(r,orr) and all(p[k]==op[k] for k in ['reference_us','horizon_us','sequence'])
                source_backed.add((folder,identifier,is_binary))
            expected_age=(float(row['acquisition_ms'])+float(row['generation_ms'])+float(row['verification_ms'])+float(row['bookkeeping_ms']))/1000+.02
            assert abs(expected_age-float(row['age_s']))<1e-12 and float(row['acquisition_ms'])==float(frames[row['cloud']]['acquisition_ms'])
            timing=binary_timing if is_binary else timing_after_verified
            for column,extra in [('conditional_stop',0.),('plus_1ms_conditional_stop',.001)]:
                actual=positive and timing(blob,policy,speed,stamp+float(row['age_s'])+extra);assert actual==(row[column]=='True')
        for case in hashes.values():assert all(len(v)==1 for v in case.values())
        for mode in modes:
            subset=[r for r in rows if r['mode']==mode];assert len(subset)==1044;p=[r for r in subset if r['geometry']=='True']
            out[mode]=dict(cases=len(subset),geometry=len(p),emitted=sum(bool(r['packet_sha256']) for r in subset),conditional_stop=sum(r['conditional_stop']=='True' for r in subset),plus_1ms_conditional_stop=sum(r['plus_1ms_conditional_stop']=='True' for r in subset),timely_by_speed={str(v):sum(r['conditional_stop']=='True' and float(r['speed'])==v for r in subset) for v in [0.,.5,1.]},median_on_geometry_positive={k:float(np.median([float(r[k]) for r in p])) for k in ['generation_ms','verification_ms','age_s']})
            if 'packet_bytes' in subset[0]:out[mode].update(total_bytes=sum(int(r['packet_bytes']) for r in subset),rejected_bytes=sum(int(r['packet_bytes']) for r in subset if r['geometry']=='False'),median_packet_bytes=float(np.median([int(r['packet_bytes']) for r in p])))
        report[folder]=out
    m=json.loads((a.results/'perturbation/manifest.json').read_text());rows=read(a.results/'perturbation/perturbation.csv');assert len(rows)==m['cases']==120
    for name,digest in m['source_sha256'].items():assert sha(src/name)==digest
    assert sha(src/'PERTURBATION_PROTOCOL.md')==m['protocol_sha256']
    assert sha(a.previous/'geometry/packets/dense_0_free_00_v0.5_h0.4.json')==m['template_sha256']
    assert all(r['all_equal']=='True' and len({r[k] for k in ['reference','hints','binary_full','binary_hints']})==1 for r in rows)
    report['perturbation']=dict(cases=120,positive=sum(r['reference']=='True' for r in rows),all_equal=True)
    report.update(validation='passed',source_backed_stage_bundle_checks=len(source_backed),physical_movement_authorized=0,scope='Conditional proof correctness and finite timing diagnostics; no physical calibration or evidence-guided driving.')
    (a.results/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
