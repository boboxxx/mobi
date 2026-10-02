"""Bounded request-bound historical negative evidence; no standalone grant."""
import collections,copy,hashlib,json,math,zlib
import numpy as np
import backward
G=backward.guard;body=G.body;flow=G.flow;compact=G.compact
LIMIT=4*1024*1024

def pack(value):
    data=body.canonical(value)
    if len(data)>LIMIT:raise ValueError('Message limit')
    return zlib.compress(data)

def unpack(wire):
    if not isinstance(wire,bytes) or len(wire)>LIMIT:raise ValueError('Message limit')
    z=zlib.decompressobj();data=z.decompress(wire,LIMIT+1)
    if len(data)>LIMIT or not z.eof or z.unused_data or z.unconsumed_tail:raise ValueError('Expansion')
    return json.loads(data)

def ref(raw):return raw['payload']['reference_us']
def seq(raw):return raw['payload']['sequence']
def digest(raw):return raw['sha256']
def envelope(core,raw):return compact.encode(dict(kind='position-flow-v1' if core.position else 'class-guard-flow-v1',dynamics='observation-speed-age-v1',anchor=core.anchor.identity,steps=[raw]))

def snapshot(core):
    # Share immutable geometry and native handles; copy all mutable replay caches.
    c=copy.copy(core)
    for name in ('covers','masks','updates'):
        if hasattr(c,name):setattr(c,name,collections.OrderedDict(getattr(c,name)))
    c.pending=None
    return c

def budget(core,h=475000):
    return {n:body.travel(h/1e6+g.clock,core.effective[n]) for n,g in core.profiles.items()}

def patch_check(parent,current,fragment,budgets,profiles,contract,anchor):
    p,o,r=body.decode(body.canonical(fragment),profiles,anchor.scope,contract)
    if (p['reference_us'],p['sequence'])!=(ref(parent),seq(parent)) or p['horizon_us']!=475000:raise ValueError('Fragment historical binding')
    needed,stats=backward.demand(parent,current,budgets,profiles,contract,anchor.scope,anchor.motion)
    if needed is None:raise ValueError('Unbounded predecessor')
    v=body.projections(o,r,p['reference_us'],profiles,anchor.scope,contract)
    if not G.stream.cover(v,profiles,anchor.motion,needed,len(r)):raise ValueError('Incomplete predecessor evidence')
    return stats

def ordinary_supported(previous,current,budgets,profiles,contract,anchor):
    p0,o0,r0=body.decode(body.canonical(previous),profiles,anchor.scope,contract);p,o,r=body.decode(body.canonical(current),profiles,anchor.scope,contract)
    v=body.projections(o,r,p['reference_us'],profiles,anchor.scope,contract);cells={}
    for n,g in profiles.items():
        old=G.stream.base.reference_speed(g,r0,p0['reference_us']);new=G.stream.base.reference_speed(g,r,p['reference_us']);d=flow.terminal_distance(old.speed,new.speed,g.acceleration,(ref(current)-ref(previous))/1e6);radius=float(np.nextafter(g.r_max+budgets[n]-d,-math.inf));c=body.required(new,anchor.motion,.475)
        if c is None:return False
        lo,hi,margin=body.envelope(anchor.motion,0.,g.clock);known=body.box_distance(c,lo,hi)+g.step/math.sqrt(2)<margin+radius-1e-9 if radius>=0 else np.zeros(len(c),dtype=bool);cells[n]=c[~known]
    return G.stream.cover(v,profiles,anchor.motion,cells,len(r))

def install_patch(core,parent,current,fragment,budgets,started):
    stats=patch_check(parent,current,fragment,budgets,core.profiles,core.contract,core.anchor)
    p,o,r=body.decode(body.canonical(fragment),core.profiles,core.anchor.scope,core.contract)
    if core.position:
        v=body.projections(o,r,p['reference_us'],core.profiles,core.anchor.scope,core.contract);possible={}
        for n,g in core.core.grid_profiles.items():
            x=core.state.possible[n]&~compact.observer.exclusion(v[n],g,core.anchor.motion);x.setflags(write=False);possible[n]=x
        core.state=compact.observer.State(core.ref,core.seq,possible,core.effective)
        decision,state=core.advance(envelope(core,current),started)
    else:
        p,o,r=body.decode(body.canonical(current),core.profiles,core.anchor.scope,core.contract)
        core.ref=core.seen_ref=p['reference_us'];core.seq=core.seen_seq=p['sequence'];core.effective={n:G.stream.base.reference_speed(g,r,core.ref) for n,g in core.profiles.items()};core.budget=budget(core);core.pending=(started,core.ref+475000,475000)
        decision=dict(reference_us=core.ref,sequence=core.seq,horizon_us=475000,endpoint_us=core.ref+475000,fact_accepted=True);state=None
    return decision,state,stats

class Receiver:
    def __init__(self,transport,root,mode):
        self.transport=transport;self.mode=mode;self.history=collections.OrderedDict([(ref(root),root)]);self.positive= snapshot(transport.core);self.parent=root;self.inflight=None;self.serial=0;self.suppressed=set();self.last=None
    @property
    def core(self):return self.transport.core
    def remember(self,raw):
        self.history[ref(raw)]=raw
        while len(self.history)>32:self.history.popitem(last=False)
    def normal(self,wire,raw,started):
        original=self.core.advance;decoded=[]
        def tap(inner,when):
            decoded.append(compact.decode(inner)['steps'][0])
            if body.canonical(decoded[0])!=body.canonical(raw):raise ValueError('Raw wire binding')
            return original(inner,when)
        self.core.advance=tap
        try:decision,state=self.transport.advance(wire,started)
        finally:del self.core.advance
        if len(decoded)!=1 or body.canonical(decoded[0])!=body.canonical(raw):raise ValueError('Raw wire binding')
        # The raw supplied by the harness must be exactly what the actual wire checked.
        if (decision['reference_us'],decision['sequence'])!=(ref(raw),seq(raw)):raise ValueError('Decoded identity')
        self.remember(raw);self.last=raw
        return decision,state
    def normal_finish(self,end,decision):
        self.core.finish(end)
        if decision['horizon_us']>=475000:self.parent=self.last;self.positive=snapshot(self.core)
    def request_key(self,target):
        p,o,r=body.decode(body.canonical(target),self.core.profiles,self.core.anchor.scope,self.core.contract)
        return (digest(self.parent),compact.geometry_key(o,r,p['reference_us']))
    def request(self,target):
        if self.mode=='none' or self.inflight is not None:return None
        key=self.request_key(target)
        if key in self.suppressed or ref(target)<=ref(self.parent):return None
        self.serial+=1
        q=dict(kind='historical-request-v1',serial=self.serial,anchor=self.core.anchor.identity,parent=digest(self.parent),target=digest(target),parent_ref=ref(self.parent),target_ref=ref(target),received=[digest(x) for x in self.history.values()],budgets=budget(self.positive),extra=self.mode=='backward')
        q['id']=hashlib.sha256(body.canonical(q)).hexdigest();self.inflight=(q,key);return pack(q)
    def reply(self,wire,started):
        if started<self.core.clock or self.core.pending is not None:raise ValueError('Receiver clock/pending')
        q=unpack(wire)
        if self.inflight is None:raise ValueError('Unsolicited or duplicate reply')
        req,key=self.inflight
        if not isinstance(q,dict) or set(q)!={'kind','request','parent','target','missing','patches','reason'} or q['kind']!='historical-reply-v1' or (q['request'],q['parent'],q['target'])!=(req['id'],req['parent'],req['target']):raise ValueError('Reply binding')
        self.inflight=None;self.suppressed.add(key)
        if digest(self.parent)!=req['parent']:return dict(reason='stale_parent',horizon_us=0),None
        if q['reason'] is not None:return dict(reason=q['reason'],horizon_us=0),None
        if not isinstance(q['missing'],list) or len(q['missing'])>8 or not isinstance(q['patches'],list) or len(q['patches'])>8:raise ValueError('Bounded history')
        merged=dict(self.history)
        for raw in q['missing']:
            body.decode(body.canonical(raw),self.core.profiles,self.core.anchor.scope,self.core.contract)
            if not ref(self.parent)<ref(raw)<=req['target_ref'] or ref(raw)>started:raise ValueError('Backfill time')
            if ref(raw) in merged and digest(merged[ref(raw)])!=digest(raw):raise ValueError('Conflicting history')
            merged[ref(raw)]=raw
        if len(merged)>40:raise ValueError('Bounded merge')
        if req['target_ref'] not in merged or digest(merged[req['target_ref']])!=req['target']:raise ValueError('Target not received')
        patches={}
        for patch in q['patches']:
            if not isinstance(patch,dict) or set(patch)!={'parent','target','fragment'} or patch['target'] in patches:raise ValueError('Patch schema')
            patches[patch['target']]=patch
        shadow=snapshot(self.positive);shadow.clock=started;shadow.pending=None;parent=self.parent;positive=snapshot(shadow);best=None;used=[];steps=[]
        for raw in sorted((x for x in merged.values() if ref(x)>ref(parent)),key=ref):
            before=snapshot(shadow);b=budget(shadow);decision,state=shadow.advance(envelope(shadow,raw),started)
            if decision['horizon_us']<475000 and digest(raw) in patches:
                patch=patches[digest(raw)]
                if patch['parent']!=digest(parent):raise ValueError('Patch parent')
                shadow=before;decision,state,stats=install_patch(shadow,parent,raw,patch['fragment'],b,started);used.append(digest(raw))
            shadow.finish(started);steps.append(dict(ref=ref(raw),horizon_us=decision['horizon_us']))
            if decision['horizon_us']>=475000:parent=raw;positive=snapshot(shadow);best=decision
            # A failed positional fact is retained during ordinary replay; a patch
            # cannot use it as a positive parent. Stop at first such failure.
            else:break
        if set(used)!=set(patches):raise ValueError('Unused or unsupported patch')
        if best is None:return dict(reason='replay_unproved',horizon_us=0,steps=steps),None
        old=self.core;positive.seen_ref=max(old.seen_ref,positive.seen_ref);positive.seen_seq=max(old.seen_seq,positive.seen_seq);positive.authority=old.authority;positive.clock=started;positive.pending=(started,best['endpoint_us'],best['horizon_us'])
        self.transport.core=positive;self.parent=parent;self.positive=snapshot(positive)
        for raw in q['missing']:self.remember(raw)
        return dict(reason=None,horizon_us=best['horizon_us'],endpoint_us=best['endpoint_us'],reference_us=best['reference_us'],steps=steps,patches_used=used),positive.state if positive.position else None
    def reply_finish(self,end):
        if self.core.pending is not None:self.core.finish(end)
        else:self.core.clock=end
        self.positive.clock=end;self.positive.authority=self.core.authority

class Source:
    def __init__(self,profiles,contract,anchor):self.cache=collections.OrderedDict();self.profiles=profiles;self.contract=contract;self.anchor=anchor
    def add(self,raw,cloud,stamp):
        self.cache[ref(raw)]=(raw,cloud,stamp)
        while len(self.cache)>8:self.cache.popitem(last=False)
    def reply(self,wire):
        req=unpack(wire);saved=[dict(ref=k,sha256=digest(v[0])) for k,v in self.cache.items()]
        result=dict(kind='historical-reply-v1',request=req['id'],parent=req['parent'],target=req['target'],missing=[],patches=[],reason=None);stats=dict(cache=saved,transitions=[])
        if req['anchor']!=self.anchor.identity:raise ValueError('Request scope')
        if any(k not in self.cache for k in [req['parent_ref'],req['target_ref']]):result['reason']='cache_miss';return pack(result),stats
        previous=self.cache[req['parent_ref']][0]
        if digest(previous)!=req['parent'] or digest(self.cache[req['target_ref']][0])!=req['target']:raise ValueError('Request digest')
        b=req['budgets']
        for k,(current,_,_) in list(self.cache.items()):
            if not req['parent_ref']<k<=req['target_ref']:continue
            if digest(current) not in req['received']:result['missing'].append(current)
            supported=ordinary_supported(previous,current,b,self.profiles,self.contract,self.anchor)
            info=dict(ordinary_supported=bool(supported));stats['transitions'].append(dict(parent=ref(previous),target=k,**info))
            if not supported:
                if not req['extra']:result['reason']='replay_unproved';break
                needed,info=backward.demand(previous,current,b,self.profiles,self.contract,self.anchor.scope,self.anchor.motion);stats['transitions'][-1].update(info)
                if needed is None:result['reason']=info['reason'];break
                _,cloud,stamp=self.cache[ref(previous)]
                if any(len(x) for x in needed.values()):
                    with np.load(cloud) as data:fragment,selection=backward.select(data['xyz'],data['origin'],stamp,ref(previous),self.profiles,self.contract,self.anchor.scope,self.anchor.motion,needed,seq(previous))
                else:fragment,selection=previous,dict(reason=None,rays=0,already_received=True)
                stats['transitions'][-1]['selection']=selection
                if fragment is None:result['reason']=selection['reason'];break
                result['patches'].append(dict(parent=digest(previous),target=digest(current),fragment=fragment))
            p,o,r=body.decode(body.canonical(current),self.profiles,self.anchor.scope,self.contract);b={n:body.travel(.475+g.clock,G.stream.base.reference_speed(g,r,p['reference_us'])) for n,g in self.profiles.items()};previous=current
        # An incomplete reply cannot convey an unverified partial proposal.
        if result['reason'] is not None:result['missing']=[];result['patches']=[]
        return pack(result),stats
