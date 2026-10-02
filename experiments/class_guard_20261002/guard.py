"""Retain class-specific free-region guards; finite joint authority."""
import collections,hashlib,json,math,sys,time,zlib
from dataclasses import replace
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'recursive_validity_20261002'))
import flow,dictionary
body=flow.body;compact=flow.compact;stream=compact.stream

def missing(result,profile,motion,cells):
    left=np.ones(len(cells),dtype=bool);w=result['witnesses']@body.rotation(motion.yaw)
    for error in np.unique(result['error']):
        radius=profile.r_min-error-profile.step/math.sqrt(2)-1e-9;todo=np.flatnonzero(left)
        if radius<=0 or not len(todo):continue
        d=cKDTree(w[result['error']==error]).query(cells[todo],k=1)[0];left[todo[d<radius]]=False
    return cells[left]

def augment(raw,points,origin,stamp,profiles,contract,anchor,horizons):
    p,oo,rr=body.decode(body.canonical(raw),profiles,anchor.scope,contract)
    if p['reference_us']!=math.ceil(stamp*1e6):raise ValueError('Source reference mismatch')
    old=stream.base.shared_projections(oo,rr,p['reference_us'],profiles,anchor.scope,contract);needed={}
    for n,g in profiles.items():
        cells=stream.base.collar(g,anchor,horizons[n]/1e6,rr,p['reference_us']);needed[n]=missing(old[n],g,anchor.motion,cells)
    o,r,ref=body.encode_source(points,origin,stamp,stamp)
    if ref!=p['reference_us']:raise ValueError('Source clock')
    active={n:profiles[n] for n in profiles if len(needed[n])};ids=[]
    if active:
        full=stream.base.shared_projections(o,r,ref,active,anchor.scope,contract)
        for n,g in active.items():
            ok,chosen=stream.base.supports(full[n],g,anchor.motion,needed[n],True)
            if not ok:return None,dict(reason='full_scan_collar_uncovered',klass=n,missing_cells=len(needed[n]))
            ids.extend(chosen)
    chosen=np.unique(ids).astype(np.int64);oldkeys=np.column_stack([oo[rr[:,0]],rr[:,1:]]);newkeys=np.column_stack([o[r[chosen,0]],r[chosen,1:]])
    keys=np.unique(np.concatenate([oldkeys,newkeys]),axis=0)
    if len(keys)>body.MAX_RAYS:return None,dict(reason='ray_limit',rays=len(keys))
    origins,index=np.unique(keys[:,:3],axis=0,return_inverse=True);rays=np.column_stack([index,keys[:,3:]])
    encoded=json.loads(body.serialize(origins,rays,ref,profiles,anchor.scope,contract,p['horizon_us']/1e6,p['sequence']))
    return encoded,dict(original_rays=len(rr),rays=len(rays),extra_rays=len(keys)-len(oldkeys),missing_cells={n:len(c) for n,c in needed.items()},reason=None)

class Receiver:
    def __init__(self,profiles,contract,horizons):
        if set(horizons)!=set(profiles) or any(type(h) is not int or h<1 for h in horizons.values()):raise ValueError('Class targets')
        self.profiles=profiles;self.contract=contract;self.horizons=horizons.copy();self.position=False;self.pending=None;self.validator=stream.base.Receiver(profiles,contract)
    def register(self,legacy,blob,scope,motion):
        if not isinstance(legacy,stream.base.LegacyReceiver):raise ValueError('Missing accepted legacy receiver')
        self.anchor=self.validator.register(legacy,blob,scope,motion)
        p,o,r=body.decode(body.canonical(json.loads(blob)['raw']),self.profiles,scope,self.contract)
        self.root_effective={n:stream.base.reference_speed(g,r,p['reference_us']) for n,g in self.profiles.items()};self.root_budget={n:body.travel(p['horizon_us']/1e6+g.clock,self.root_effective[n]) for n,g in self.profiles.items()}
        return self.anchor
    def establish_root(self,raw):
        p,o,r=body.decode(body.canonical(raw),self.profiles,self.anchor.scope,self.contract)
        if (p['reference_us'],p['sequence'])!=(self.anchor.reference_us,self.anchor.sequence):raise ValueError('Root reference')
        v=body.projections(o,r,p['reference_us'],self.profiles,self.anchor.scope,self.contract);cells={n:stream.base.collar(g,self.anchor,self.horizons[n]/1e6,r,p['reference_us']) for n,g in self.profiles.items()}
        if not stream.cover(v,self.profiles,self.anchor.motion,cells,len(r)):raise ValueError('Root guard unsupported')
        self.root_budget={n:body.travel(self.horizons[n]/1e6+g.clock,self.root_effective[n]) for n,g in self.profiles.items()}
    def reset(self,receipt):
        if not compact.integer(receipt) or receipt<self.anchor.reference_us:raise ValueError('Receipt')
        self.ref=self.seen_ref=self.anchor.reference_us;self.seq=self.seen_seq=self.anchor.sequence;self.effective=self.root_effective;self.budget=self.root_budget;self.clock=receipt;self.pending=None;self.authority=(self.anchor.endpoint_us,receipt);self.templates=collections.OrderedDict();self.covers=collections.OrderedDict()
    def advance(self,transport,started_us):
        if not compact.integer(started_us) or started_us<self.clock or self.pending is not None:raise ValueError('Clock/pending')
        packet=compact.decode(transport)
        if packet['kind']!='class-guard-flow-v1' or packet['dynamics']!='observation-speed-age-v1' or packet['anchor']!=self.anchor.identity or len(packet['steps'])!=1:raise ValueError('Typed class guard')
        p,o,r=body.decode(body.canonical(packet['steps'][0]),self.profiles,self.anchor.scope,self.contract);ref,seq=p['reference_us'],p['sequence']
        if p['horizon_us']!=min(self.horizons.values()):raise ValueError('Joint requested horizon')
        if not self.seen_ref<ref<=started_us or seq<=self.seen_seq:raise ValueError('Source order')
        current={n:stream.base.reference_speed(g,r,ref) for n,g in self.profiles.items()};dt=(ref-self.ref)/1e6;distances={n:flow.terminal_distance(self.effective[n].speed,current[n].speed,g.acceleration,dt) for n,g in self.profiles.items()}
        inherited={n:float(np.nextafter(g.r_max+self.budget[n]-distances[n],-math.inf)) for n,g in self.profiles.items()};key=(compact.geometry_key(o,r,ref),tuple(inherited.items()));hit=key in self.covers
        if hit:ok=self.covers[key]
        else:
            v=body.projections(o,r,ref,self.profiles,self.anchor.scope,self.contract);cells={}
            for n,g in self.profiles.items():
                required=body.required(current[n],self.anchor.motion,self.horizons[n]/1e6);lo,hi,margin=body.envelope(self.anchor.motion,0.,g.clock);q=g.step/math.sqrt(2)
                if required is None:cells[n]=None;continue
                inside=body.box_distance(required,lo,hi)+q<margin+inherited[n]-1e-9 if inherited[n]>=0 else np.zeros(len(required),dtype=bool);cells[n]=required[~inside]
            ok=stream.cover(v,self.profiles,self.anchor.motion,cells,len(r));self.covers[key]=ok
            if len(self.covers)>16:self.covers.popitem(last=False)
        self.seen_ref,self.seen_seq=ref,seq;h=min(self.horizons.values()) if ok else 0
        if ok:self.ref,self.seq,self.effective=ref,seq,current;self.budget={n:body.travel(self.horizons[n]/1e6+g.clock,current[n]) for n,g in self.profiles.items()}
        self.pending=(started_us,ref+h,h)
        return dict(reference_us=ref,sequence=seq,horizon_us=h,endpoint_us=ref+h,fact_accepted=bool(ok),past_distances=distances,inherited_radii=inherited,class_horizons=self.horizons.copy(),cache_hit=hit),None
    finish=flow.Receiver.finish
    can_act=flow.Receiver.can_act

class Transport:
    """Same bounded F/R bytes as all baselines; only stores validated facts."""
    def __init__(self,core):self.core=core
    def __getattr__(self,key):return getattr(self.core,key)
    def reset(self,receipt):self.core.reset(receipt);self.templates=collections.OrderedDict()
    def advance(self,transport,started):
        if not isinstance(transport,bytes) or len(transport)>compact.LIMIT or not transport.startswith(dictionary.MAGIC):raise ValueError('Transport')
        kind=transport[len(dictionary.MAGIC):len(dictionary.MAGIC)+1];inner=transport[len(dictionary.MAGIC)+1:];new=None
        if kind==b'F':
            packet=compact.decode(inner)
            if len(packet['steps'])!=1:raise ValueError('Step count')
            new=dictionary.template(packet['steps'][0])
        elif kind==b'R':
            z=zlib.decompressobj();data=z.decompress(inner,compact.LIMIT+1)
            if len(data)>compact.LIMIT or not z.eof or z.unused_data or z.unconsumed_tail:raise ValueError('Expansion')
            d=json.loads(data)
            if not isinstance(d,dict) or set(d)!={'template_sha256','header','step'} or not isinstance(d['header'],dict) or set(d['header'])!={'kind','dynamics','anchor'}:raise ValueError('Schema')
            row=d['step']
            if not isinstance(row,list) or len(row)!=4 or any(not compact.integer(x) for x in row[:3]) or not isinstance(row[3],str) or len(row[3])!=64:raise ValueError('Metadata')
            q=self.templates[d['template_sha256']];ref,h,seq,digest=row;p=dict(q,reference_us=ref,horizon_us=h,sequence=seq);p['rays']=[x[:4]+[ref-x[4]] for x in q['rays']];inner=compact.encode(dict(d['header'],steps=[dict(payload=p,sha256=digest)]))
        else:raise ValueError('Kind')
        result=self.core.advance(inner,started)
        if new:
            tid,q=new;self.templates[tid]=q
            if len(self.templates)>4:self.templates.popitem(last=False)
        return result
