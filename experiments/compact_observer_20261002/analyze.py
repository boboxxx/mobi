#!/usr/bin/env python3
"""Independent uncached ball/vertex-tree replay and temporal dictionary decode."""
import argparse,gzip,hashlib,importlib.util,json,math,zlib
from dataclasses import replace
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('independent_set_audit',ROOT/'experiments/set_observer_20261002/analyze.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit);body=audit.body


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def unpack(blob):
    assert blob[:9]==b'MOBICTD1\0' and len(blob)<=2100000
    z=zlib.decompressobj();raw=z.decompress(blob[9:],2100001)
    assert z.eof and not z.unused_data and not z.unconsumed_tail and len(raw)<=2100000
    b=json.loads(raw);assert b['version']==1 and 1<=len(b['steps'])<=32 and 1<=len(b['templates'])<=32
    packet=dict(b['header']);packet['steps']=[]
    for row in b['steps']:
        index,ref,h,seq,digest=row;t=b['templates'][index];p={k:v for k,v in t.items() if k!='rays'}
        p.update(reference_us=ref,horizon_us=h,sequence=seq)
        p['rays']=[list(ray[:-1])+[ref-ray[-1]] for ray in t['rays']]
        assert hashlib.sha256(body.canonical(p)).hexdigest()==digest
        packet['steps'].append(dict(payload=p,sha256=digest))
    assert len(body.canonical(packet))<=2100000;return packet,len(b['templates'])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    s=json.loads((a.results/'study/analysis.json').read_bytes());pipeline=json.loads((a.source/'study/analysis.json').read_bytes());assert len(s['rows'])==108
    for f,h in s['source_sha256'].items():assert sha(ROOT/f)==h,f
    for f,h in s['input_sha256'].items():assert sha(ROOT/f)==h,f
    assert s['source_study_sha256']==sha(a.source/'study/analysis.json') and s['baseline_manifest_sha256']==sha(a.baseline/'source_manifest.json')
    for f,h in json.loads((a.baseline/'source_manifest.json').read_bytes())['source_sha256'].items():assert sha(ROOT/f)==h,f
    assert s['protocol_sha256']==sha(Path(__file__).with_name('PROTOCOL.md'))
    build=json.loads((a.results/'build.json').read_bytes());assert build['source_sha256']==sha(Path(__file__).with_name('propagate.cpp')) and build['binary_sha256']==s['propagation_library_sha256']
    original=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=body.Contract();windows=dict(small=9.,vehicle=11.5)
    grids={method:{n:replace(p,domain=windows[n],step=p.step/factor) for n,p in original.items()} for method,factor in [('coarse_set',1),('fine_set',2)]}
    prefixes=0;sources=0;propagations=0;masks=0;packets=0;costs=0;boundaries=0;rows=[]
    for ctx in s['contexts']:
        name=ctx['run'];run=a.capture/name;record=json.loads(gzip.decompress((run/'record.json.gz').read_bytes()));decisions={d['id']:d for d in record['decisions']}
        old=audit.audit.LegacyReceiver(original,contract,name,'Carla/Maps/Town10HD_Opt');regions={}
        for identity in ctx['prefix_ids']:
            d=decisions[identity];blob=(run/'packets'/(identity+'.json')).read_bytes();b=json.loads(blob)
            scope=body.Scope(name,old.frame_id,tuple(d['query']),b['raw']['payload']['scope']['plane_z']);motion=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
            assert old.accept(blob,scope,motion,d['receiver_check_time'])
            p,o,r=audit.audit.full_check(b['raw'],original,contract,scope,motion,prior=regions[b['prior']] if b['prior'] else None)
            key=hashlib.sha256(blob).hexdigest();lo,hi,margin=body.envelope(motion,p['horizon_us']/1e6,.02)
            regions[key]=body.Region(tuple(scope.query),motion.yaw,tuple(lo),tuple(hi),margin,p['reference_us']/1e6,(p['reference_us']+p['horizon_us'])/1e6,key,name);prefixes+=1
        assert key==ctx['anchor']['identity'];rootref=p['reference_us'];rootseq=p['sequence'];v=body.projections(o,r,rootref,original,scope,contract)
        roots={};eff={};possible={}
        for method,factor in [('coarse_set',1),('fine_set',2)]:
            roots[method]={};eff[method]={}
            for n,profile in original.items():
                allc=body.grid(profile.domain,profile.step)[0];required=body.required(audit.effective(profile,r,rootref),motion,p['horizon_us']/1e6)
                axis=-profile.domain+.5*profile.step;loc=np.rint((required-axis)/profile.step).astype(int);size=round(2*profile.domain/profile.step);proved=np.zeros((size,size),dtype=bool);proved[loc[:,0],loc[:,1]]=True
                coarse=(~proved)&~audit.excluded(v[n],profile,motion)
                off=round((profile.domain-windows[n])/profile.step);nn=round(2*windows[n]/profile.step);crop=coarse[off:off+nn,off:off+nn]
                g=grids[method][n];roots[method][n]=np.repeat(np.repeat(crop,factor,axis=0),factor,axis=1)&~audit.excluded(v[n],g,motion);eff[method][n]=audit.effective(g,r,rootref)
            with np.load(a.results/'study/states'/(name+'_root_'+method+'.npz')) as stored:
                for n in original:np.testing.assert_array_equal(roots[method][n],stored[n]);masks+=1
            possible[method]=roots[method]
        lastref,lastseq=rootref,rootseq;source_raw={};fixed_valid=True;fixedend=ctx['anchor']['endpoint_us'];fixedref=rootref;fixedseq=rootseq;computed={}
        for index in range(20,40):
            identity='drive_%03d'%index;raw=json.loads((a.source/'study/source'/(name+'_'+identity+'.json')).read_bytes());source_raw[identity]=raw
            p,o,r=body.decode(body.canonical(raw),original,scope,contract);ref=p['reference_us'];assert ref>lastref and p['sequence']>lastseq and ref==math.ceil(decisions[identity]['stamp']*1e6)
            with np.load(run/'clouds'/(identity+'.npz')) as c:orig=body.encode_source(c['xyz'],c['origin'],decisions[identity]['stamp'],decisions[identity]['stamp'])
            assert audit.audit.ray_keys(o,r)<=audit.audit.ray_keys(orig[0],orig[1]) and int(r[:,4].max())==int(orig[1][:,4].max());sources+=1
            v=body.projections(o,r,ref,original,scope,contract)
            if fixed_valid:
                if not fixedref<ref<fixedend or p['sequence']<=fixedseq or ref+p['horizon_us']<=fixedend:fixed_valid=False
                else:
                    for n,profile in original.items():
                        req=body.required(audit.effective(profile,r,ref),motion,p['horizon_us']/1e6);low,high,margin=body.envelope(motion,0.,profile.clock);q=profile.step/math.sqrt(2)
                        req=req[~(body.box_distance(req,low,high)+q<margin+profile.r_max-1e-9)];axis=-profile.domain+.5*profile.step;loc=np.rint((req-axis)/profile.step).astype(int)
                        assert audit.excluded(v[n],profile,motion)[loc[:,0],loc[:,1]].all()
                    fixedref,fixedend,fixedseq=ref,ref+p['horizon_us'],p['sequence']
            for method,grid in grids.items():
                for n,g in grid.items():
                    possible[method][n]=audit.propagate_tree(possible[method][n],g,body.travel((ref-lastref)/1e6,eff[method][n]))&~audit.excluded(v[n],g,motion)
                    eff[method][n]=audit.effective(g,r,ref);propagations+=1
                if index in [25,39]:
                    group=[x for x in s['rows'] if x['run']==name and x['id']==identity and x['method']==method];assert len(group)==3 and len({x['horizon_us'] for x in group})==1
                    h=group[0]['horizon_us'];computed[(identity,method)]=h
                    with np.load(a.results/'study/states'/(name+'_'+identity+'_'+method+'.npz')) as stored:
                        for n in original:np.testing.assert_array_equal(possible[method][n],stored[n]);masks+=1
                    if h:assert all(audit.support(possible[method][n],eff[method][n],motion,h) for n in original);boundaries+=1
                    assert not all(audit.support(possible[method][n],eff[method][n],motion,h+1) for n in original);boundaries+=1
            if index in [25,39]:computed[(identity,'fixed_K')]=475000 if fixed_valid else 0
            lastref,lastseq=ref,p['sequence']
        for x in [x for x in s['rows'] if x['run']==name]:
            assert x['horizon_us']==computed[(x['id'],x['method'])] and x['geometry']==(x['horizon_us']>0)
            d=decisions[x['id']];ids=['drive_%03d'%i for i in range(20,d['index']+1)];assert x['source_ids']==ids
            m=[z for z in pipeline['maintenance'] if z['run']==name and z['repeat']==x['repeat'] and z['id'] in ids]
            assert x['ready_us']==m[-1]['finish_us'] and x['charged_source_work_ms']==sum(z['generation_ms'] for z in m)
            assert x['wire_ms']==20+x['bytes']*8/20000
            total=(x['ready_us']-math.ceil(d['stamp']*1e6))/1000+x['assembly_ms']+x['verification_ms']+x['wire_ms'];assert total==x['total_ms'] and x['age_us']==max(50000,math.ceil(total/50)*50000)
            assert x['timely475']==bool(x['horizon_us']>=475000 and x['age_us']+200000<475000) and x['timely_max']==bool(x['horizon_us']>0 and x['age_us']+200000<x['horizon_us']);costs+=1
            if x['repeat']!=0 or not x['bytes']:continue
            blob=(a.results/'study/packets'/(name+'_'+x['id']+'_'+x['method']+'.bin')).read_bytes();assert len(blob)==x['bytes'];packet,count=unpack(blob)
            assert packet['anchor']==key and packet['dynamics']=='observation-speed-age-v1' and packet['kind']==('center-continuity-v1' if x['method']=='fixed_K' else 'position-observations-v1')
            assert body.canonical(packet['steps'])==body.canonical([source_raw[z] for z in ids]);packets+=1;rows.append(dict(run=name,id=x['id'],method=x['method'],bytes=len(blob),templates=count))
    result=dict(prefix_packet_checks=prefixes,source_step_checks=sources,independent_uncached_propagations=propagations,state_mask_checks=masks,saved_packet_checks=packets,
                cost_rows=costs,frontier_boundary_checks=boundaries,packets=rows,analyzer_sha256=sha(Path(__file__)),scope='Independent full prefix/source/contract replay, original checksum temporal dictionary reconstruction, uncached local-domain ball/vertex-tree propagation, unknown exterior arrivals, H/H+1 and all costs. No compact/native/EDT imports.')
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['packets','scope','analyzer_sha256']}))


if __name__=='__main__':main()
