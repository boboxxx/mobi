"""Paid receiver-owned facts, separate finite action certificates."""
import collections, hashlib, math, sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'compact_observer_20261002'))
import compact
body=compact.body; base=compact.base
METHODS=['fixed_strict','fixed_forward','fixed_terminal','coarse_forward','coarse_terminal','fine_forward','fine_terminal']


def terminal_distance(v0,v1,a,dt):
    if any(not math.isfinite(x) or x<0 for x in [v0,v1,a,dt]):raise ValueError('Invalid travel contract')
    if dt==0:return 0.
    if a==0:d=min(v0,v1)*dt
    else:
        c=min(dt,max(0.,(v1-v0+a*dt)/(2*a)))
        d=v0*c+.5*a*c*c+v1*(dt-c)+.5*a*(dt-c)**2
    if not math.isfinite(d):raise ValueError('Travel overflow')
    return float(np.nextafter(d,math.inf))


def cached(cache,key,make,limit):
    if key in cache:
        value=cache.pop(key);cache[key]=value;return value,True
    value=make();cache[key]=value
    if len(cache)>limit:cache.popitem(last=False)
    return value,False


class Receiver:
    def __init__(self,method,profiles,contract,windows):
        if method not in METHODS:raise ValueError('Method')
        self.method=method;self.position=not method.startswith('fixed');self.terminal=method.endswith('terminal')
        self.core=(compact.PositionReceiver(profiles,contract,windows,2 if method.startswith('fine') else 1)
                   if self.position else compact.FixedReceiver(profiles,contract))
        self.profiles=profiles;self.contract=contract;self.pending=None

    def register(self,legacy,blob,scope,motion):
        anchor=self.core.register(legacy,blob,scope,motion);self.anchor=anchor
        raw=compact.json.loads(blob)['raw'];p,o,r=body.decode(body.canonical(raw),self.profiles,scope,self.contract)
        self.root_effective={n:base.reference_speed(g,r,p['reference_us']) for n,g in self.profiles.items()}
        self.root_budget={n:body.travel(p['horizon_us']/1e6+g.clock,self.root_effective[n]) for n,g in self.profiles.items()}
        if self.position:self.root_state=self.core._states[anchor.identity]
        return anchor

    def reset(self,root_receipt_us):
        if not compact.integer(root_receipt_us) or root_receipt_us<self.anchor.reference_us:raise ValueError('Trusted warm root receipt')
        self.ref=self.seen_ref=self.anchor.reference_us;self.seq=self.seen_seq=self.anchor.sequence
        self.previous_h=self.anchor.endpoint_us-self.anchor.reference_us
        self.effective=self.root_effective;self.budget=self.root_budget
        if self.position:self.state=self.root_state
        self.masks=collections.OrderedDict();self.updates=collections.OrderedDict();self.covers=collections.OrderedDict()
        self.authority=(self.anchor.endpoint_us,root_receipt_us);self.pending=None;self.clock=root_receipt_us

    def advance(self,transport,started_us):
        if not compact.integer(started_us) or started_us<self.clock or self.pending is not None:raise ValueError('Receiver clock/pending')
        packet=compact.decode(transport)
        kind='position-flow-v1' if self.position else 'center-flow-v1'
        if packet['kind']!=kind or packet['dynamics']!='observation-speed-age-v1' or packet['anchor']!=self.anchor.identity or len(packet['steps'])!=1:raise ValueError('Flow schema/root')
        p,o,r=body.decode(body.canonical(packet['steps'][0]),self.profiles,self.anchor.scope,self.contract)
        ref,seq=p['reference_us'],p['sequence'];h=p['horizon_us']
        if not self.seen_ref<ref<=started_us or seq<=self.seen_seq:raise ValueError('Source order/replay/future')
        grid=self.core.grid_profiles if self.position else self.profiles
        current={n:base.reference_speed(g,r,ref) for n,g in grid.items()}
        dt=(ref-self.ref)/1e6
        distances={n:terminal_distance(self.effective[n].speed,current[n].speed,g.acceleration,dt) if self.terminal
                   else body.travel(dt,self.effective[n]) for n,g in grid.items()}
        key=compact.geometry_key(o,r,ref);stats=dict(mask_hits=0,update_hits=0,cover_hits=0)
        classes=None;accepted=False;reason=None;state=None
        if self.position:
            def make_masks():
                v=body.projections(o,r,ref,self.profiles,self.anchor.scope,self.contract)
                return {n:compact.observer.exclusion(v[n],g,self.anchor.motion) for n,g in grid.items()}
            masks,hit=cached(self.masks,key,make_masks,4);stats['mask_hits']=int(hit);possible={}
            for n,g in grid.items():
                uk=(n,key,distances[n],self.state.possible[n].tobytes())
                def make_update(n=n,g=g):
                    x=compact.propagate(self.state.possible[n],g.step,distances[n])&~masks[n];x.setflags(write=False);return x
                possible[n],hit=cached(self.updates,uk,make_update,64);stats['update_hits']+=int(hit)
            state=compact.observer.State(ref,seq,possible,current)
            classes={n:compact.observer.frontier(possible[n],current[n],self.anchor.motion) for n in grid}
            h=min(x['horizon_us'] for x in classes.values());accepted=True
        else:
            bridge=(ref<self.ref+self.previous_h and ref+h>self.ref+self.previous_h) if self.method=='fixed_strict' else all(distances[n]<=self.budget[n] for n in grid)
            if not bridge:reason='past_bridge_unproved';h=0
            else:
                def make_cover():
                    v=body.projections(o,r,ref,self.profiles,self.anchor.scope,self.contract)
                    c={n:base.collar(g,self.anchor,h/1e6,r,ref) for n,g in grid.items()}
                    return compact.stream.cover(v,self.profiles,self.anchor.motion,c,len(r))
                ok,hit=cached(self.covers,(key,h),make_cover,4);stats['cover_hits']=int(hit)
                if ok:accepted=True
                else:reason='current_collar_unproved';h=0
        # Fully checked source can advance replay guards even when a fact bridge fails.
        self.seen_ref,self.seen_seq=ref,seq
        if accepted:
            self.ref,self.seq,self.effective=ref,seq,current
            if self.position:self.state=state
            else:self.budget={n:body.travel(h/1e6+g.clock,current[n]) for n,g in grid.items()}
            self.previous_h=h
        decision=dict(reference_us=ref,sequence=seq,horizon_us=h,endpoint_us=ref+h,fact_accepted=accepted,
                      reason=reason,past_distances=distances,classes=classes,cache=stats)
        self.pending=(started_us,ref+h,h);return decision,state

    def finish(self,verified_end_us):
        if self.pending is None or not compact.integer(verified_end_us) or verified_end_us<self.pending[0]:raise ValueError('Completion clock/pending')
        _,end,h=self.pending
        if h>0 and end>self.authority[0]:self.authority=(end,verified_end_us)
        self.clock=verified_end_us;self.pending=None

    def can_act(self,now_us,reserve_us=200000):
        if not compact.integer(now_us) or not compact.integer(reserve_us) or reserve_us<0 or now_us<self.clock:return False
        end,available=self.authority
        return self.pending is None and available<=now_us and now_us+reserve_us<end

    @property
    def previous_h(self):return self._previous_h if hasattr(self,'_previous_h') else self.anchor.endpoint_us-self.anchor.reference_us
    @previous_h.setter
    def previous_h(self,x):self._previous_h=x
