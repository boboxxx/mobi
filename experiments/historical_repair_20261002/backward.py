"""Backward demand for additional, genuinely historical ray evidence."""
import math,sys
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'class_guard_20261002'))
import guard
body=guard.body;stream=guard.stream

def missing_cells(v,g,motion,cells):return guard.missing(v,g,motion,cells)

def predecessors(cells,g,distance):
    """Conservative whole-tile preimage, with explicit unknown-exterior refusal."""
    size=round(2*g.domain/g.step);out=np.zeros((size,size),dtype=bool)
    if not len(cells):return out
    if g.domain-np.max(np.abs(cells))-g.step/2<=distance+1e-9:return None
    axis=-g.domain+g.step/2;ix=np.rint((cells-axis)/g.step).astype(int)
    out[ix[:,0],ix[:,1]]=True;v=np.zeros((size+1,size+1),dtype=bool)
    v[:-1,:-1]|=out;v[1:,:-1]|=out;v[:-1,1:]|=out;v[1:,1:]|=out
    d=distance_transform_edt(~v,sampling=g.step)
    return np.minimum(np.minimum(d[:-1,:-1],d[1:,:-1]),np.minimum(d[:-1,1:],d[1:,1:]))<=distance+1e-9

def demand(previous,current,budgets,profiles,contract,scope,motion,horizon_us=475000):
    """Inputs are already received raw facts, never a future frame."""
    p0,o0,r0=body.decode(body.canonical(previous),profiles,scope,contract);p,o,r=body.decode(body.canonical(current),profiles,scope,contract)
    if p['reference_us']<=p0['reference_us']:raise ValueError('Historical order')
    v0=body.projections(o0,r0,p0['reference_us'],profiles,scope,contract);v=body.projections(o,r,p['reference_us'],profiles,scope,contract);needed={};distances={};missing={}
    for n,g in profiles.items():
        e0=stream.base.reference_speed(g,r0,p0['reference_us']);e=stream.base.reference_speed(g,r,p['reference_us']);distance=guard.flow.terminal_distance(e0.speed,e.speed,g.acceleration,(p['reference_us']-p0['reference_us'])/1e6);distances[n]=distance
        cells=body.required(e,motion,horizon_us/1e6)
        if cells is None:return None,dict(reason='Current domain',klass=n)
        low,high,margin=body.envelope(motion,0.,g.clock);q=g.step/math.sqrt(2);radius=float(np.nextafter(g.r_max+budgets[n]-distance,-math.inf));known=(body.box_distance(cells,low,high)+q<margin+radius-1e-9) if radius>=0 else np.zeros(len(cells),dtype=bool)
        unresolved=missing_cells(v[n],g,motion,cells[~known]);missing[n]=unresolved
        pred=predecessors(unresolved,g,distance)
        if pred is None:return None,dict(reason='Unknown historical exterior',klass=n)
        allcells=body.grid(g.domain,g.step)[0];candidate=allcells[pred.ravel()];oldknown=body.box_distance(candidate,low,high)+q<margin+g.r_max+budgets[n]-1e-9
        needed[n]=missing_cells(v0[n],g,motion,candidate[~oldknown])
    return needed,dict(reason=None,past_distances=distances,unresolved_current={n:len(x) for n,x in missing.items()},needed_old={n:len(x) for n,x in needed.items()})

def select(points,origin,stamp,reference_us,profiles,contract,scope,motion,needed,sequence):
    active={n:g for n,g in profiles.items() if len(needed[n])}
    if not active:return None,dict(reason='No additional evidence required')
    o,r,ref=body.encode_source(points,origin,stamp,stamp)
    if ref!=reference_us:raise ValueError('Historical reference mismatch')
    v=stream.base.shared_projections(o,r,ref,active,scope,contract);ids=stream.cover(v,active,motion,needed,len(r),True)
    if ids is None:return None,dict(reason='Historical scan does not cover demand')
    if not 0<len(ids)<=body.MAX_RAYS:return None,dict(reason='Bounded ray count')
    import json
    return json.loads(body.serialize(o,r[ids],ref,profiles,scope,contract,.475,sequence)),dict(reason=None,rays=len(ids))
