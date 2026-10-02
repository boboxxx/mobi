#!/usr/bin/env python3
"""Independent ungrouped ball-tree audit; does not load native raster or stream."""
import argparse, gzip, hashlib, importlib.util, json, math, sys, zlib
from collections import defaultdict
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('old_independent_audit',ROOT/'experiments/continuity_recovery_20261002/analyze.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
body=audit.body


def decompress(blob):
    assert blob[:9]==b'MOBICV1Z\0' and len(blob)<=2_100_000
    d=zlib.decompressobj();out=d.decompress(blob[9:],2_100_001)
    assert len(out)<=2_100_000 and d.eof and not d.unconsumed_tail and not d.unused_data
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True)
    ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--previous',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();study=json.loads((a.results/'study/analysis.json').read_bytes())
    assert len(study['maintenance'])==360 and len(study['rows'])==72 and len(study['contexts'])==6
    for f,h in study['source_sha256'].items():assert audit.sha(ROOT/f)==h,f
    for f,h in study['input_sha256'].items():
        p=a.capture/Path(f).relative_to('results/online_evidence_20261002/live');assert audit.sha(p)==h,f
    assert study['previous_sha256']==audit.sha(a.previous)
    assert study['protocol_sha256']==audit.sha(Path(__file__).with_name('PROTOCOL.md'))
    build=json.loads((a.results/'build.json').read_bytes());assert study['library_sha256']==build['binary_sha256']
    assert build['source_sha256']==audit.sha(Path(__file__).with_name('raster.cpp'))
    assert build['included_cover_source_sha256']==audit.sha(ROOT/'experiments/usable_lease_20261002/cover.cpp')
    profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),
                  vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=body.Contract()
    prefix=0;raw_count=0;bundle_count=0;step_count=0;queues=0;costs=0;summary=[]
    for ctx in study['contexts']:
        name=ctx['run'];run=a.capture/name;record=json.loads(gzip.decompress((run/'record.json.gz').read_bytes()))
        decisions={x['id']:x for x in record['decisions']};old=audit.LegacyReceiver(profiles,contract,name,'Carla/Maps/Town10HD_Opt');regions={}
        for identity in ctx['prefix_ids']:
            d=decisions[identity];blob=(run/'packets'/(identity+'.json')).read_bytes();b=json.loads(blob)
            scope=body.Scope(name,old.frame_id,tuple(d['query']),b['raw']['payload']['scope']['plane_z'])
            motion=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
            assert old.accept(blob,scope,motion,d['receiver_check_time'])
            p,_,_=audit.full_check(b['raw'],profiles,contract,scope,motion,prior=regions[b['prior']] if b['prior'] else None)
            key=hashlib.sha256(blob).hexdigest();low,high,margin=body.envelope(motion,p['horizon_us']/1e6,.02)
            regions[key]=body.Region(tuple(scope.query),motion.yaw,tuple(low),tuple(high),margin,p['reference_us']/1e6,(p['reference_us']+p['horizon_us'])/1e6,key,name);prefix+=1
        anchor=ctx['anchor'];assert key==anchor['identity'] and p['reference_us']==anchor['reference_us']
        assert p['reference_us']+p['horizon_us']==anchor['endpoint_us']
        for repeat in range(3):
            q=anchor['reference_us'];maint=[m for m in study['maintenance'] if m['run']==name and m['repeat']==repeat]
            assert [m['id'] for m in maint]==['drive_%03d'%i for i in range(20,40)]
            by_id={m['id']:m for m in maint}
            for m in maint:
                d=decisions[m['id']];assert m['ref_us']==math.ceil(d['stamp']*1e6)
                assert m['arrival_us']==m['ref_us']+math.ceil(d['acquisition_s']*1e6)
                assert m['start_us']==max(q,m['arrival_us']) and m['queue_wait_us']==m['start_us']-m['arrival_us']
                assert m['finish_us']==m['start_us']+math.ceil(m['generation_ms']*1000);q=m['finish_us'];queues+=1
                if repeat!=0:continue
                path=a.results/'study/source'/(name+'_'+m['id']+'.json')
                assert path.exists()==m['geometry']
                if not path.exists():continue
                raw=json.loads(path.read_bytes());p0,o,r=audit.full_check(raw,profiles,contract,scope,motion,known_center=True)
                assert p0['reference_us']==m['ref_us'] and p0['horizon_us']==475_000 and p0['sequence']==d['sequence']
                with np.load(run/'clouds'/(m['id']+'.npz')) as c:source=body.encode_source(c['xyz'],c['origin'],d['stamp'],d['stamp'])
                assert audit.ray_keys(o,r)<=audit.ray_keys(source[0],source[1])
                assert int(r[:,4].max())==int(source[1][:,4].max());raw_count+=1
            for row in [r for r in study['rows'] if r['run']==name and r['repeat']==repeat]:
                m=by_id[row['id']];d=decisions[row['id']]
                if row['method']=='stream_fixed':
                    assert row['ready_us']==m['finish_us']
                    end,prev=anchor['endpoint_us'],anchor['reference_us'];selected=[]
                    while prev<m['ref_us']:
                        eligible=[z for z in maint if prev<z['ref_us']<end and z['ref_us']<=m['ref_us']]
                        if not eligible:break
                        z=max(eligible,key=lambda z:z['ref_us']);selected.append(z);prev=z['ref_us'];end=prev+475_000
                    assert [z['id'] for z in selected]==row['planned_ids']
                    assert row['cached_work_ms']==sum(z['generation_ms'] for z in selected)
                    assert row['geometry']==bool(prev==m['ref_us'] and all(z['geometry'] for z in selected))
                else:
                    assert row['method']=='cold_native'
                    assert row['ready_us']==m['arrival_us']+math.ceil(row['current_generation_ms']*1000)
                assert row['wire_ms']==20+row['bytes']*8/20_000
                total=(row['ready_us']-m['ref_us'])/1000+row['assembly_ms']+row['verification_ms']+row['wire_ms']
                assert row['total_ms']==total and row['age_us']==max(50_000,math.ceil(total/50)*50_000)
                assert row['hypothetical_action_pass']==bool(row['geometry'] and row['age_us']+200_000<475_000)
                assert row['action_slack_us']==(475_000-row['age_us']-200_000 if row['geometry'] else None);costs+=1
                if not row['geometry'] or repeat!=0:continue
                packet=(a.results/'study/packets'/(name+'_'+row['id']+'_'+row['method']+'.bin')).read_bytes()
                assert len(packet)==row['bytes'];blob=decompress(packet);assert len(blob)==row['raw_bytes'];b=json.loads(blob)
                if row['method']=='cold_native':audit.full_check(b['raw'],profiles,contract,scope,motion)
                else:
                    assert b['anchor']==key and b['kind']=='center-continuity-v1' and b['dynamics']=='observation-speed-age-v1'
                    assert len(b['steps'])==row['steps']<=32
                    end,prev,seq=anchor['endpoint_us'],anchor['reference_us'],anchor['sequence']
                    for raw,identity in zip(b['steps'],row['planned_ids']):
                        assert body.canonical(raw)==(a.results/'study/source'/(name+'_'+identity+'.json')).read_bytes()
                        p0,_,_=audit.full_check(raw,profiles,contract,scope,motion,known_center=True)
                        assert prev<p0['reference_us']<end and p0['sequence']>seq and p0['reference_us']+p0['horizon_us']>end
                        prev,end,seq=p0['reference_us'],p0['reference_us']+p0['horizon_us'],p0['sequence'];step_count+=1
                    assert prev==m['ref_us'] and end==prev+475_000
                bundle_count+=1
        groups=defaultdict(list)
        for row in study['rows']:
            if row['run']==name:groups[(row['id'],row['method'])].append(row)
        for (identity,method),g in groups.items():
            assert len(g)==3 and len({x['geometry'] for x in g})==1
            x=dict(run=name,id=identity,method=method,geometry=g[0]['geometry'],action_passes=sum(r['hypothetical_action_pass'] for r in g))
            for f in ['bytes','raw_bytes','assembly_ms','verification_ms','total_ms','age_us','action_slack_us']:
                x[f+'_median']=float(np.median([r[f] for r in g])) if g[0][f] is not None else None
            summary.append(x)
    result=dict(prefix_packet_checks=prefix,source_step_checks=raw_count,bundle_checks=bundle_count,
                bundle_step_checks=step_count,queue_rows=queues,cost_rows=costs,summaries=summary,
                analyzer_sha256=audit.sha(Path(__file__)),scope='Independent raw-source/ungrouped ball-tree/full-grid/strict temporal/queue/cost replay; first-repeat saved proof geometry only; no physical/closed-loop/WCET inference.')
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['prefix_packet_checks','source_step_checks','bundle_checks','bundle_step_checks','queue_rows','cost_rows']}))


if __name__=='__main__':main()
