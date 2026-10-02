"""Largest integer horizon of the corrected fixed-K tile condition.

This offline diagnostic is charged separately and never supplies a free online
horizon oracle to the frozen timing study. It retains grid/shape/dynamics bounds.
"""
import math
import numpy as np
from scipy.spatial import cKDTree
import stream
base=stream.base;body=stream.body


def compute(receiver,anchor_id,raw,cap_us=2_000_000):
    if not isinstance(receiver,base.Receiver) or type(cap_us) is not int or cap_us<1:
        raise ValueError('Receiver-owned root and positive cap required')
    anchor=receiver._anchors[anchor_id]
    p,o,r=body.decode(body.canonical(raw),receiver.profiles,anchor.scope,receiver.contract)
    v=body.projections(o,r,p['reference_us'],receiver.profiles,anchor.scope,receiver.contract)
    classes={}
    for n,profile in receiver.profiles.items():
        effective=base.reference_speed(profile,r,p['reference_us'])
        c=body.grid(profile.domain,profile.step)[0];low,high,margin=body.envelope(anchor.motion,0.,profile.clock)
        q=profile.step/math.sqrt(2)
        missing=~(body.box_distance(c,low,high)+q<margin+profile.r_max-1e-9)
        xy=v[n]['witnesses']@body.rotation(anchor.motion.yaw)
        for error in np.unique(v[n]['error']):
            radius=profile.r_min-error-q-1e-9
            todo=np.flatnonzero(missing)
            if radius<=0 or not len(todo):continue
            group=np.flatnonzero(v[n]['error']==error)
            near=cKDTree(xy[group]).query(c[todo],k=1)[0]
            missing[todo[near<radius]]=False
        unknown=c[missing];distance=body.box_distance(unknown,low,high)
        j=int(np.argmin(distance)) if len(distance) else None
        nearest=float(distance[j]) if j is not None else math.inf
        extent=np.maximum(np.abs(low),np.abs(high))
        def passes(h):
            t=h/1e6+profile.clock
            inflate=margin+profile.r_max+body.travel(t,effective)
            return bool(np.all(extent+inflate<profile.domain) and nearest>inflate+q)
        lo,hi=0,cap_us+1
        while hi-lo>1:
            mid=(lo+hi)//2
            if passes(mid):lo=mid
            else:hi=mid
        assert not lo or passes(lo)
        assert lo==cap_us or not passes(lo+1)
        classes[n]=dict(horizon_us=lo,cap_limited=lo==cap_us,reference_speed=effective.speed,
                        nearest_unexcluded_distance_m=nearest if math.isfinite(nearest) else None,
                        nearest_unexcluded_cell=unknown[j].tolist() if j is not None else None)
    return dict(horizon_us=min(x['horizon_us'] for x in classes.values()),classes=classes,
                raw_reference_us=p['reference_us'],scope='Maximum of fixed-K corrected tile condition, not physical safe horizon or free online oracle.')


def check(receiver,anchor_id,raw,horizon_us):
    if horizon_us<1:return False
    anchor=receiver._anchors[anchor_id]
    p,o,r=body.decode(body.canonical(raw),receiver.profiles,anchor.scope,receiver.contract)
    v=body.projections(o,r,p['reference_us'],receiver.profiles,anchor.scope,receiver.contract)
    cells={n:base.collar(profile,anchor,horizon_us/1e6,r,p['reference_us']) for n,profile in receiver.profiles.items()}
    return stream.cover(v,receiver.profiles,anchor.motion,cells,len(r))
