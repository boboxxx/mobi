#!/usr/bin/env python3
import argparse,gzip,hashlib,json,math,socket,sys,time
from pathlib import Path
import numpy as np
from shell_frontier import body,frontier as shell,ordered
from frontier import frontier as full
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'evidence_loop_20261001'))
from fast_path import Receiver


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--reference',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(exist_ok=False)
    reference=json.loads(a.reference.read_text());selected={(x['run'],x['id'],x['kind']):x for x in reference['rows']}
    profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=body.Contract();rows=[]
    for f in sorted(a.capture.glob('*/record.json.gz')):
        r=json.loads(gzip.decompress(f.read_bytes()));rx=Receiver(profiles,contract,r['run'],'Carla/Maps/Town10HD_Opt')
        for d in r['decisions']:
            cl=np.load(f.parent/'clouds'/(d['id']+'.npz'));s=body.Scope(r['run'],'Carla/Maps/Town10HD_Opt',tuple(d['query']),float(cl['plane_z']));m=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
            prior=rx.latest_region()
            if prior and not (prior.established<=d['stamp'] and math.ceil(d['stamp']*1e6)<rx._deadlines[prior.identity]):prior=None
            assert (prior.identity if prior else None)==d['prior']
            blob=(f.parent/'packets'/(d['id']+'.json')).read_bytes() if d['geometry'] else None
            alternatives=[]
            if (r['run'],d['id'],'all_observed_rays') in selected:
                o,rays,ref=body.encode_source(cl['xyz'],cl['origin'],d['stamp'],d['stamp']);alternatives.append(('all_observed_rays',o,rays,ref))
            if (r['run'],d['id'],'transmitted_subset') in selected:
                p,o,rays=body.decode(body.canonical(json.loads(blob)['raw']),profiles,s,contract);alternatives.append(('transmitted_subset',o,rays,p['reference_us']))
            for kind,o,rays,ref in alternatives:
                expected=selected[(r['run'],d['id'],kind)]['frontier'];last=None
                for repeat in range(3):
                    costs={};answers={}
                    for name in (['full','shell'] if repeat%2==0 else ['shell','full']):
                        if repeat==0:ordered.cache_clear()
                        begin=time.perf_counter();result=body.projections(o,rays,ref,profiles,s,contract)
                        answer=(full if name=='full' else shell)(result,profiles,s,m,prior,ref/1e6)
                        costs[name]=(time.perf_counter()-begin)*1000;answers[name]=answer
                        assert answer['horizon_us']==expected['horizon_us'],(r['run'],d['id'],kind,name,answer,expected)
                    for n,v in answers['shell']['classes'].items():
                        distance=v['nearest_unexcluded_distance_m']
                        if distance is not None:assert distance==answers['full']['classes'][n]['nearest_unexcluded_distance_m']
                    row=dict(run=r['run'],id=d['id'],kind=kind,repeat=repeat,cold_ordered_index=repeat==0,
                        full_ms=costs['full'],shell_ms=costs['shell'],horizon_us=expected['horizon_us'],
                        cells_examined=sum(v['cells_examined'] for v in answers['shell']['classes'].values()),
                        reference_grid_cells=sum(v['unexcluded_cells']*0+round(2*profiles[n].domain/profiles[n].step)**2 for n,v in answers['full']['classes'].items()))
                    rows.append(row);print(json.dumps(row),flush=True)
            if d['receiver_accepted']:assert rx.accept(blob,s,m,d['receiver_check_time'])
    assert len(rows)==37*3
    report=dict(host=socket.gethostname(),rows=rows,equivalent_cases=37,comparison_calls=len(rows)*2,scope='All prior archived cases, cold/warm index measurements under equal one-thread library setting; no WCET or new independent scenarios.',source_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),Path(__file__).with_name('shell_frontier.py')]})
    (a.out/'analysis.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
