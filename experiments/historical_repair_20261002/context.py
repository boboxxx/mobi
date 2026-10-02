import copy,gzip,hashlib,json,time
from pathlib import Path
import repair
G=repair.G;body=repair.body;flow=repair.flow;compact=repair.compact
ROOT=Path(__file__).resolve().parents[2]
RUNS=['c0_view0_reference_fixed','c0_view0_reference_rate20','c0_view0_reuse_fixed','c0_view0_reuse_rate20','c2_view0_reference_rate20','c2_view0_reuse_rate20']

def load(name):
    profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=body.Contract();windows=dict(small=9.,vehicle=11.5)
    prior=json.loads((ROOT/'results/recursive_validity_20261002/study/analysis.json').read_bytes());ctx=next(x for x in prior['contexts'] if x['run']==name);capture=ROOT/'results/online_evidence_20261002/live'/name
    record=json.loads(gzip.decompress((capture/'record.json.gz').read_bytes()));decisions={d['id']:d for d in record['decisions']};legacy=compact.base.LegacyReceiver(profiles,contract,name,'Carla/Maps/Town10HD_Opt');engines=dict(scalar=G.Receiver(profiles,contract,dict(small=475000,vehicle=475000)),fine=flow.Receiver('fine_terminal',profiles,contract,windows));meta={};warm=time.perf_counter();prefix=[]
    for i,identity in enumerate(ctx['prefix_ids']):
        d=decisions[identity];blob=(capture/'packets'/(identity+'.json')).read_bytes();b=json.loads(blob);scope=body.Scope(name,legacy.frame_id,tuple(d['query']),b['raw']['payload']['scope']['plane_z']);motion=body.Motion(**b['motion']);t=time.perf_counter();assert legacy.accept(blob,scope,motion,d['receiver_check_time']);vm=(time.perf_counter()-t)*1000
        for mode,c in engines.items():
            t=time.perf_counter();anchor=c.register(legacy,blob,scope,motion);rm=(time.perf_counter()-t)*1000
            if i==len(ctx['prefix_ids'])-1:
                t=time.perf_counter();wire=G.stream.encode(blob);em=(time.perf_counter()-t)*1000;meta[mode]=dict(validation_ms=vm,registration_ms=rm,encoding_ms=em,bytes=len(wire),anchor=body.asdict(anchor))
        prefix.append(dict(identity=identity,sha256=hashlib.sha256(blob).hexdigest()))
    original={i:json.loads((ROOT/'results/streaming_recovery_20261002/study/source'/(name+'_drive_%03d.json'%i)).read_bytes()) for i in range(20,40)}
    pipeline=json.loads((ROOT/'results/streaming_recovery_20261002/study/analysis.json').read_bytes());sources={(x['id'],x['repeat']):x for x in pipeline['maintenance'] if x['run']==name}
    return dict(name=name,profiles=profiles,contract=contract,engines=engines,meta=meta,root=b['raw'],root_decision=d,root_identity=identity,capture=capture,decisions=decisions,original=original,sources=sources,prefix=prefix,warm_ms=(time.perf_counter()-warm)*1000)

def receiver(ctx,mode,receipt,feedback):
    c=copy.deepcopy(ctx['engines'][mode]);rx=G.Transport(c);rx.reset(receipt);return repair.Receiver(rx,ctx['root'],feedback)
