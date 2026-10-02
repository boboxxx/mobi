#!/usr/bin/env python3
"""Reference KD geometry, F/R reconstruction and paid FIFO audit; no guard import."""
import argparse,collections,copy,gzip,hashlib,importlib.util,json,math,sys,zlib
from dataclasses import replace
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('reference_recovery_audit',ROOT/'experiments/recursive_validity_20261002/analyze.py')
reference=importlib.util.module_from_spec(spec);spec.loader.exec_module(reference)
prior=reference.prior;audit=reference.audit;body=reference.body
sha=reference.sha;charge=reference.charge;union=reference.union

def past_distance(v0,v1,a,t):
    # Closed form of integral min(v0+a*s,v1+a*(t-s)); search uses split integral.
    d=reference.distance(v0,v1,a,t)
    return float(np.nextafter(d,math.inf))

def unpack(blob,templates,store):
    assert blob.startswith(b'MOBIFLOW1\0') and len(blob)<=2100000
    typ=blob[10:11];inner=blob[11:];new=None
    if typ==b'F':
        packet,_=prior.unpack(inner);p=packet['steps'][0]['payload']
        q={k:v for k,v in p.items() if k not in ['reference_us','horizon_us','sequence']}
        q['rays']=[r[:4]+[p['reference_us']-r[4]] for r in p['rays']]
        new=hashlib.sha256(body.canonical(q)).hexdigest(),q
    else:
        assert typ==b'R';z=zlib.decompressobj();data=z.decompress(inner,2100001)
        assert len(data)<=2100000 and z.eof and not z.unused_data and not z.unconsumed_tail
        b=json.loads(data);assert set(b)=={'template_sha256','header','step'}
        ref,h,seq,digest=b['step'];q=templates[b['template_sha256']]
        p=dict(q,reference_us=ref,horizon_us=h,sequence=seq);p['rays']=[r[:4]+[ref-r[4]] for r in q['rays']]
        assert hashlib.sha256(body.canonical(p)).hexdigest()==digest
        packet=dict(b['header'],steps=[dict(payload=p,sha256=digest)])
    if new and store:
        templates[new[0]]=new[1]
        if len(templates)>4:templates.popitem(last=False)
    return packet

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();study=a.results/'study';s=json.loads((study/'analysis.json').read_bytes())
    assert len(s['rows'])==5400 and len(s['coverage'])==270 and len(s['augmentation'])==360 and len(s['contexts'])==6
    for f,h in s['source_sha256'].items():assert sha(ROOT/f)==h,f
    for f,h in s['input_sha256'].items():assert sha(ROOT/f)==h,f
    assert s['protocol_sha256']==sha(Path(__file__).with_name('PROTOCOL.md'))
    assert s['baseline_sha256']==sha(ROOT/'results/recursive_validity_20261002/study/analysis.json') and s['pipeline_sha256']==sha(ROOT/'results/streaming_recovery_20261002/study/analysis.json')
    pipeline=json.loads((ROOT/'results/streaming_recovery_20261002/study/analysis.json').read_bytes())
    profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=body.Contract();windows=dict(small=9.,vehicle=11.5);grid={n:replace(g,domain=windows[n],step=g.step/2) for n,g in profiles.items()};targets=dict(small=525000,vehicle=475000)
    counts=dict(prefixes=0,augmented_roots=0,sources=0,augmented_sources=0,augmentation_rows=0,saved_packets=0,logical_class_predictions=0,unique_kd_predictions=0,states=0,frontier_boundaries=0,scalar_class_checks=0,cost_rows=0,coverage_rows=0)
    stored={};packets={};preds={};bounds={};wire_reference={(x['run'],x['preset'],x['method'],x['index']):(x['packet_sha256'],x['bytes'],x['raw_sha256']) for x in s['rows'] if x['repeat']==0}
    for key,h in s['state_files_sha256'].items():
        path=study/'states'/(key+'.npz');assert sha(path)==h
        with np.load(path) as z:stored[key]={n:z[n] for n in profiles}
        data=b''.join(n.encode()+str(x.shape).encode()+x.tobytes() for n,x in sorted(stored[key].items()));assert hashlib.sha256(data).hexdigest()==key
    def covers(cells,mask,g):
        if cells is None:return False
        axis=-g.domain+.5*g.step;loc=np.rint((cells-axis)/g.step).astype(int)
        return bool(mask[loc[:,0],loc[:,1]].all())
    for ctx in s['contexts']:
        name=ctx['run'];run=ROOT/'results/online_evidence_20261002/live'/name;record=json.loads(gzip.decompress((run/'record.json.gz').read_bytes()));decisions={d['id']:d for d in record['decisions']};legacy=audit.audit.LegacyReceiver(profiles,contract,name,'Carla/Maps/Town10HD_Opt');regions={}
        assert len(ctx['prefix_ids'])==42
        for identity in ctx['prefix_ids']:
            d=decisions[identity];blob=(run/'packets'/(identity+'.json')).read_bytes();b=json.loads(blob);scope=body.Scope(name,legacy.frame_id,tuple(d['query']),b['raw']['payload']['scope']['plane_z']);motion=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
            assert legacy.accept(blob,scope,motion,d['receiver_check_time']);parent=regions[b['prior']] if b['prior'] else None
            p,o,r=audit.audit.full_check(b['raw'],profiles,contract,scope,motion,prior=parent);key=hashlib.sha256(blob).hexdigest();lo,hi,margin=body.envelope(motion,p['horizon_us']/1e6,.02)
            regions[key]=body.Region(tuple(scope.query),motion.yaw,tuple(lo),tuple(hi),margin,p['reference_us']/1e6,(p['reference_us']+p['horizon_us'])/1e6,key,name);counts['prefixes']+=1
        rootref=p['reference_us'];rootseq=p['sequence'];rooth=p['horizon_us'];rootoriginal=b;rootoriginal_blob=blob;rootoriginal_legacy=copy.deepcopy(legacy)
        roots={};root_eff={};geometries={};exclusions={};covers_memo={};source_data={}
        for mode in ['original','augmented']:
            rb=(study/'roots'/(name+'_'+mode+'.json')).read_bytes();rawblob=json.loads(rb);digest=hashlib.sha256(rb).hexdigest();assert digest==ctx['root_packet_'+mode+'_sha256']
            if mode=='original':assert rb==rootoriginal_blob
            else:
                assert {k:v for k,v in rawblob.items() if k!='raw'}=={k:v for k,v in rootoriginal.items() if k!='raw'}
                # Rebuild the original prior from all accepted earlier packets.
                audit.audit.full_check(rawblob['raw'],profiles,contract,scope,motion,prior=regions[rawblob['prior']] if rawblob['prior'] else None);counts['augmented_roots']+=1
            p,o,r=body.decode(body.canonical(rawblob['raw']),profiles,scope,contract)
            op,oo,orr=body.decode(body.canonical(rootoriginal['raw']),profiles,scope,contract)
            assert {k:v for k,v in p.items() if k not in ['origins','rays']}=={k:v for k,v in op.items() if k not in ['origins','rays']}
            with np.load(run/'clouds'/(ctx['prefix_ids'][-1]+'.npz')) as c:full=body.encode_source(c['xyz'],c['origin'],d['stamp'],d['stamp'])
            assert audit.audit.ray_keys(oo,orr)<=audit.audit.ray_keys(o,r)<=audit.audit.ray_keys(full[0],full[1]);assert int(r[:,4].max())==int(full[1][:,4].max())
            v=body.projections(o,r,rootref,profiles,scope,contract);root_eff[mode]={n:audit.effective(g,r,rootref) for n,g in profiles.items()};root_masks={n:audit.excluded(v[n],g,motion) for n,g in profiles.items()};roots[mode]={}
            for n,g in profiles.items():
                required=body.required(root_eff[mode][n],motion,rooth/1e6);axis=-g.domain+.5*g.step;loc=np.rint((required-axis)/g.step).astype(int);nn=round(2*g.domain/g.step);proved=np.zeros((nn,nn),dtype=bool);proved[loc[:,0],loc[:,1]]=True;coarse=(~proved)&~root_masks[n]
                off=round((g.domain-windows[n])/g.step);nn=round(2*windows[n]/g.step);crop=coarse[off:off+nn,off:off+nn];roots[mode][n]=np.repeat(np.repeat(crop,2,axis=0),2,axis=1)&~audit.excluded(v[n],grid[n],motion)
                if mode=='augmented':
                    req=body.required(root_eff[mode][n],motion,targets[n]/1e6);lo,hi,margin=body.envelope(motion,0.,g.clock);known=body.box_distance(req,lo,hi)+g.step/math.sqrt(2)<margin+g.r_max-1e-9
                    assert covers(req[~known],root_masks[n],g);counts['scalar_class_checks']+=1
            for method,rm in ctx['root_metadata'].items():
                if method.startswith('aug_')!=(mode=='augmented'):continue
                expected=dict(identity=digest,scope=body.asdict(scope),motion=body.asdict(motion),reference_us=rootref,endpoint_us=rootref+rooth,sequence=rootseq)
                assert body.canonical(rm['anchor'])==body.canonical(expected)
                rootwire=b'MOBICV1Z\0'+zlib.compress(rb,1);assert len(rootwire)==rm['bytes']
                assert rm['generation_extra_ms']==(ctx['root_generation_ms'] if mode=='augmented' else 0.)
                if method in ['fine','aug_fine']:
                    for n in grid:np.testing.assert_array_equal(roots[mode][n],stored[rm['root_state']][n]);counts['states']+=1
        assert ctx['root_capture_acquisition_ms']==d['acquisition_s']*1000 and ctx['root_capture_generation_ms']==d['generation_s']*1000
        for index in range(20,40):
            identity='drive_%03d'%index;original=json.loads((ROOT/'results/streaming_recovery_20261002/study/source'/(name+'_'+identity+'.json')).read_bytes());augmented=json.loads((study/'source'/(name+'_'+identity+'.json')).read_bytes());op,oo,orr=body.decode(body.canonical(original),profiles,scope,contract)
            with np.load(run/'clouds'/(identity+'.npz')) as c:full=body.encode_source(c['xyz'],c['origin'],decisions[identity]['stamp'],decisions[identity]['stamp'])
            source_data[index]={}
            for mode,raw in [('original',original),('augmented',augmented)]:
                p,o,r=body.decode(body.canonical(raw),profiles,scope,contract);ref=p['reference_us'];assert ref==math.ceil(decisions[identity]['stamp']*1e6) and p['horizon_us']==475000
                assert {k:v for k,v in p.items() if k not in ['origins','rays']}=={k:v for k,v in op.items() if k not in ['origins','rays']}
                assert audit.audit.ray_keys(oo,orr)<=audit.audit.ray_keys(o,r)<=audit.audit.ray_keys(full[0],full[1]) and int(r[:,4].max())==int(full[1][:,4].max())
                gkey=(o.tobytes(),r[:,:4].tobytes(),(ref-r[:,4]).tobytes());eff={n:audit.effective(g,r,ref) for n,g in profiles.items()}
                if gkey not in geometries:geometries[gkey]=body.projections(o,r,ref,profiles,scope,contract)
                v=geometries[gkey]
                if gkey not in exclusions:exclusions[gkey]={factor:{n:audit.excluded(v[n],g,motion) for n,g in gs.items()} for factor,gs in [(1,profiles),(2,grid)]}
                source_data[index][mode]=dict(raw=raw,p=p,gkey=gkey,eff=eff)
                counts['sources' if mode=='original' else 'augmented_sources']+=1
                if mode=='augmented':
                    aa=[x for x in s['augmentation'] if (x['run'],x['index'])==(name,index)];assert len(aa)==3
                    for x in aa:
                        assert x['raw_sha256']==raw['sha256'] and x['generation_ms']>=0;counts['augmentation_rows']+=1
                    assert len({x['supported'] for x in aa})==1
                    if aa[0]['supported']:
                        for n,g in profiles.items():
                            req=body.required(eff[n],motion,targets[n]/1e6);lo,hi,margin=body.envelope(motion,0.,g.clock);known=body.box_distance(req,lo,hi)+g.step/math.sqrt(2)<margin+g.r_max-1e-9
                            assert covers(req[~known],exclusions[gkey][1][n],g);counts['scalar_class_checks']+=1
        groups={}
        for x in s['rows']:
            if x['run']==name:groups.setdefault((x['preset'],x['repeat'],x['method']),[]).append(x)
        for (preset,repeat,method),group in groups.items():
            assert len(group)==20;mode='augmented' if method.startswith('aug_') else 'original';position=method in ['fine','aug_fine'];scalar=method in ['scalar','aug_scalar'];ts=targets if method=='aug_scalar' else dict(small=475000,vehicle=475000);rm=ctx['root_metadata'][method]
            possible=roots[mode] if position else None;ref=rootref;seenref=rootref;seen_seq=rootseq;eff=root_eff[mode];budget={n:body.travel((ts[n] if method=='aug_scalar' else rooth)/1e6+g.clock,eff[n]) for n,g in profiles.items()};rate=.5 if preset=='slow' else 20.
            rootservice=ctx['root_capture_acquisition_ms']+ctx['root_capture_generation_ms']+rm['generation_extra_ms']+rm['encoding_ms'];rootarrival=rootref+charge(rootservice)+math.ceil(rm['bytes']*8/rate)+20000;receipt=rootarrival+charge(rm['validation_ms']+rm['registration_ms']);authority=[rootref+rooth,receipt];receive_end=receipt;send_end=link_end=0;intervals=[(receipt,rootref+rooth-200000)];templates=collections.OrderedDict()
            for offset,x in enumerate(group):
                index=x['index'];assert index==20+offset;data=source_data[index][mode];p=data['p'];raw=data['raw'];gkey=data['gkey'];current=data['eff'];src=next(z for z in pipeline['maintenance'] if z['run']==name and z['repeat']==repeat and z['id']=='drive_%03d'%index)
                assert x['ref_us']==p['reference_us'] and x['source_arrival_us']==src['arrival_us'] and x['generation_ms']==src['generation_ms']
                extra=next(z['generation_ms'] for z in s['augmentation'] if (z['run'],z['index'],z['repeat'])==(name,index,repeat)) if mode=='augmented' else 0.;assert x['augmentation_ms']==extra
                assert x['root_receipt_us']==receipt and x['root_arrival_us']==rootarrival and x['raw_sha256']==raw['sha256']
                sender_start=max(src['arrival_us'],send_end);gen_end=sender_start+charge(src['generation_ms']+extra);send_end=gen_end+charge(x['encoding_ms']);link_start=max(send_end,link_end);link_end=link_start+math.ceil(x['bytes']*8/rate);arrival=link_end+20000
                assert [x[k] for k in ['sender_start_us','generation_end_us','sender_end_us','link_start_us','link_end_us','receiver_arrival_us']]==[sender_start,gen_end,send_end,link_start,link_end,arrival]
                dropped=preset=='blackout' and index in [27,28,29];assert x['dropped']==dropped
                assert (x['packet_sha256'],x['bytes'],x['raw_sha256'])==wire_reference[name,preset,method,index]
                digest=x['packet_sha256'];path=study/'packets'/(digest+'.bin');assert sha(path)==digest and path.stat().st_size==x['bytes'];packet=unpack(path.read_bytes(),templates,not dropped);expected=dict(kind='class-guard-flow-v1' if scalar else ('position-flow-v1' if position else 'center-flow-v1'),dynamics='observation-speed-age-v1',anchor=rm['anchor']['identity'],steps=[raw]);assert packet==expected;packets[digest]=True;counts['saved_packets']+=1
                h=0;accepted=False
                if dropped:
                    assert x['decision'] is None and x['verification_ms']==0 and x['receiver_start_us'] is None and x['receiver_end_us'] is None;available=arrival
                else:
                    rxstart=max(arrival,receive_end);rxend=rxstart+charge(x['verification_ms']);assert x['receiver_start_us']==rxstart and x['receiver_end_us']==rxend and seenref<p['reference_us']<=rxstart and p['sequence']>seen_seq;dt=(p['reference_us']-ref)/1e6
                    ds={n:past_distance(eff[n].speed,current[n].speed,g.acceleration,dt) for n,g in profiles.items()}
                    for n in ds:assert math.isclose(ds[n],x['decision']['past_distances'][n],rel_tol=1e-13,abs_tol=1e-13)
                    if position:
                        new={}
                        for n,g in grid.items():
                            predkey=(n,gkey,ds[n],possible[n].tobytes());counts['logical_class_predictions']+=1
                            if predkey not in preds:preds[predkey]=audit.propagate_tree(possible[n],g,ds[n])&~exclusions[gkey][2][n];counts['unique_kd_predictions']+=1
                            new[n]=preds[predkey]
                        possible=new;accepted=True;h=x['horizon_us']
                        if repeat==0:
                            assert x['state_key'] in stored
                            for n in grid:np.testing.assert_array_equal(possible[n],stored[x['state_key']][n]);counts['states']+=1
                        for testh in ([h,h+1] if h>0 else [1]):
                            bkey=(tuple((n,hashlib.sha256(possible[n].tobytes()).hexdigest(),current[n].speed) for n in sorted(grid)),testh)
                            if bkey not in bounds:bounds[bkey]=all(audit.support(possible[n],replace(g,speed=current[n].speed),motion,testh) for n,g in grid.items())
                            assert bounds[bkey]==(testh==h and h>0);counts['frontier_boundaries']+=1
                    else:
                        radii={n:float(np.nextafter(g.r_max+budget[n]-ds[n],-math.inf)) if scalar else g.r_max for n,g in profiles.items()};bridge=scalar or all(ds[n]<=budget[n] for n in profiles);accepted=bridge
                        if scalar:
                            assert x['decision']['class_horizons']==ts
                            for n in radii:assert math.isclose(radii[n],x['decision']['inherited_radii'][n],rel_tol=1e-13,abs_tol=1e-13)
                        for n,g in profiles.items():
                            req=body.required(current[n],motion,ts[n]/1e6);lo,hi,margin=body.envelope(motion,0.,g.clock);known=body.box_distance(req,lo,hi)+g.step/math.sqrt(2)<margin+radii[n]-1e-9 if radii[n]>=0 else np.zeros(len(req),dtype=bool)
                            ck=(n,gkey,ts[n],radii[n]);
                            if ck not in covers_memo:covers_memo[ck]=covers(req[~known],exclusions[gkey][1][n],g)
                            accepted=accepted and covers_memo[ck];counts['scalar_class_checks']+=1
                        h=min(ts.values()) if accepted else 0;assert x['horizon_us']==h
                        if method=='fixed':assert x['decision']['reason']==(None if accepted else 'past_bridge_unproved' if not bridge else 'current_collar_unproved')
                    assert x['decision']['fact_accepted']==bool(accepted) and x['decision']['reference_us']==p['reference_us'] and x['decision']['endpoint_us']==p['reference_us']+h
                    seenref,seen_seq=p['reference_us'],p['sequence']
                    if accepted:
                        ref=p['reference_us'];eff=current
                        if not position:budget={n:body.travel(ts[n]/1e6+g.clock,current[n]) for n,g in profiles.items()}
                    if h>0 and p['reference_us']+h>authority[0]:authority=[p['reference_us']+h,rxend]
                    receive_end=rxend;available=rxend
                age=max(50000,math.ceil((available-p['reference_us'])/50000)*50000);tick=p['reference_us']+age
                assert x['horizon_us']==h and x['fact_ref_us']==ref and x['authority']==authority and x['age_us']==age and x['tick_us']==tick and x['total_ms']==(available-p['reference_us'])/1000
                assert x['fresh_admission']==bool(not dropped and h>0 and age+200000<h) and x['current_authority']==bool(tick>=receive_end and authority[1]<=tick and tick+200000<authority[0]);counts['cost_rows']+=1
                if h>0:intervals.append((tick,p['reference_us']+h-200000))
            start=source_data[20][mode]['p']['reference_us'];end=source_data[39][mode]['p']['reference_us']+500000;covered,merged=union(intervals,start,end);out=next(z for z in s['coverage'] if (z['run'],z['preset'],z['repeat'],z['method'])==(name,preset,repeat,method))
            assert [out[k] for k in ['start_us','end_us','covered_us','intervals']]==[start,end,covered,merged] and out['coverage']==covered/(end-start);counts['coverage_rows']+=1
        print(json.dumps(dict(run=name,**counts)),flush=True)
    assert not any(n in sys.modules for n in ['guard','flow','compact','observer','dictionary'])
    result=dict(**counts,unique_saved_packet_checks=len(packets),unique_saved_states=len(stored),analyzer_sha256=sha(Path(__file__)),scope='Independent complete prefix/augmented root/superset source/current pointcloud, ungrouped whole-cell KD cover, closed-form past travel, scalar erosion, fine vertex-KD propagation, every H/H+1, F/R dictionary, paid FIFO/expiry/coverage. Memoization uses only reference operands; no tested guard/flow/compact/observer/dictionary/native imports. Warm prefix costs reported separately; modeled aligned-time stationary contract.')
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
