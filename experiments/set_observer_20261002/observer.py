"""Established conservative position-set observer on received raw observations."""
import copy, ctypes, functools, hashlib, json, math, os, sys, zlib
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'streaming_recovery_20261002'))
import stream
base=stream.base;body=stream.body


@functools.lru_cache(maxsize=1)
def library():
    f=ctypes.CDLL(os.environ['MOBI_MASK_LIBRARY']).ray_mask
    d=np.ctypeslib.ndpointer(dtype=np.float64,ndim=1,flags='C_CONTIGUOUS')
    b=np.ctypeslib.ndpointer(dtype=np.uint8,ndim=1,flags='C_CONTIGUOUS')
    f.argtypes=[ctypes.c_int64,d,ctypes.c_int64,ctypes.c_double,ctypes.c_double,b];f.restype=ctypes.c_int
    return f


def exclusion(result,profile,motion):
    n=round(2*profile.domain/profile.step)
    xy=result['witnesses']@body.rotation(motion.yaw)
    radius=profile.r_min-result['error']-profile.step/math.sqrt(2)-1e-9
    w=np.ascontiguousarray(np.column_stack([xy,radius]).ravel(),dtype=np.float64)
    output=np.empty(n*n,dtype=np.uint8)
    if library()(len(xy),w,n,profile.domain,profile.step,output):raise ValueError('Invalid ray mask')
    return output.reshape(n,n).astype(bool)


def propagate(possible,step,distance):
    if possible.ndim!=2 or possible.shape[0]!=possible.shape[1] or possible.dtype!=bool or not math.isfinite(distance) or distance<0:
        raise ValueError('Invalid conservative state')
    n=len(possible);vertices=np.zeros((n+1,n+1),dtype=bool)
    for di,dj in [(0,0),(0,1),(1,0),(1,1)]:vertices[di:di+n,dj:dj+n]|=possible
    if possible.any():
        d=distance_transform_edt(~vertices,sampling=step)
        best=np.minimum.reduce([d[:-1,:-1],d[:-1,1:],d[1:,:-1],d[1:,1:]])
        reached=best<=distance+1e-9
    else:reached=np.zeros_like(possible)
    # Unknown centers outside the finite square may arrive at any boundary.
    axis=np.arange(n);boundary=step*np.minimum(axis,n-1-axis)
    return reached|(np.minimum(boundary[:,None],boundary[None,:])<=distance+1e-9)


def frontier(possible,profile,motion,cap_us=2_000_000):
    cells=body.grid(profile.domain,profile.step)[0];unknown=cells[possible.ravel()]
    low,high,margin=body.envelope(motion,0.,profile.clock)
    dist=body.box_distance(unknown,low,high);nearest=float(dist.min()) if len(dist) else math.inf
    extent=np.maximum(np.abs(low),np.abs(high));q=profile.step/math.sqrt(2)
    def passes(h):
        inflate=margin+profile.r_max+body.travel(h/1e6+profile.clock,profile)
        return bool(np.all(extent+inflate<profile.domain) and nearest>inflate+q)
    lo,hi=0,cap_us+1
    while hi-lo>1:
        mid=(hi+lo)//2
        if passes(mid):lo=mid
        else:hi=mid
    assert lo==0 or passes(lo)
    assert lo==cap_us or not passes(lo+1)
    return dict(horizon_us=lo,possible_cells=int(possible.sum()),nearest_possible_distance_m=nearest if math.isfinite(nearest) else None,
                nearest_possible_cell=unknown[int(np.argmin(dist))].tolist() if len(dist) else None)


@dataclass
class State:
    reference_us:int
    sequence:int
    possible:dict
    effective_profiles:dict


def wire(anchor,steps):
    if not 1<=len(steps)<=base.MAX_STEPS:return None
    blob=body.canonical(dict(kind='position-observations-v1',dynamics='observation-speed-age-v1',anchor=anchor.identity,steps=steps))
    return stream.encode(blob) if len(blob)<=base.MAX_BYTES else None


class Receiver(base.Receiver):
    def __init__(self,profiles,contract):
        super().__init__(profiles,contract);self._states={};self.last_state=None

    def register(self,legacy,blob,scope,motion):
        anchor=super().register(legacy,blob,scope,motion)
        raw=json.loads(blob)['raw'];p,o,r=body.decode(body.canonical(raw),self.profiles,scope,self.contract)
        v=body.projections(o,r,p['reference_us'],self.profiles,scope,self.contract)
        possible={};effective={}
        for n,profile in self.profiles.items():
            effective[n]=base.reference_speed(profile,r,p['reference_us'])
            c=body.grid(profile.domain,profile.step)[0];size=round(2*profile.domain/profile.step)
            low,high,margin=body.envelope(motion,p['horizon_us']/1e6,profile.clock)
            inflate=margin+profile.r_max+body.travel(p['horizon_us']/1e6+profile.clock,effective[n])
            proved=body.box_distance(c,low,high)<=inflate+profile.step/math.sqrt(2)
            possible[n]=(~proved).reshape(size,size)&~exclusion(v[n],profile,motion)
        self._states[anchor.identity]=State(anchor.reference_us,anchor.sequence,possible,effective)
        return anchor

    def rebuild(self,transport):
        b=json.loads(stream.decode(transport))
        if set(b)!={'kind','dynamics','anchor','steps'} or b['kind']!='position-observations-v1' or b['dynamics']!='observation-speed-age-v1':raise ValueError('Wrong observation bundle')
        anchor=self._anchors[b['anchor']]
        if not isinstance(b['steps'],list) or not 1<=len(b['steps'])<=base.MAX_STEPS:raise ValueError('Step bound')
        state=self._states[anchor.identity];steps=0
        for raw in b['steps']:
            p,o,r=body.decode(body.canonical(raw),self.profiles,anchor.scope,self.contract)
            ref=p['reference_us']
            if ref<=state.reference_us or p['sequence']<=state.sequence:raise ValueError('Future/order/replay')
            v=body.projections(o,r,ref,self.profiles,anchor.scope,self.contract)
            dt=(ref-state.reference_us)/1e6;possible={};effective={}
            for n,profile in self.profiles.items():
                distance=body.travel(dt,state.effective_profiles[n])
                prediction=propagate(state.possible[n],profile.step,distance)
                possible[n]=prediction&~exclusion(v[n],profile,anchor.motion)
                effective[n]=base.reference_speed(profile,r,ref)
            state=State(ref,p['sequence'],possible,effective);steps+=1
        classes={n:frontier(state.possible[n],state.effective_profiles[n],anchor.motion) for n in self.profiles}
        h=min(x['horizon_us'] for x in classes.values())
        decision=dict(reference_us=state.reference_us,endpoint_us=state.reference_us+h,sequence=state.sequence,
                      horizon_us=h,classes=classes,steps=steps,anchor=anchor.identity)
        return decision,state

    def inspect(self,transport):return self.rebuild(transport)[0]

    def accept(self,transport,now,execution=0.):
        try:
            if not math.isfinite(now) or not math.isfinite(execution) or execution<0:return False
            decision,state=self.rebuild(transport)
            receipt=math.ceil(Fraction.from_float(float(now))*1e6);action=math.ceil(Fraction.from_float(float(execution))*1e6)
            if receipt<decision['reference_us'] or receipt+action>=decision['endpoint_us'] or decision['reference_us']<=self._last_reference or decision['sequence']<=self._last_sequence:return False
            self.last=decision;self.last_state=state;self._last_reference=state.reference_us;self._last_sequence=state.sequence;return True
        except (ValueError,TypeError,KeyError,OverflowError,IndexError,zlib.error):return False
