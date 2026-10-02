#!/usr/bin/env python3
"""Independent full source/KD-grid/FIFO audit; does not import tested flow."""
import argparse,gzip,hashlib,importlib.util,json,math,sys
from dataclasses import replace
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('independent_dictionary_audit',ROOT/'experiments/compact_observer_20261002/analyze.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior);audit=prior.audit;body=audit.body

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def charge(ms):return math.ceil(ms*1000)
def distance(v0,v1,a,t):
    if t==0:return 0.
    if a==0:return min(v0,v1)*t
    if v1-v0>=a*t:return v0*t+.5*a*t*t
    if v0-v1>=a*t:return v1*t+.5*a*t*t
    return .5*(v0+v1)*t+.25*a*t*t-(v1-v0)**2/(4*a)
def union(intervals,start,end):
    result=[]
    for a,b in sorted((max(a,start),min(b,end)) for a,b in intervals):
        if a>=b:continue
        if result and a<=result[-1][1]:result[-1][1]=max(b,result[-1][1])
        else:result.append([a,b])
    return sum(b-a for a,b in result),result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--capture',type=Path,required=True);ap.add_argument('--source',type=Path,required=True);ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    s=json.loads((a.results/'study/analysis.json').read_bytes());pipeline=json.loads((a.source/'study/analysis.json').read_bytes());assert len(s['rows'])==7560
    for f,h in s['source_sha256'].items():assert sha(ROOT/f)==h,f
    for f,h in s['input_sha256'].items():assert sha(ROOT/f)==h,f
    assert s['source_study_sha256']==sha(a.source/'study/analysis.json') and s['baseline_manifest_sha256']==sha(a.baseline/'source_manifest.json')
    for f,h in json.loads((a.baseline/'source_manifest.json').read_bytes())['source_sha256'].items():assert sha(ROOT/f)==h,f
    assert s['protocol_sha256']==sha(Path(__file__).with_name('PROTOCOL.md'))
    build=json.loads((a.results/'build.json').read_bytes());assert build['binary_sha256']==s['propagation_library_sha256'] and build['source_sha256']==sha(ROOT/'experiments/compact_observer_20261002/propagate.cpp')
    original=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=body.Contract();windows=dict(small=9.,vehicle=11.5)
    grids={f:{n:replace(p,domain=windows[n],step=p.step/f) for n,p in original.items()} for f in [1,2]}
    counts=dict(prefixes=0,sources=0,packets=0,logical_class_predictions=0,unique_kd_predictions=0,states=0,frontier_boundaries=0,cost_rows=0,coverage_rows=0)
    packets={};stored={}
    for f,h in s['state_files_sha256'].items():
        path=a.results/'study/states'/(f+'.npz');assert sha(path)==h
        with np.load(path) as z:stored[f]={n:z[n] for n in original}
        data=b''.join(n.encode()+str(x.shape).encode()+x.tobytes() for n,x in sorted(stored[f].items()));assert hashlib.sha256(data).hexdigest()==f
    for ctx in s['contexts']:
        name=ctx['run'];run=a.capture/name;record=json.loads(gzip.decompress((run/'record.json.gz').read_bytes()));decisions={d['id']:d for d in record['decisions']}
        old=audit.audit.LegacyReceiver(original,contract,name,'Carla/Maps/Town10HD_Opt');regions={}
        for identity in ctx['prefix_ids']:
            d=decisions[identity];blob=(run/'packets'/(identity+'.json')).read_bytes();b=json.loads(blob)
            scope=body.Scope(name,old.frame_id,tuple(d['query']),b['raw']['payload']['scope']['plane_z']);motion=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.)
            assert old.accept(blob,scope,motion,d['receiver_check_time'])
            p,o,r=audit.audit.full_check(b['raw'],original,contract,scope,motion,prior=regions[b['prior']] if b['prior'] else None)
            key=hashlib.sha256(blob).hexdigest();lo,hi,margin=body.envelope(motion,p['horizon_us']/1e6,.02)
            regions[key]=body.Region(tuple(scope.query),motion.yaw,tuple(lo),tuple(hi),margin,p['reference_us']/1e6,(p['reference_us']+p['horizon_us'])/1e6,key,name);counts['prefixes']+=1
        rootref=p['reference_us'];rooth=p['horizon_us'];assert key==ctx['anchor']['identity'];assert ctx['root_receipt_us']==math.ceil(d['receiver_check_time']*1e6)
        root_eff={n:audit.effective(g,r,rootref) for n,g in original.items()};v=body.projections(o,r,rootref,original,scope,contract);roots={}
        for factor,grid in grids.items():
            roots[factor]={}
            for n,profile in original.items():
                required=body.required(root_eff[n],motion,rooth/1e6);axis=-profile.domain+.5*profile.step;loc=np.rint((required-axis)/profile.step).astype(int);size=round(2*profile.domain/profile.step)
                proved=np.zeros((size,size),dtype=bool);proved[loc[:,0],loc[:,1]]=True;coarse=(~proved)&~audit.excluded(v[n],profile,motion)
                off=round((profile.domain-windows[n])/profile.step);nn=round(2*windows[n]/profile.step);crop=coarse[off:off+nn,off:off+nn]
                roots[factor][n]=np.repeat(np.repeat(crop,factor,axis=0),factor,axis=1)&~audit.excluded(v[n],grid[n],motion)
        for method,digest in ctx['root_states'].items():
            factor=2 if method.startswith('fine') else 1
            for n in original:np.testing.assert_array_equal(roots[factor][n],stored[digest][n]);counts['states']+=1
        rawsteps={};projections={};effects={};empty={};cover={}
        for index in range(20,40):
            identity='drive_%03d'%index;raw=json.loads((a.source/'study/source'/(name+'_'+identity+'.json')).read_bytes());rawsteps[index]=raw
            p,o,r=body.decode(body.canonical(raw),original,scope,contract);ref=p['reference_us'];assert ref==math.ceil(decisions[identity]['stamp']*1e6)
            with np.load(run/'clouds'/(identity+'.npz')) as c:orig=body.encode_source(c['xyz'],c['origin'],decisions[identity]['stamp'],decisions[identity]['stamp'])
            assert audit.audit.ray_keys(o,r)<=audit.audit.ray_keys(orig[0],orig[1]) and int(r[:,4].max())==int(orig[1][:,4].max());counts['sources']+=1
            gkey=(o.tobytes(),r[:,:4].tobytes(),(ref-r[:,4]).tobytes());effects[index]={n:audit.effective(g,r,ref) for n,g in original.items()}
            if gkey not in projections:projections[gkey]=body.projections(o,r,ref,original,scope,contract)
            v=projections[gkey]
            for factor,grid in grids.items():
                if (gkey,factor) not in empty:empty[gkey,factor]={n:audit.excluded(v[n],g,motion) for n,g in grid.items()}
            ckey=(gkey,p['horizon_us'])
            if ckey not in cover:
                ok=True
                for n,profile in original.items():
                    req=body.required(effects[index][n],motion,p['horizon_us']/1e6);low,high,margin=body.envelope(motion,0.,profile.clock);q=profile.step/math.sqrt(2)
                    req=req[~(body.box_distance(req,low,high)+q<margin+profile.r_max-1e-9)];axis=-profile.domain+.5*profile.step;loc=np.rint((req-axis)/profile.step).astype(int)
                    ok=ok and bool(audit.excluded(v[n],profile,motion)[loc[:,0],loc[:,1]].all())
                cover[ckey]=ok
            rawsteps[index]['_gkey']=gkey
        # Memoization uses only independently recomputed reference operands.
        preds={};bounds={}
        groups={}
        for x in s['rows']:
            if x['run']==name:groups.setdefault((x['preset'],x['repeat'],x['method']),[]).append(x)
        for (preset,repeat,method),group in groups.items():
            assert len(group)==20;position=not method.startswith('fixed');factor=2 if method.startswith('fine') else 1;terminal=method.endswith('terminal');grid=grids[factor] if position else original
            possible=roots[factor] if position else None;ref=rootref;seq=ctx['anchor']['sequence'];seenref=ref;seen_seq=seq;eff=root_eff;hprev=rooth
            budget={n:body.travel(rooth/1e6+g.clock,eff[n]) for n,g in original.items()};authority=[rootref+rooth,ctx['root_receipt_us']]
            send_end=link_end=0;receive_end=ctx['root_receipt_us']+charge(group[0]['reset_ms']);intervals=[(authority[1],authority[0]-200000)]
            for x in group:
                index=x['index'];assert index==20+group.index(x);raw=rawsteps[index];p=raw['payload'];gkey=raw['_gkey'];current=effects[index]
                src=next(z for z in pipeline['maintenance'] if z['run']==name and z['repeat']==repeat and z['id']==x['id'])
                assert x['ref_us']==p['reference_us'] and x['source_arrival_us']==src['arrival_us'] and x['generation_ms']==src['generation_ms']
                sender_start=max(src['arrival_us'],send_end);gen_end=sender_start+charge(src['generation_ms']);send_end=gen_end+charge(x['encoding_ms'])
                link_start=max(send_end,link_end);rate=.5 if preset=='slow' else 20.;link_end=link_start+math.ceil(x['bytes']*8/rate);arrival=link_end+20000
                assert [x[k] for k in ['sender_start_us','generation_end_us','sender_end_us','link_start_us','link_end_us','receiver_arrival_us']]==[sender_start,gen_end,send_end,link_start,link_end,arrival]
                dropped=preset=='blackout' and index in [27,28,29];assert x['dropped']==dropped
                h=0;accepted=False
                if dropped:assert x['decision'] is None and x['verification_ms']==0 and x['receiver_start_us'] is None and x['receiver_end_us'] is None;available=arrival
                else:
                    rxstart=max(arrival,receive_end);rxend=rxstart+charge(x['verification_ms']);assert x['receiver_start_us']==rxstart and x['receiver_end_us']==rxend
                    assert seenref<p['reference_us']<=rxstart and p['sequence']>seen_seq;dt=(p['reference_us']-ref)/1e6
                    ds={n:distance(eff[n].speed,current[n].speed,g.acceleration,dt) if terminal else body.travel(dt,eff[n]) for n,g in grid.items()}
                    for n in ds:assert math.isclose(ds[n],x['decision']['past_distances'][n],rel_tol=1e-13,abs_tol=1e-13)
                    if position:
                        new={}
                        for n,g in grid.items():
                            # Outward rounding and 1e-9 geometric tolerance are separately explicit.
                            d=float(np.nextafter(ds[n],math.inf)) if terminal and dt>0 else ds[n]
                            predkey=(factor,n,gkey,d,possible[n].tobytes());counts['logical_class_predictions']+=1
                            if predkey not in preds:
                                preds[predkey]=audit.propagate_tree(possible[n],g,d)&~empty[gkey,factor][n];counts['unique_kd_predictions']+=1
                            new[n]=preds[predkey]
                        possible=new;accepted=True;h=x['horizon_us']
                        if repeat==0:
                            assert x['state_key'] in stored
                            for n in grid:np.testing.assert_array_equal(possible[n],stored[x['state_key']][n]);counts['states']+=1
                            for testh in ([h,h+1] if h>0 else [1]):
                                bkey=(factor,tuple((n,hashlib.sha256(possible[n].tobytes()).hexdigest(),current[n].speed) for n in sorted(grid)),testh)
                                if bkey not in bounds:bounds[bkey]=all(audit.support(possible[n],replace(g,speed=current[n].speed),motion,testh) for n,g in grid.items())
                                assert bounds[bkey]==(testh==h and h>0);counts['frontier_boundaries']+=1
                    else:
                        bridge=(p['reference_us']<ref+hprev and p['reference_us']+p['horizon_us']>ref+hprev) if method=='fixed_strict' else all(ds[n]<=budget[n] for n in grid)
                        accepted=bridge and cover[gkey,p['horizon_us']];h=p['horizon_us'] if accepted else 0
                        assert x['horizon_us']==h
                        assert x['decision']['reason']==(None if accepted else 'past_bridge_unproved' if not bridge else 'current_collar_unproved')
                    assert x['decision']['fact_accepted']==accepted and x['decision']['reference_us']==p['reference_us'] and x['decision']['endpoint_us']==p['reference_us']+h
                    seenref,seen_seq=p['reference_us'],p['sequence']
                    if accepted:
                        ref,seq,eff,hprev=p['reference_us'],p['sequence'],current,h
                        if not position:budget={n:body.travel(h/1e6+g.clock,eff[n]) for n,g in grid.items()}
                    if h>0 and p['reference_us']+h>authority[0]:authority=[p['reference_us']+h,rxend]
                    receive_end=rxend;available=rxend
                age=max(50000,math.ceil((available-p['reference_us'])/50000)*50000);tick=p['reference_us']+age
                assert x['horizon_us']==h and x['fact_ref_us']==ref and x['authority']==authority and x['age_us']==age and x['tick_us']==tick and x['total_ms']==(available-p['reference_us'])/1000
                assert x['fresh_admission']==bool(not dropped and h>0 and age+200000<h)
                assert x['current_authority']==bool(tick>=receive_end and authority[1]<=tick and tick+200000<authority[0]);counts['cost_rows']+=1
                if h>0:intervals.append((tick,p['reference_us']+h-200000))
                if repeat==0:
                    digest=x['packet_sha256'];path=a.results/'study/packets'/(digest+'.bin');assert sha(path)==digest and path.stat().st_size==x['bytes']
                    if digest not in packets:
                        b,_=prior.unpack(path.read_bytes());clean={k:v for k,v in raw.items() if k!='_gkey'}
                        assert b==dict(kind='position-flow-v1' if position else 'center-flow-v1',dynamics='observation-speed-age-v1',anchor=key,steps=[clean]);packets[digest]=True
                    counts['packets']+=1
            start=rawsteps[20]['payload']['reference_us'];end=rawsteps[39]['payload']['reference_us']+500000;covered,merged=union(intervals,start,end)
            out=next(z for z in s['coverage'] if (z['run'],z['preset'],z['repeat'],z['method'])==(name,preset,repeat,method))
            assert [out[k] for k in ['start_us','end_us','covered_us','intervals']]==[start,end,covered,merged] and out['coverage']==covered/(end-start);counts['coverage_rows']+=1
        print(json.dumps(dict(run=name,**counts)),flush=True)
    assert not any(n in sys.modules for n in ['flow','compact','observer'])
    result=dict(**counts,unique_packet_checks=len(packets),unique_saved_states=len(stored),analyzer_sha256=sha(Path(__file__)),scope='Independent full-prefix/source/physical typed dictionary/KD-tree grid/H,H+1/FIFO/expiry/coverage audit. Exact memoization uses own reference operands; no flow/compact/observer/native/EDT imports.')
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
