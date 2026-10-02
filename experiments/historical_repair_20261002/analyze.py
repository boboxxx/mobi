#!/usr/bin/env python3
"""Independent reference: full-cell KD geometry and chronological cost audit.
Does not import the tested repair, backward, receiver, scheduler or native kernels.
"""
import argparse,collections,copy,gzip,hashlib,importlib.util,json,math,sys,zlib
from dataclasses import replace
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('class_guard_reference',ROOT/'experiments/class_guard_20261002/analyze.py');refmod=importlib.util.module_from_spec(spec);spec.loader.exec_module(refmod)
body=refmod.body;audit=refmod.audit;sha=refmod.sha

def decode(wire):
    z=zlib.decompressobj();data=z.decompress(wire,4*1024*1024+1);assert len(data)<=4*1024*1024 and z.eof and not z.unused_data and not z.unconsumed_tail;return json.loads(data)
def charge(ms):return max(1,math.ceil(ms*1000))
def payload(raw):return raw['payload']
def rd(raw):return raw['sha256']
def rr(raw):return payload(raw)['reference_us']
def ss(raw):return payload(raw)['sequence']

def union(items,start,end):
    points=sorted(set([start,end]+[max(start,min(end,x)) for p in items for x in p]));out=[]
    for a,b in zip(points,points[1:]):
        if a<b and any(x<=a and b<=y for x,y in items):
            if out and out[-1][1]==a:out[-1][1]=b
            else:out.append([a,b])
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--study',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();data=json.loads((a.study/'analysis.json').read_bytes());pipeline=json.loads((ROOT/'results/streaming_recovery_20261002/study/analysis.json').read_bytes())['maintenance'];counts=collections.Counter();predcache={};maskcache={};frontcache={};geometrycache={};patchcache={};input_hashes={}
    def record(path):input_hashes[str(path.relative_to(ROOT))]=sha(path)
    def wire(h):
        p=a.study/'packets'/(h+'.bin');b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==h;return b
    profiles=dict(small=body.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=body.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.));contract=body.Contract();windows=dict(small=9.,vehicle=11.5);grids={n:replace(g,domain=windows[n],step=g.step/2) for n,g in profiles.items()}
    for ctx in data['contexts']:
        name=ctx['run'];capture=ROOT/'results/online_evidence_20261002/live'/name;record(capture/'record.json.gz');rec=json.loads(gzip.decompress((capture/'record.json.gz').read_bytes()));decisions={d['id']:d for d in rec['decisions']};legacy=audit.audit.LegacyReceiver(profiles,contract,name,'Carla/Maps/Town10HD_Opt');regions={}
        for row in ctx['prefix']:
            identity=row['identity'];p=capture/'packets'/(identity+'.json');record(p);blob=p.read_bytes();assert sha(p)==row['sha256'];b=json.loads(blob);d=decisions[identity];scope=body.Scope(name,legacy.frame_id,tuple(d['query']),b['raw']['payload']['scope']['plane_z']);motion=body.Motion(**b['motion']);assert legacy.accept(blob,scope,motion,d['receiver_check_time']);prior=regions[b['prior']] if b['prior'] else None;p,o,r=audit.audit.full_check(b['raw'],profiles,contract,scope,motion,prior=prior);key=hashlib.sha256(blob).hexdigest();lo,hi,margin=body.envelope(motion,p['horizon_us']/1e6,.02);regions[key]=body.Region(tuple(scope.query),motion.yaw,tuple(lo),tuple(hi),margin,p['reference_us']/1e6,(p['reference_us']+p['horizon_us'])/1e6,key,name);counts['prefixes']+=1
        root=b['raw'];rootref=rr(root);rootblob=blob;raws={rootref:root};ids={rootref:identity};stamps={rootref:d['stamp']}
        for i in range(20,40):
            p=ROOT/'results/streaming_recovery_20261002/study/source'/(name+'_drive_%03d.json'%i);record(p);raw=json.loads(p.read_bytes());raws[rr(raw)]=raw;ids[rr(raw)]='drive_%03d'%i;stamps[rr(raw)]=decisions[ids[rr(raw)]]['stamp'];body.decode(body.canonical(raw),profiles,scope,contract)
        def info(raw):
            p,o,r=body.decode(body.canonical(raw),profiles,scope,contract);key=(body.canonical(body.asdict(scope)),body.canonical(body.asdict(motion)),o.tobytes(),r[:,:4].tobytes(),(rr(raw)-r[:,4]).tobytes());eff={n:audit.effective(g,r,rr(raw)) for n,g in profiles.items()}
            if key not in geometrycache:geometrycache[key]=body.projections(o,r,rr(raw),profiles,scope,contract)
            return dict(raw=raw,p=p,o=o,r=r,key=key,eff=eff,v=geometrycache[key])
        def mask(d,n,fine=False):
            g=grids[n] if fine else profiles[n];k=(d['key'],n,g.domain,g.step)
            if k not in maskcache:maskcache[k]=audit.excluded(d['v'][n],g,motion)
            return maskcache[k]
        def covered(cells,d,n):
            g=profiles[n]
            if cells is None:return False
            xy=np.rint((cells+g.domain-g.step/2)/g.step).astype(int);return bool(mask(d,n)[xy[:,0],xy[:,1]].all())
        def budgets(d):return {n:body.travel(.475+g.clock,d['eff'][n]) for n,g in profiles.items()}
        rootinfo=info(root);rootpossible={}
        for n,g in profiles.items():
            required=body.required(rootinfo['eff'][n],motion,payload(root)['horizon_us']/1e6);xy=np.rint((required+g.domain-g.step/2)/g.step).astype(int);nn=round(2*g.domain/g.step);proved=np.zeros((nn,nn),bool);proved[xy[:,0],xy[:,1]]=True;coarse=~proved&~mask(rootinfo,n);off=round((g.domain-windows[n])/g.step);nn=round(2*windows[n]/g.step);rootpossible[n]=np.repeat(np.repeat(coarse[off:off+nn,off:off+nn],2,0),2,1)&~mask(rootinfo,n,True)
        sourceinfos={r:info(raw) for r,raw in raws.items()}
        for r,raw in raws.items():
            p=capture/'clouds'/(ids[r]+'.npz');record(p)
            with np.load(p) as c:o,rs,ref=body.encode_source(c['xyz'],c['origin'],stamps[r],stamps[r])
            assert ref==r and audit.audit.ray_keys(sourceinfos[r]['o'],sourceinfos[r]['r'])<=audit.audit.ray_keys(o,rs);counts['source_provenance']+=1
        def ds(old,new):return {n:refmod.past_distance(old['eff'][n].speed,new['eff'][n].speed,g.acceleration,(rr(new['raw'])-rr(old['raw']))/1e6) for n,g in profiles.items()}
        def step(old,new,possible,fine,expected=None):
            distances=ds(old,new)
            if fine:
                out={}
                for n,g in grids.items():
                    k=(n,g.domain,g.step,distances[n],possible[n].tobytes(),mask(new,n,True).tobytes())
                    if k not in predcache:predcache[k]=audit.propagate_tree(possible[n],g,distances[n])&~mask(new,n,True);counts['unique_kd_predictions']+=1
                    out[n]=predcache[k];counts['logical_class_predictions']+=1
                assert expected is not None
                for h in ([expected,expected+1] if expected else [1]):
                    k=(body.canonical(body.asdict(motion)),tuple((n,hashlib.sha256(out[n].tobytes()).hexdigest(),new['eff'][n].speed) for n in sorted(grids)),h)
                    if k not in frontcache:frontcache[k]=all(audit.support(out[n],replace(g,speed=new['eff'][n].speed),motion,h) for n,g in grids.items())
                    assert frontcache[k]==(h==expected and h>0);counts['frontier_boundaries']+=1
                return expected,new,out
            ok=True;b=budgets(old)
            for n,g in profiles.items():
                radius=float(np.nextafter(g.r_max+b[n]-distances[n],-math.inf));cells=body.required(new['eff'][n],motion,.475);lo,hi,margin=body.envelope(motion,0.,g.clock);known=body.box_distance(cells,lo,hi)+g.step/math.sqrt(2)<margin+radius-1e-9 if radius>=0 else np.zeros(len(cells),bool);ok=ok and covered(cells[~known],new,n);counts['scalar_classes']+=1
            return (475000,new,None) if ok else (0,old,None)
        def patch(old,new,fragment):
            k=(rd(old['raw']),rd(new['raw']),rd(fragment))
            if k in patchcache:return patchcache[k]
            f=info(fragment);assert (rr(fragment),ss(fragment),payload(fragment)['horizon_us'])==(rr(old['raw']),ss(old['raw']),475000);p=capture/'clouds'/(ids[rr(fragment)]+'.npz')
            with np.load(p) as c:o,r,t=body.encode_source(c['xyz'],c['origin'],stamps[rr(fragment)],stamps[rr(fragment)])
            assert audit.audit.ray_keys(f['o'],f['r'])<=audit.audit.ray_keys(o,r);distances=ds(old,new);b=budgets(old);details={}
            for n,g in profiles.items():
                cells=body.required(new['eff'][n],motion,.475);lo,hi,margin=body.envelope(motion,0.,g.clock);q=g.step/math.sqrt(2);radius=float(np.nextafter(g.r_max+b[n]-distances[n],-math.inf));known=body.box_distance(cells,lo,hi)+q<margin+radius-1e-9 if radius>=0 else np.zeros(len(cells),bool);xy=np.rint((cells+g.domain-g.step/2)/g.step).astype(int);missing=cells[~known&~mask(new,n)[xy[:,0],xy[:,1]]]
                if len(missing):
                    assert g.domain-np.max(np.abs(missing))-g.step/2>distances[n]+1e-9
                    offsets=np.array([[-1,-1],[-1,1],[1,-1],[1,1]])*g.step/2;vertices=(missing[:,None,:]+offsets).reshape(-1,2);tree=cKDTree(vertices);grid=body.grid(g.domain,g.step)[0];dmin=np.full(len(grid),np.inf)
                    for offset in offsets:dmin=np.minimum(dmin,tree.query(grid+offset,k=1)[0])
                    candidates=grid[dmin<=distances[n]+1e-9];knownold=body.box_distance(candidates,lo,hi)+q<margin+g.r_max+b[n]-1e-9;xy=np.rint((candidates+g.domain-g.step/2)/g.step).astype(int);needed=candidates[~knownold&~mask(old,n)[xy[:,0],xy[:,1]]];assert covered(needed,f,n)
                else:needed=np.zeros((0,2))
                details[n]=dict(unresolved=len(missing),needed=len(needed));counts['predecessor_classes']+=1
            patchcache[k]=f;counts['unique_fragments']+=1;return f
        for run in [x for x in data['runs'] if x['run']==name]:
            fine=run['method'] in ('fine','backward_fine');rate=.5 if run['preset']=='slow' else 20.;rm=ctx['root_metadata']['fine' if fine else 'scalar'];d=ctx['root_capture'];rootcpu=rootref+charge(d['acquisition_s']*1000+d['generation_s']*1000+rm['encoding_ms']);rootlink=rootcpu+math.ceil(rm['bytes']*8/rate);receipt=rootlink+20000+charge(rm['validation_ms']+rm['registration_ms']);assert [run[k] for k in ['root_sender_end_us','root_link_end_us','root_receipt_us']]==[rootcpu,rootlink,receipt]
            ev=run['events'];byres={k:[x for x in ev if x.get('resource')==k] for k in ('source','receiver')}
            for resource,jobs in byres.items():
                free=rootcpu if resource=='source' else receipt
                for x in jobs:
                    assert x['start_us']==max(free,x['enqueued_us']);assert x['end_us']==x['start_us']+charge(x['service_ms']);free=x['end_us'];counts['cpu_jobs']+=1
                assert [x['enqueued_us'] for x in jobs]==sorted(x['enqueued_us'] for x in jobs)
            for direction in ('down','up'):
                free=rootlink if direction=='down' else 0
                for x in [v for v in ev if v.get('direction')==direction]:
                    assert len(wire(x['sha256']))==x['bytes'];assert x['start_us']==max(free,x['enqueued_us']);assert x['end_us']==x['start_us']+math.ceil(x['bytes']*8/rate);assert x['arrival_us']==x['end_us']+20000;free=x['end_us'];counts['transmissions']+=1
            assert run['downlink_bytes']==rm['bytes']+sum(x['bytes'] for x in ev if x.get('direction')=='down')
            assert run['uplink_bytes']==sum(x['bytes'] for x in ev if x.get('direction')=='up')
            for job in byres['source']:
                if job['kind']=='reply_source':
                    incoming=next(x for x in ev if x['kind']=='request_arrival' and x['sha256']==job['input_sha256'])
                    assert incoming['arrival_us']==job['enqueued_us']
            for job in byres['receiver']:
                if job['kind']=='reply_receiver':
                    incoming=next(x for x in ev if x['kind']=='reply_arrival' and x['sha256']==job['input_sha256'])
                    assert incoming['arrival_us']==job['enqueued_us']
                elif job['kind']=='request_receiver':
                    trigger=next(x for x in run['rows'] if x['index']==job['index'])
                    assert trigger['horizon_us']<475000 and trigger['receiver_end_us']==job['enqueued_us']
            for row in run['rows']:
                job=next(x for x in byres['source'] if x['kind']=='normal_source' and x['index']==row['index'])
                assert [job[k] for k in ['enqueued_us','start_us','end_us']]==[row[k] for k in ['source_arrival_us','sender_start_us','sender_end_us']]
                assert row['link']['enqueued_us']==row['sender_end_us'] and row['link']['sha256']==row['packet_sha256']
            rows={x['index']:x for x in run['rows']};templates=collections.OrderedDict();old=rootinfo;positive=(old,rootpossible);parent=root;possible=rootpossible;history={rootref:root};authority=[rootref+payload(root)['horizon_us'],receipt];seenref=rootref;seenseq=ss(root);grants=[(receipt,authority[0]-200000)];inflight=None;request_by_reply={}
            for event in [x for x in ev if x['kind']=='reply_source']:
                req=decode(wire(event['input_sha256']));cached=[root]+[raws[x['ref_us']] for x in run['rows'] if x['sender_end_us']<=event['start_us']];cached=cached[-8:];rep=next(x for x in run['repairs'] if x['request_sha256']==event['input_sha256']);assert rep['stats']['cache']==[dict(ref=rr(x),sha256=rd(x)) for x in cached];reply=decode(wire(rep['reply_sha256']));request_by_reply[rep['reply_sha256']]=req;assert reply['request']==req['id'];cachekeys={rr(x) for x in cached}
                for raw in reply['missing']:assert rr(raw) in cachekeys and raw==raws[rr(raw)] and rr(raw)<=req['target_ref']
                for p in reply['patches']:assert rr(p['fragment']) in cachekeys and rr(p['fragment'])<=req['target_ref']
                counts['cache_snapshots']+=1
            for job in byres['receiver']:
                start,end=job['start_us'],job['end_us']
                if job['kind']=='request_receiver':
                    sent=next((x for x in ev if x['kind']=='request_arrival' and x['enqueued_us']==end),None)
                    if sent:
                        req=decode(wire(sent['sha256']));bare={k:v for k,v in req.items() if k!='id'};assert hashlib.sha256(body.canonical(bare)).hexdigest()==req['id'];assert inflight is None and req['parent']==rd(parent) and req['target']==rd(history[req['target_ref']]);assert req['received']==[rd(x) for x in history.values()];assert req['budgets']==budgets(positive[0]) and req['extra']==(run['method'] in ('backward','backward_fine'));inflight=req
                    continue
                if job['kind']=='normal_receiver':
                    row=rows[job['index']];raw=raws[row['ref_us']];packet=refmod.unpack(wire(row['packet_sha256']),templates,True);assert packet['steps']==[raw] and packet['anchor']==rm['anchor']['identity'];assert seenref<rr(raw)<=start and seenseq<ss(raw);assert job['enqueued_us']==row['link']['arrival_us'];h,old,possible=step(old,sourceinfos[rr(raw)],possible,fine,row['horizon_us']);assert h==row['horizon_us'];seenref,seenseq=rr(raw),ss(raw);history[rr(raw)]=raw
                    while len(history)>32:history.pop(next(iter(history)))
                    if h>=475000:parent=raw;positive=(old,possible)
                    endpoint=rr(raw)+h
                    if h>0 and endpoint>authority[0]:authority=[endpoint,end]
                    assert authority==row['authority'] and rr(old['raw'])==row['fact_ref_us'];age=max(50000,math.ceil((end-rr(raw))/50000)*50000);assert row['fresh_admission']==(h>age+200000) and row['age_us']==age;counts['normal_receipts']+=1
                else:
                    assert job['kind']=='reply_receiver';reply=decode(wire(job['input_sha256']));req=request_by_reply[job['input_sha256']];assert inflight==req;inflight=None;rep=next(x for x in run['repairs'] if x['reply_sha256']==job['input_sha256']);decision=rep['decision'];h=0
                    if rd(parent)!=req['parent']:assert decision['reason']=='stale_parent';continue
                    if reply['reason'] is not None:assert decision['reason']==reply['reason'];continue
                    merged=dict(history)
                    for raw in reply['missing']:merged[rr(raw)]=raw
                    oo,pp=positive;pa=parent;best=None;patches={x['target']:x for x in reply['patches']};steps=[]
                    for raw in sorted((x for x in merged.values() if rr(x)>rr(parent)),key=rr):
                        nd=sourceinfos[rr(raw)];expected=decision['steps'][len(steps)]['horizon_us'];before=oo;beforepossible=pp
                        if rd(raw) in patches:
                            p=patches[rd(raw)];assert p['parent']==rd(pa);f=patch(oo,nd,p['fragment'])
                            if fine:pp={n:pp[n]&~mask(f,n,True) for n in grids};h,oo,pp=step(oo,nd,pp,True,expected)
                            else:h,oo,pp=475000,nd,None
                        else:h,oo,pp=step(oo,nd,pp,fine,expected)
                        steps.append(dict(ref=rr(raw),horizon_us=h));assert expected==h
                        if h>=475000:best=(h,oo,pp,raw);pa=raw
                        else:break
                    assert steps==decision['steps']
                    if best:
                        h,old,possible,parent=best;positive=(old,possible);endpoint=rr(parent)+h
                        if endpoint>authority[0]:authority=[endpoint,end]
                        for raw in reply['missing']:history[rr(raw)]=raw
                        while len(history)>32:history.pop(next(iter(history)))
                    else:h=0
                    assert decision['horizon_us']==h and authority==rep['authority'] and rr(old['raw'])==rep['fact_ref_us'];counts['repair_receipts']+=1
                if h>0:grants.append((end,endpoint-200000))
            for i,row in rows.items():
                assert row['dropped']==(run['preset']=='blackout' and i in (27,28,29));src=next(x for x in pipeline if x['run']==name and x['id']=='drive_%03d'%i and x['repeat']==run['repeat']);assert row['generation_ms']==src['generation_ms'] and row['source_arrival_us']==src['arrival_us'];assert row['sender_end_us']==row['sender_start_us']+charge(row['generation_ms']+row['encoding_ms']);counts['normal_rows']+=1
            cov=run['coverage'];busy=[(x['start_us'],x['end_us']) for x in byres['receiver']];assert cov['grants']==[list(x) for x in grants] and cov['cpu']==[list(x) for x in busy];points=sorted(set([cov['start_us'],cov['end_us']]+[max(cov['start_us'],min(cov['end_us'],x)) for p in grants+busy for x in p]));allowed=[]
            for a0,b0 in zip(points,points[1:]):
                if any(x<=a0 and b0<=y for x,y in grants) and not any(x<b0 and a0<y for x,y in busy):allowed.append((a0,b0))
            intervals=union(allowed,cov['start_us'],cov['end_us']);assert cov['intervals']==intervals and cov['covered_us']==sum(b-a for a,b in intervals);assert cov['coverage']==cov['covered_us']/(cov['end_us']-cov['start_us']);counts['coverage_rows']+=1
        print(json.dumps(dict(run=name,**counts)),flush=True)
    for f,h in data['source_sha256'].items():assert sha(Path(__file__).parent/f)==h
    assert counts['normal_rows']==len(data['runs'])*20
    assert not any(n in sys.modules for n in ['repair','backward','context','bench','guard','flow','compact','observer','dictionary'])
    result=dict(counts=counts,analyzer_sha256=sha(Path(__file__)),data_sha256=sha(a.study/'analysis.json'),input_sha256=input_hashes,scope='Independent accepted prefixes, pointcloud provenance, historical vertex KD preimages, scalar geometry, fine KD propagation and H/H+1, received-only replay, request bindings, cache chronology, CPU/link FIFO, expiry and busy-subtracted coverage; no tested/native algorithm imports.')
    a.out.write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
