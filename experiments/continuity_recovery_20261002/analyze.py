#!/usr/bin/env python3
"""Independent full-grid/ball-neighborhood backfill verifier; no sender import."""
import argparse, copy, gzip, hashlib, json, math, sys
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiments/evidence_loop_20261001'))
from fast_path import body,Receiver as LegacyReceiver


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def full_check(raw,profiles,contract,scope,motion,known_center=False,prior=None):
    p,o,r=body.decode(body.canonical(raw),profiles,scope,contract)
    result=body.projections(o,r,p['reference_us'],profiles,scope,contract)
    latest_age=(p['reference_us']-int(r[:,4].max()))/body.TIME_SCALE
    assert latest_age>=0
    for n,profile in profiles.items():
        effective=replace(profile,speed=profile.speed+profile.acceleration*latest_age)
        cells=body.required(effective,motion,p['horizon_us']/body.TIME_SCALE)
        assert cells is not None
        if known_center:
            low,high,margin=body.envelope(motion,0.,profile.clock)
            known=body.box_distance(cells,low,high)+profile.step/math.sqrt(2)<margin+profile.r_max-1e-9
        else:
            known=body.prior_covers(cells,scope,motion,prior,profile,p['reference_us']/body.TIME_SCALE)
        cells=cells[~known]
        v=result[n];w=v['witnesses']@body.rotation(motion.yaw)
        radii=profile.r_min-v['error']-profile.step/math.sqrt(2)-1e-9
        ok=radii>0;w,radii=w[ok],radii[ok]
        if not len(cells):continue
        assert len(w)>0
        # One ungrouped tree, enumerate every possible local ball witness and
        # test its individual STRICT radius; independent of sender bin queries.
        neighbors=cKDTree(w).query_ball_point(cells,float(radii.max()))
        lengths=np.fromiter((len(x) for x in neighbors),dtype=np.int64,count=len(cells))
        assert np.all(lengths>0)
        witness=np.concatenate(neighbors).astype(np.int64,copy=False)
        center=np.repeat(np.arange(len(cells)),lengths)
        valid=np.linalg.norm(cells[center]-w[witness],axis=1)<radii[witness]
        covered=np.zeros(len(cells),dtype=bool);covered[center[valid]]=True
        assert covered.all()
    return p,o,r


def ray_keys(o,r):return {tuple(o[x[0]])+tuple(x[1:]) for x in r}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True)
    ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();study=json.loads((a.results/'study/analysis.json').read_bytes())
    assert len(study['contexts'])==12 and len(study['rows'])==144
    for f,h in study['source_sha256'].items():assert sha(ROOT/f)==h,f
    for f,h in study['input_sha256'].items():
        p=a.capture/Path(f).relative_to('results/online_evidence_20261002/live');assert sha(p)==h,f
    for field,name in [('protocol_sha256','PROTOCOL.md'),('model_addendum_sha256','MODEL_ADDENDUM.md')]:
        assert study[field]==sha(Path(__file__).with_name(name))
    assert study['library_sha256']==json.loads((a.results/'build_dependency.json').read_bytes())['binary_sha256']
    profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),
                  vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=body.Contract()
    prefix_checks=0;bundle_checks=0;step_checks=0;cost_rows=0;summaries=[];cache={}
    for ctx in study['contexts']:
        name=ctx['run'];run=a.capture/name
        record=json.loads(gzip.decompress((run/'record.json.gz').read_bytes()))
        decisions={x['id']:x for x in record['decisions']};target=decisions[ctx['id']]
        assert target==ctx['target'] and not target['geometry']
        if name not in cache:
            rx=LegacyReceiver(profiles,contract,name,'Carla/Maps/Town10HD_Opt');regions={};last=None
            for identity in ctx['prefix_ids']:
                d=decisions[identity];blob=(run/'packets'/(identity+'.json')).read_bytes();b=json.loads(blob)
                scope=body.Scope(name,rx.frame_id,tuple(d['query']),b['raw']['payload']['scope']['plane_z'])
                motion=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
                assert d['receiver_accepted'] and rx.accept(blob,scope,motion,d['receiver_check_time'])
                prior=regions[b['prior']] if b['prior'] else None
                p,_,_=full_check(b['raw'],profiles,contract,scope,motion,prior=prior)
                low,high,margin=body.envelope(motion,p['horizon_us']/body.TIME_SCALE,.02)
                key=hashlib.sha256(blob).hexdigest()
                regions[key]=body.Region(tuple(scope.query),motion.yaw,tuple(low),tuple(high),margin,
                                          p['reference_us']/body.TIME_SCALE,(p['reference_us']+p['horizon_us'])/body.TIME_SCALE,key,name)
                last=(key,scope,motion,p);prefix_checks+=1
            cache[name]=last
        key,scope,motion,anchor=cache[name]
        assert key==ctx['anchor_packet_sha256'] and ctx['anchor']['identity']==key
        assert ctx['anchor']['reference_us']==anchor['reference_us']
        assert ctx['anchor']['endpoint_us']==anchor['reference_us']+anchor['horizon_us']
        expected_buffer=[d['id'] for d in record['decisions'] if anchor['reference_us']<math.ceil(d['stamp']*1e6)<=math.ceil(target['stamp']*1e6)]
        assert ctx['buffer_ids']==expected_buffer
        groups=defaultdict(list)
        for row in study['rows']:
            if (row['run'],row['id'])!=(name,ctx['id']):continue
            groups[row['method']].append(row)
            cost=sum(row[k] for k in ['generation_ms','verification_ms','acquisition_ms','wire_ms'])
            ticks=max(50_000,math.ceil(cost/50)*50_000);ref=math.ceil(target['stamp']*1e6)
            assert row['wire_ms']==20+row['bytes']*8/20_000
            assert row['acquisition_ms']==target['acquisition_s']*1000 and row['age_us']==ticks
            assert row['usable_us']==(row['endpoint_us']-ref-math.ceil(cost*1000) if row['geometry'] else None)
            assert row['action_slack_us']==(row['endpoint_us']-ref-ticks-200_000 if row['geometry'] else None)
            assert row['hypothetical_action_pass']==bool(row['geometry'] and ref+ticks+200_000<row['endpoint_us'])
            cost_rows+=1
            if not row['geometry']:
                assert row['bytes']==0 and row['steps']==0;continue
            if row['repeat']!=0:continue
            blob=(a.results/'study/packets'/(name+'_'+ctx['id']+'_'+row['method']+'.json')).read_bytes()
            assert len(blob)==row['bytes']<=2_100_000;b=json.loads(blob)
            if row['method']=='current_full':
                full_check(b['raw'],profiles,contract,scope,motion);bundle_checks+=1;continue
            assert b['kind']=='center-continuity-v1' and b['dynamics']=='observation-speed-age-v1' and b['anchor']==key
            assert 1<=len(b['steps'])<=32 and len(b['steps'])==row['steps']
            previous,end,seq=anchor['reference_us'],anchor['reference_us']+anchor['horizon_us'],anchor['sequence']
            assert len(row['diagnostics']['planned_ids'])==len(b['steps'])
            for raw,identity in zip(b['steps'],row['diagnostics']['planned_ids']):
                d=decisions[identity];p,o,r=full_check(raw,profiles,contract,scope,motion,known_center=True)
                assert previous<p['reference_us']<end and p['sequence']>seq and p['reference_us']+p['horizon_us']>end
                assert p['reference_us']==math.ceil(d['stamp']*1e6) and p['sequence']==d['sequence']
                with np.load(run/'clouds'/(identity+'.npz')) as cloud:
                    source=body.encode_source(cloud['xyz'],cloud['origin'],d['stamp'],d['stamp'])
                assert ray_keys(o,r)<=ray_keys(source[0],source[1])
                assert int(r[:,4].max())==int(source[1][:,4].max())
                previous,end,seq=p['reference_us'],p['reference_us']+p['horizon_us'],p['sequence'];step_checks+=1
            assert previous==ref and end==row['endpoint_us'] and end==ref+475_000
            bundle_checks+=1
        assert set(groups)=={'current_full','nearest_fixed','greedy_fixed','greedy_bridges'}
        for method,g in groups.items():
            assert len(g)==3 and len({r['geometry'] for r in g})==1
            x=dict(run=name,id=ctx['id'],method=method,geometry=g[0]['geometry'],action_passes=sum(r['hypothetical_action_pass'] for r in g),diagnostics=g[0]['diagnostics'])
            for field in ['generation_ms','verification_ms','bytes','steps','usable_us','action_slack_us']:
                x[field+'_median']=float(np.median([r[field] for r in g])) if g[0][field] is not None else None
            summaries.append(x)
    result=dict(prefix_packet_checks=prefix_checks,bundle_checks=bundle_checks,raw_step_checks=step_checks,
                arithmetic_rows=cost_rows,summaries=summaries,analyzer_sha256=sha(Path(__file__)),
                scope='Independent ball-neighborhood/full-required-cell and original-source replay; saved first repeats only; observed hypothetical timing, no physical or control guarantee.')
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['prefix_packet_checks','bundle_checks','raw_step_checks','arithmetic_rows']}))


if __name__=='__main__':main()
