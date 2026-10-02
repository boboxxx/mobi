#!/usr/bin/env python3
import argparse,copy,gzip,hashlib,json,math,os,sys,time
from pathlib import Path
import numpy as np
import guard
flow=guard.flow;dictionary=guard.dictionary;compact=guard.compact;body=guard.body
ROOT=Path(__file__).resolve().parents[2]
METHODS=['fixed','fine','scalar','aug_scalar','aug_fine'];PRESETS={'standard':(20.,()),'slow':(.5,()),'blackout':(20.,(27,28,29))}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def charge(ms):return math.ceil(ms*1000)
def union(intervals,start,end):
    merged=[]
    for a,b in sorted((max(a,start),min(b,end)) for a,b in intervals):
        if a>=b:continue
        if merged and a<=merged[-1][1]:merged[-1][1]=max(b,merged[-1][1])
        else:merged.append([a,b])
    return sum(b-a for a,b in merged),merged

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(exist_ok=False)
    for name in ['source','packets','states','roots']:(a.out/name).mkdir()
    assert all(os.environ.get(n)=='1' for n in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'])
    compact.library();compact.observer.library();compact.stream.library();profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=body.Contract();windows=dict(small=9.,vehicle=11.5);targets=dict(small=525000,vehicle=475000)
    baseline=json.loads((ROOT/'results/recursive_validity_20261002/study/analysis.json').read_bytes());pipeline=json.loads((ROOT/'results/streaming_recovery_20261002/study/analysis.json').read_bytes());rng=np.random.default_rng(20261003);rows=[];contexts=[];coverage=[];augments=[];inputs={};state_files={}
    def record(path):inputs[str(path.relative_to(ROOT))]=sha(path)
    def state_key(state):
        data=b''.join(n.encode()+str(x.shape).encode()+x.tobytes() for n,x in sorted(state.possible.items()));key=hashlib.sha256(data).hexdigest()
        if key not in state_files:
            path=a.out/'states'/(key+'.npz');np.savez_compressed(path,**state.possible);state_files[key]=sha(path)
        return key
    for ctx in baseline['contexts']:
        name=ctx['run'];capture=ROOT/'results/online_evidence_20261002/live'/name;record(capture/'record.json.gz');rec=json.loads(gzip.decompress((capture/'record.json.gz').read_bytes()));decisions={d['id']:d for d in rec['decisions']};legacy=compact.base.LegacyReceiver(profiles,contract,name,'Carla/Maps/Town10HD_Opt')
        warm_engines=dict(fixed=flow.Receiver('fixed_terminal',profiles,contract,windows),fine=flow.Receiver('fine_terminal',profiles,contract,windows),scalar=guard.Receiver(profiles,contract,dict(small=475000,vehicle=475000)),aug_scalar=guard.Receiver(profiles,contract,targets));warm_reg={n:0. for n in warm_engines};warm_legacy=0.;t=time.perf_counter()
        for identity in ctx['prefix_ids'][:-1]:
            d=decisions[identity];path=capture/'packets'/(identity+'.json');record(path);blob=path.read_bytes();b=json.loads(blob);scope=body.Scope(name,legacy.frame_id,tuple(d['query']),b['raw']['payload']['scope']['plane_z']);motion=body.Motion(half_length=2.3,half_width=1.3,yaw=d['yaw'],acceleration=0.,yaw_rate=0.);vt=time.perf_counter();assert legacy.accept(blob,scope,motion,d['receiver_check_time']);warm_legacy+=(time.perf_counter()-vt)*1000
            for n,engine in warm_engines.items():
                vt=time.perf_counter();engine.register(legacy,blob,scope,motion);warm_reg[n]+=(time.perf_counter()-vt)*1000
        warm_ms=(time.perf_counter()-t)*1000;identity=ctx['prefix_ids'][-1];d=decisions[identity];path=capture/'packets'/(identity+'.json');record(path);rootblob=path.read_bytes();b=json.loads(rootblob);scope=body.Scope(name,legacy.frame_id,tuple(d['query']),b['raw']['payload']['scope']['plane_z']);motion=body.Motion(**b['motion']);anchorlike=type('AnchorView',(),dict(scope=scope,motion=motion))();cloudpath=capture/'clouds'/(identity+'.npz');record(cloudpath);t=time.perf_counter()
        with np.load(cloudpath) as cloud:augroot,rootstats=guard.augment(b['raw'],cloud['xyz'],cloud['origin'],d['stamp'],profiles,contract,anchorlike,targets)
        rootgeneration=(time.perf_counter()-t)*1000;assert augroot is not None,rootstats;newblob=body.canonical(dict(b,raw=augroot));(a.out/'roots'/(name+'_original.json')).write_bytes(rootblob);(a.out/'roots'/(name+'_augmented.json')).write_bytes(newblob)
        engines={};root_metadata={}
        for mode,blob in [('original',rootblob),('augmented',newblob)]:
            old=copy.deepcopy(legacy);t=time.perf_counter();assert old.accept(blob,scope,motion,d['receiver_check_time']);validation_ms=(time.perf_counter()-t)*1000
            methods=['fixed','fine','scalar'] if mode=='original' else ['aug_scalar','aug_fine']
            for method in methods:
                t=time.perf_counter()
                core=copy.deepcopy(warm_engines['fine' if method=='aug_fine' else method])
                if method in ['scalar','aug_scalar']:
                    anchor=core.register(old,blob,scope,motion)
                    if method=='aug_scalar':core.establish_root(augroot)
                else:anchor=core.register(old,blob,scope,motion)
                registration_ms=(time.perf_counter()-t)*1000;engine=guard.Transport(core);engines[method]=engine
                t=time.perf_counter();wire=guard.stream.encode(blob);encoding_ms=(time.perf_counter()-t)*1000
                root_metadata[method]=dict(anchor=body.asdict(anchor),validation_ms=validation_ms,registration_ms=registration_ms,generation_extra_ms=rootgeneration if mode=='augmented' else 0.,encoding_ms=encoding_ms,bytes=len(wire),root_state=state_key(core.root_state) if core.position else None)
        contexts.append(dict(run=name,prefix_ids=ctx['prefix_ids'],warm_prefix_ms=warm_ms,warm_legacy_ms=warm_legacy,warm_registration_ms=warm_reg,root_stats=rootstats,root_generation_ms=rootgeneration,root_packet_original_sha256=hashlib.sha256(rootblob).hexdigest(),root_packet_augmented_sha256=hashlib.sha256(newblob).hexdigest(),root_metadata=root_metadata,root_capture_acquisition_ms=d['acquisition_s']*1000,root_capture_generation_ms=d['generation_s']*1000))
        original={}
        for index in range(20,40):
            path=ROOT/'results/streaming_recovery_20261002/study/source'/(name+'_drive_%03d.json'%index);record(path);original[index]=json.loads(path.read_bytes())
        start=original[20]['payload']['reference_us'];end=original[39]['payload']['reference_us']+500000
        for repeat in range(3):
            augmented={};gen={}
            for index in range(20,40):
                identity='drive_%03d'%index;cloudpath=capture/'clouds'/(identity+'.npz');record(cloudpath);t=time.perf_counter()
                with np.load(cloudpath) as cloud:raw,stats=guard.augment(original[index],cloud['xyz'],cloud['origin'],decisions[identity]['stamp'],profiles,contract,anchorlike,targets)
                gen[index]=(time.perf_counter()-t)*1000;augmented[index]=raw if raw is not None else original[index];key=name+'_'+identity
                if repeat==0:(a.out/'source'/(key+'.json')).write_bytes(body.canonical(augmented[index]))
                augments.append(dict(run=name,index=index,repeat=repeat,generation_ms=gen[index],supported=raw is not None,stats=stats,raw_sha256=augmented[index]['sha256']))
            for preset,(rate,drops) in PRESETS.items():
                for method in rng.permutation(METHODS).tolist():
                    rx=engines[method];rm=root_metadata[method];rootref=rm['anchor']['reference_us'];rootservice=d['acquisition_s']*1000+d['generation_s']*1000+rm['generation_extra_ms']+rm['encoding_ms'];rootarrival=rootref+charge(rootservice)+math.ceil(rm['bytes']*8/rate)+20000;receipt=rootarrival+charge(rm['validation_ms']+rm['registration_ms']);rx.reset(receipt);sender=dictionary.Sender();send_end=link_end=0;receive_end=receipt;intervals=[(receipt,rm['anchor']['endpoint_us']-200000)]
                    for index in range(20,40):
                        raw=augmented[index] if method.startswith('aug_') else original[index];ref=raw['payload']['reference_us'];src=next(x for x in pipeline['maintenance'] if x['run']==name and x['index']==index and x['repeat']==repeat) if 'index' in pipeline['maintenance'][0] else next(x for x in pipeline['maintenance'] if x['run']==name and x['id']=='drive_%03d'%index and x['repeat']==repeat)
                        extra=gen[index] if method.startswith('aug_') else 0.;kind='class-guard-flow-v1' if method in ['scalar','aug_scalar'] else ('position-flow-v1' if method.endswith('fine') else 'center-flow-v1');t=time.perf_counter();wire=sender.encode(dict(kind=kind,dynamics='observation-speed-age-v1',anchor=rm['anchor']['identity'],steps=[raw]),index);encoding=(time.perf_counter()-t)*1000
                        sender_start=max(src['arrival_us'],send_end);gen_end=sender_start+charge(src['generation_ms']+extra);send_end=gen_end+charge(encoding);link_start=max(send_end,link_end);link_end=link_start+math.ceil(len(wire)*8/rate);arrival=link_end+20000;dropped=index in drops;decision=state=None;verify=0.;rxstart=rxend=None
                        if not dropped:
                            rxstart=max(arrival,receive_end);t=time.perf_counter();decision,state=rx.advance(wire,rxstart);verify=(time.perf_counter()-t)*1000;rxend=rxstart+charge(verify);rx.finish(rxend);receive_end=rxend
                        available=arrival if dropped else rxend;age=max(50000,math.ceil((available-ref)/50000)*50000);tick=ref+age;h=decision['horizon_us'] if decision else 0;fresh=bool(h>0 and not dropped and age+200000<h)
                        if h>0:intervals.append((tick,ref+h-200000))
                        digest=hashlib.sha256(wire).hexdigest()
                        if repeat==0:
                            path=a.out/'packets'/(digest+'.bin')
                            if not path.exists():path.write_bytes(wire)
                        rows.append(dict(run=name,index=index,repeat=repeat,preset=preset,method=method,ref_us=ref,root_receipt_us=receipt,root_arrival_us=rootarrival,source_arrival_us=src['arrival_us'],generation_ms=src['generation_ms'],augmentation_ms=extra,encoding_ms=encoding,sender_start_us=sender_start,generation_end_us=gen_end,sender_end_us=send_end,link_start_us=link_start,link_end_us=link_end,receiver_arrival_us=arrival,dropped=dropped,receiver_start_us=rxstart,verification_ms=verify,receiver_end_us=rxend,total_ms=(available-ref)/1000,bytes=len(wire),packet_sha256=digest,raw_sha256=raw['sha256'],age_us=age,tick_us=tick,horizon_us=h,fresh_admission=fresh,current_authority=rx.can_act(tick),authority=list(rx.authority),fact_ref_us=rx.ref,decision=decision,state_key=state_key(state) if state is not None and repeat==0 else None))
                    covered,merged=union(intervals,start,end);coverage.append(dict(run=name,method=method,preset=preset,repeat=repeat,start_us=start,end_us=end,covered_us=covered,coverage=covered/(end-start),intervals=merged))
                print(json.dumps(dict(run=name,repeat=repeat,preset=preset,rows=len(rows))),flush=True)
    sources={}
    for mod in list(sys.modules.values()):
        f=getattr(mod,'__file__',None)
        if f:
            p=Path(f).resolve()
            if ROOT in p.parents and p.suffix=='.py' and p.is_file():sources[str(p.relative_to(ROOT))]=sha(p)
    result=dict(contexts=contexts,rows=rows,coverage=coverage,augmentation=augments,input_sha256=inputs,source_sha256=sources,state_files_sha256=state_files,protocol_sha256=sha(Path(__file__).with_name('PROTOCOL.md')),baseline_sha256=sha(ROOT/'results/recursive_validity_20261002/study/analysis.json'),pipeline_sha256=sha(ROOT/'results/streaming_recovery_20261002/study/analysis.json'),scope='5400 paid modeled FIFO rows on saved captures with warm verified41-packet histories; actual last-root/augmentation services charged; uncalibrated stationary physical contract, repeated geometry, no real link/driving/optimality claim.')
    assert len(rows)==5400 and len(coverage)==270 and len(augments)==360;(a.out/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
