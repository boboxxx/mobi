#!/usr/bin/env python3
"""Independent fine-grid reconstruction using already audited coarse root facts."""
import argparse,hashlib,json,math
from dataclasses import replace
from pathlib import Path
import numpy as np
import analyze as audit
body=audit.body


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();s=json.loads((a.results/'refined/analysis.json').read_bytes());old=json.loads((a.results/'study/analysis.json').read_bytes())
    val=json.loads((a.results/'validation.json').read_bytes())
    assert val['prefix_packet_checks']==252 and val['state_mask_checks']==36 and val['analyzer_sha256']==audit.audit.sha(Path(audit.__file__))
    assert s['baseline_sha256']==audit.audit.sha(a.results/'study/analysis.json') and len(s['rows'])==12
    assert s['source_study_sha256']==audit.audit.sha(a.source/'study/analysis.json')
    for f,h in s['loaded_additional_sources'].items():assert audit.audit.sha(audit.ROOT/f)==h,f
    assert s['protocol_sha256']==audit.audit.sha(Path(__file__).with_name('REFINEMENT_PROTOCOL.md'))
    original=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.))
    grid={n:replace(p,step=p.step/2) for n,p in original.items()};contract=body.Contract()
    pipeline=json.loads((a.source/'study/analysis.json').read_bytes());mask_checks=0;propagations=0;source_checks=0;boundaries=0;costs=0;packets=0
    for ctx in old['contexts']:
        name=ctx['run'];run=a.capture/name;identity=ctx['prefix_ids'][-1]
        blob=json.loads((run/'packets'/(identity+'.json')).read_bytes());scope=body.Scope(**blob['raw']['payload']['scope']);motion=body.Motion(**blob['motion'])
        p,o,r=body.decode(body.canonical(blob['raw']),original,scope,contract);last_ref=p['reference_us'];last_seq=p['sequence']
        assert ctx['anchor']['reference_us']==last_ref
        v=body.projections(o,r,last_ref,original,scope,contract);eff={n:audit.effective(g,r,last_ref) for n,g in grid.items()};possible={}
        with np.load(a.results/'study/states'/(name+'_root.npz')) as coarse:
            for n,g in grid.items():possible[n]=np.repeat(np.repeat(coarse[n],2,axis=0),2,axis=1)&~audit.excluded(v[n],g,motion)
        with np.load(a.results/'refined/states'/(name+'_root.npz')) as stored:
            for n in grid:np.testing.assert_array_equal(possible[n],stored[n]);mask_checks+=1
        for index in range(20,40):
            identity='drive_%03d'%index;path=a.source/'study/source'/(name+'_'+identity+'.json');raw=json.loads(path.read_bytes())
            p,o,r=body.decode(body.canonical(raw),original,scope,contract);ref=p['reference_us'];assert last_ref<ref and p['sequence']>last_seq
            v=body.projections(o,r,ref,original,scope,contract);dt=(ref-last_ref)/1e6
            for n,g in grid.items():
                possible[n]=audit.propagate_tree(possible[n],g,body.travel(dt,eff[n]))&~audit.excluded(v[n],g,motion)
                eff[n]=audit.effective(g,r,ref);propagations+=1
            last_ref,last_seq=ref,p['sequence'];source_checks+=1
            if index not in [25,39]:continue
            row=next(x for x in s['rows'] if x['run']==name and x['id']==identity);h=row['horizon_us']
            with np.load(a.results/'refined/states'/(name+'_'+identity+'.npz')) as stored:
                for n in grid:np.testing.assert_array_equal(possible[n],stored[n]);mask_checks+=1
            assert all(audit.support(possible[n],eff[n],motion,h) for n in grid) if h else True
            assert not all(audit.support(possible[n],eff[n],motion,h+1) for n in grid);boundaries+=1+int(h>0)
            for n,g in grid.items():
                info=row['decision']['classes'][n];assert info['possible_cells']==int(possible[n].sum())
                c=body.grid(g.domain,g.step)[0][possible[n].ravel()];low,high,_=body.envelope(motion,0.,g.clock)
                assert info['nearest_possible_distance_m']==float(body.box_distance(c,low,high).min())
            ids=['drive_%03d'%i for i in range(20,index+1)];assert row['source_ids']==ids and row['grid_factor']==2
            for f,digest in row['source_sha256'].items():assert audit.audit.sha(audit.ROOT/f)==digest,f
            m=[x for x in pipeline['maintenance'] if x['run']==name and x['repeat']==0 and x['id'] in ids]
            assert row['ready_us']==m[-1]['finish_us'] and row['charged_source_work_ms']==sum(x['generation_ms'] for x in m)
            import zlib
            transport=(a.results/'refined/packets'/(name+'_'+identity+'.bin')).read_bytes();assert len(transport)==row['bytes'] and transport[:9]==b'MOBICV1Z\0'
            z=zlib.decompressobj();data=z.decompress(transport[9:],2_100_001);assert z.eof and not z.unused_data and not z.unconsumed_tail and len(data)==row['raw_bytes']<=2_100_000
            packet=json.loads(data);assert packet['kind']=='position-observations-v1' and packet['anchor']==ctx['anchor']['identity'] and packet['dynamics']=='observation-speed-age-v1'
            assert packet['steps']==[json.loads((a.source/'study/source'/(name+'_'+x+'.json')).read_bytes()) for x in ids];packets+=1
            assert row['wire_ms']==20+row['bytes']*8/20_000
            total=(row['ready_us']-ref)/1000+row['assembly_ms']+row['verification_ms']+row['wire_ms'];assert total==row['total_ms'] and row['age_us']==max(50000,math.ceil(total/50)*50000)
            assert row['geometry']==(h>0) and row['horizon475_pass']==(h>=475000)
            assert row['timely475']==bool(h>=475000 and row['age_us']+200000<475000)
            assert row['timely_max']==bool(h>0 and row['age_us']+200000<h);costs+=1
    result=dict(revalidated_coarse_root_packets=val['prefix_packet_checks'],independent_fine_propagations=propagations,source_step_checks=source_checks,
                state_mask_checks=mask_checks,saved_packet_checks=packets,frontier_boundary_checks=boundaries,cost_rows=costs,
                analyzer_sha256=audit.audit.sha(Path(__file__)),coarse_validation_sha256=audit.audit.sha(a.results/'validation.json'),
                scope='Independent fine-grid ball/vertex tree rebuild from separately fully audited coarse roots; all12 packets/masks/costs; unchanged source/physical contract, representation sensitivity only.')
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
