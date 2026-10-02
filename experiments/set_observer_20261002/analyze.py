#!/usr/bin/env python3
"""Independent ball/vertex-KD-tree set reconstruction; no observer/native import."""
import argparse,gzip,hashlib,importlib.util,json,math
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('source_audit',ROOT/'experiments/continuity_recovery_20261002/analyze.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit);body=audit.body
grid_cache={}


def effective(profile,rays,ref):return replace(profile,speed=profile.speed+profile.acceleration*(ref-int(rays[:,4].max()))/1e6)


def excluded(result,profile,motion):
    key=(profile.domain,profile.step)
    if key not in grid_cache:
        c=body.grid(*key)[0];grid_cache[key]=(c,cKDTree(c))
    c,tree=grid_cache[key];xy=result['witnesses']@body.rotation(motion.yaw)
    radii=profile.r_min-result['error']-profile.step/math.sqrt(2)-1e-9
    use=radii>0;xy,radii=xy[use],radii[use];mask=np.zeros(len(c),dtype=bool)
    if len(xy):
        found=tree.query_ball_point(xy,radii);lengths=np.fromiter((len(x) for x in found),dtype=np.int64,count=len(found))
        if lengths.sum():
            index=np.concatenate(found).astype(np.int64);witness=np.repeat(np.arange(len(xy)),lengths)
            strict=np.linalg.norm(c[index]-xy[witness],axis=1)<radii[witness];mask[index[strict]]=True
    n=round(2*profile.domain/profile.step);return mask.reshape(n,n)


def propagate_tree(possible,profile,distance):
    n=len(possible);vertices=np.zeros((n+1,n+1),dtype=bool)
    vertices[:-1,:-1]|=possible;vertices[1:,:-1]|=possible;vertices[:-1,1:]|=possible;vertices[1:,1:]|=possible
    target=np.indices((n+1,n+1)).reshape(2,-1).T*profile.step
    if vertices.any():
        nearest=cKDTree(np.argwhere(vertices)*profile.step).query(target,k=1)[0].reshape(n+1,n+1)
        d=np.minimum(np.minimum(nearest[:-1,:-1],nearest[1:,:-1]),np.minimum(nearest[:-1,1:],nearest[1:,1:]))
        reached=d<=distance+1e-9
    else:reached=np.zeros_like(possible)
    centers=body.grid(profile.domain,profile.step)[0]
    boundary=profile.domain-np.maximum(np.abs(centers[:,0]),np.abs(centers[:,1]))-profile.step/2
    return reached|(boundary.reshape(n,n)<=distance+1e-9)


def support(possible,profile,motion,h):
    if h<1:return False
    c=body.required(profile,motion,h/1e6)
    if c is None:return False
    axis=-profile.domain+.5*profile.step;loc=np.rint((c-axis)/profile.step).astype(int)
    return not possible[loc[:,0],loc[:,1]].any()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();study=json.loads((a.results/'study/analysis.json').read_bytes());prior=json.loads((a.source/'study/analysis.json').read_bytes())
    assert len(study['rows'])==72 and len(study['contexts'])==6
    for f,h in study['source_sha256'].items():assert audit.sha(ROOT/f)==h,f
    for f,h in study['input_sha256'].items():assert audit.sha(ROOT/f)==h,f
    assert study['source_study_sha256']==audit.sha(a.source/'study/analysis.json')
    assert study['protocol_sha256']==audit.sha(Path(__file__).with_name('PROTOCOL.md'))
    build=json.loads((a.results/'build.json').read_bytes());assert study['library_sha256']==build['binary_sha256'] and build['source_sha256']==audit.sha(Path(__file__).with_name('mask.cpp'))
    profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=body.Contract()
    prefixes=0;source_steps=0;propagations=0;state_checks=0;packets=0;costs=0;boundaries=0;summaries=[]
    for ctx in study['contexts']:
        name=ctx['run'];run=a.capture/name;record=json.loads(gzip.decompress((run/'record.json.gz').read_bytes()));decisions={d['id']:d for d in record['decisions']}
        legacy=audit.LegacyReceiver(profiles,contract,name,'Carla/Maps/Town10HD_Opt');regions={}
        for identity in ctx['prefix_ids']:
            d=decisions[identity];blob=(run/'packets'/(identity+'.json')).read_bytes();b=json.loads(blob)
            scope=body.Scope(name,legacy.frame_id,tuple(d['query']),b['raw']['payload']['scope']['plane_z'])
            motion=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
            assert legacy.accept(blob,scope,motion,d['receiver_check_time'])
            p,o,r=audit.full_check(b['raw'],profiles,contract,scope,motion,prior=regions[b['prior']] if b['prior'] else None)
            key=hashlib.sha256(blob).hexdigest();low,high,margin=body.envelope(motion,p['horizon_us']/1e6,.02)
            regions[key]=body.Region(tuple(scope.query),motion.yaw,tuple(low),tuple(high),margin,p['reference_us']/1e6,(p['reference_us']+p['horizon_us'])/1e6,key,name);prefixes+=1
        assert key==ctx['anchor']['identity'];last_ref=p['reference_us'];last_seq=p['sequence'];eff={n:effective(profile,r,last_ref) for n,profile in profiles.items()}
        v=body.projections(o,r,last_ref,profiles,scope,contract);possible={}
        for n,profile in profiles.items():
            cells=body.grid(profile.domain,profile.step)[0];required=body.required(eff[n],motion,p['horizon_us']/1e6)
            proved=np.zeros(len(cells),dtype=bool);axis=-profile.domain+.5*profile.step
            loc=np.rint((required-axis)/profile.step).astype(int);size=round(2*profile.domain/profile.step)
            proved[loc[:,0]*size+loc[:,1]]=True
            possible[n]=(~proved).reshape(size,size)&~excluded(v[n],profile,motion)
        with np.load(a.results/'study/states'/(name+'_root.npz')) as stored:
            for n in profiles:np.testing.assert_array_equal(possible[n],stored[n]);state_checks+=1
        all_raw={};exclusions={};computed={}
        for index in range(20,40):
            identity='drive_%03d'%index;path=a.source/'study/source'/(name+'_'+identity+'.json');raw=json.loads(path.read_bytes());all_raw[identity]=raw
            p,o,r=body.decode(body.canonical(raw),profiles,scope,contract);ref=p['reference_us'];d=decisions[identity]
            assert last_ref<ref and p['sequence']>last_seq and ref==math.ceil(d['stamp']*1e6)
            with np.load(run/'clouds'/(identity+'.npz')) as c:original=body.encode_source(c['xyz'],c['origin'],d['stamp'],d['stamp'])
            assert audit.ray_keys(o,r)<=audit.ray_keys(original[0],original[1]) and int(r[:,4].max())==int(original[1][:,4].max());source_steps+=1
            v=body.projections(o,r,ref,profiles,scope,contract);dt=(ref-last_ref)/1e6;exclusions[identity]={}
            for n,profile in profiles.items():
                prediction=propagate_tree(possible[n],profile,body.travel(dt,eff[n]));mask=excluded(v[n],profile,motion)
                possible[n]=prediction&~mask;exclusions[identity][n]=mask;eff[n]=effective(profile,r,ref);propagations+=1
            last_ref,last_seq=ref,p['sequence']
            if index not in [25,39]:continue
            with np.load(a.results/'study/states'/(name+'_'+identity+'.npz')) as stored:
                for n in profiles:np.testing.assert_array_equal(possible[n],stored[n]);state_checks+=1
            rows=[x for x in study['rows'] if x['run']==name and x['id']==identity and x['method']=='position_set']
            assert len(rows)==3 and len({x['horizon_us'] for x in rows})==1;h=rows[0]['horizon_us']
            assert all(support(possible[n],eff[n],motion,h) for n in profiles) if h else True
            assert not all(support(possible[n],eff[n],motion,h+1) for n in profiles);boundaries+=1+int(h>0)
            for row in rows:
                for n in profiles:
                    info=row['decision']['classes'][n];assert info['possible_cells']==int(possible[n].sum())
                    c=body.grid(profiles[n].domain,profiles[n].step)[0][possible[n].ravel()];low,high,_=body.envelope(motion,0.,profiles[n].clock)
                    dist=body.box_distance(c,low,high);assert info['nearest_possible_distance_m']==float(dist.min())
            computed[identity]=h
        for row in [x for x in study['rows'] if x['run']==name]:
            d=decisions[row['id']];ref=math.ceil(d['stamp']*1e6);ids=['drive_%03d'%i for i in range(20,d['index']+1)];assert row['source_ids']==ids
            maintenance=[x for x in prior['maintenance'] if x['run']==name and x['repeat']==row['repeat'] and x['id'] in ids]
            assert row['ready_us']==maintenance[-1]['finish_us'] and row['charged_source_work_ms']==sum(x['generation_ms'] for x in maintenance)
            if row['method']=='fixed_K':
                end,previous,seq=ctx['anchor']['endpoint_us'],ctx['anchor']['reference_us'],ctx['anchor']['sequence'];valid=True
                for identity in ids:
                    p=all_raw[identity]['payload']
                    if not previous<p['reference_us']<end or p['sequence']<=seq or p['reference_us']+p['horizon_us']<=end:valid=False;break
                    for n,profile in profiles.items():
                        raw=all_raw[identity];p0,o,r=body.decode(body.canonical(raw),profiles,scope,contract)
                        c=body.required(effective(profile,r,p0['reference_us']),motion,p0['horizon_us']/1e6)
                        low,high,margin=body.envelope(motion,0.,profile.clock);q=profile.step/math.sqrt(2)
                        c=c[~(body.box_distance(c,low,high)+q<margin+profile.r_max-1e-9)]
                        axis=-profile.domain+.5*profile.step;loc=np.rint((c-axis)/profile.step).astype(int)
                        assert exclusions[identity][n][loc[:,0],loc[:,1]].all()
                    previous,end,seq=p['reference_us'],p['reference_us']+p['horizon_us'],p['sequence']
                assert row['horizon_us']==(475000 if valid else 0) and row['reason']==(None if valid else 'no_temporal_cover')
            else:assert row['method']=='position_set' and row['horizon_us']==computed[row['id']]
            assert row['geometry']==(row['horizon_us']>0) and row['horizon475_pass']==(row['horizon_us']>=475000)
            assert row['wire_ms']==20+row['bytes']*8/20_000
            total=(row['ready_us']-ref)/1000+row['assembly_ms']+row['verification_ms']+row['wire_ms']
            assert total==row['total_ms'] and row['age_us']==max(50_000,math.ceil(total/50)*50_000)
            assert row['timely475']==bool(row['horizon_us']>=475000 and row['age_us']+200000<475000)
            assert row['timely_max']==bool(row['horizon_us']>0 and row['age_us']+200000<row['horizon_us']);costs+=1
            if row['repeat']!=0 or not row['bytes']:continue
            blob=(a.results/'study/packets'/(name+'_'+row['id']+'_'+row['method']+'.bin')).read_bytes();assert len(blob)==row['bytes']
            # Bounded decompression implemented independently of stream.decode.
            import zlib
            assert blob[:9]==b'MOBICV1Z\0';z=zlib.decompressobj();raw_bytes=z.decompress(blob[9:],2_100_001)
            assert z.eof and not z.unused_data and not z.unconsumed_tail and len(raw_bytes)==row['raw_bytes']<=2_100_000
            packet=json.loads(raw_bytes);assert packet['anchor']==key and packet['dynamics']=='observation-speed-age-v1'
            assert packet['kind']==('center-continuity-v1' if row['method']=='fixed_K' else 'position-observations-v1')
            assert packet['steps']==[all_raw[x] for x in ids];packets+=1
        groups=defaultdict(list)
        for row in study['rows']:
            if row['run']==name:groups[(row['id'],row['method'])].append(row)
        for (identity,method),g in groups.items():
            item=dict(run=name,id=identity,method=method,horizon_us=g[0]['horizon_us'],geometry=g[0]['geometry'],timely475=sum(x['timely475'] for x in g),timely_max=sum(x['timely_max'] for x in g))
            for f in ['bytes','assembly_ms','verification_ms','total_ms','age_us']:item[f+'_median']=float(np.median([x[f] for x in g]))
            summaries.append(item)
    result=dict(prefix_packet_checks=prefixes,source_step_checks=source_steps,independent_propagations=propagations,state_mask_checks=state_checks,
                saved_packet_checks=packets,cost_rows=costs,frontier_boundary_checks=boundaries,summaries=summaries,
                analyzer_sha256=audit.sha(Path(__file__)),scope='Independent full-domain ray-to-cell ball tree, vertex-to-vertex nearest tree (not EDT/native), source/prefix/temporal/cost/queue replay; saved first-repeat mask/packet checks only; conditional retrospective scope.')
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['summaries','scope','analyzer_sha256']}))


if __name__=='__main__':main()
