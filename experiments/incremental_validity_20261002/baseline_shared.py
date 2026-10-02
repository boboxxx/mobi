"""Same current-ray repair proposal with one coverage pass per candidate.

The sender computes typed geometry once; the receiver still decodes the whole
packet and recomputes all geometry. No sender assertion replaces receiver work.
"""
import json,math,sys
from pathlib import Path
import numpy as np
from projection_once import projections
from scipy.spatial import cKDTree
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'evidence_loop_20261001'))
from fast_path import body,nearest,QUANTUM
from renew import support as _old_support


def support(template,profiles,contract):
    # Import was resolved while body_evidence was on sys.path. Cache semantics
    # are the established implementation; keep exactly the same support points.
    return _old_support(template,tuple(profiles.items()),contract)


def missing_cells(result,profile,scope,motion,prior,reference,horizon):
    cells=body.required(profile,motion,horizon)
    if cells is None:return None
    missing=~body.prior_covers(cells,scope,motion,prior,profile,reference)
    witnesses=result['witnesses']@body.rotation(motion.yaw)
    for error in np.unique(result['error']):
        radius=profile.r_min-error-profile.step/math.sqrt(2)-1e-9
        if radius<=0:continue
        todo=np.flatnonzero(missing)
        if not len(todo):break
        group=np.flatnonzero(result['error']==error)
        distances=cKDTree(witnesses[group]).query(cells[todo],k=1)[0]
        missing[todo[distances<radius]]=False
    return cells[missing]


def propose(template,points,origin,observed,reference,profiles,scope,contract,motion):
    w=support(template,profiles,contract);o,r,ref=body.encode_source(points,origin,observed,reference)
    origins=o[r[:,0]]*QUANTUM;end=r[:,1:4]*QUANTUM
    valid=(origins[:,2]-contract.origin_error-QUANTUM/2>scope.plane_z+1e-9)&(end[:,2]+contract.point_error+QUANTUM/2<scope.plane_z-1e-9)
    ids=np.flatnonzero(valid);origins=origins[valid];end=end[valid]
    t=(origins[:,2]-scope.plane_z)/(origins[:,2]-end[:,2])
    current=((1-t[:,None])*origins[:,:2]+t[:,None]*end[:,:2]-scope.query)@body.rotation(motion.yaw)
    if not len(current) or not len(w):return None
    j,_=nearest(current,w)
    return o,r,ref,ids,current,np.unique(ids[j])


def packet(o,r,ref,profiles,scope,contract,motion,prior,horizon,sequence):
    raw=json.loads(body.serialize(o,r,ref,profiles,scope,contract,horizon,sequence))
    return body.canonical(dict(kind='body-evidence-v1',motion=body.asdict(motion),prior=prior.identity if prior else None,raw=raw))


def repair(template,points,origin,observed,reference,profiles,scope,contract,motion,prior,horizon=.4,sequence=0):
    try:
        if type(sequence) is not int or sequence<0 or not math.isfinite(horizon) or math.floor(horizon*body.TIME_SCALE)<=0:return None
        if len({p.clock for p in profiles.values()})!=1 or any(p.error!=0 for p in profiles.values()):return None
        proposal=propose(template,points,origin,observed,reference,profiles,scope,contract,motion)
        if proposal is None:return None
        o,r,ref,ids,current,chosen=proposal;tree=None
        for k in [0,4,16]:
            if k:
                if tree is None:tree=cKDTree(current)
                _,j=tree.query(gaps,k=min(k,len(current)))
                chosen=np.unique(np.concatenate([chosen,ids[np.asarray(j).reshape(-1)]]))
            if not len(chosen) or len(chosen)>body.MAX_RAYS:return None
            results=projections(o,r[chosen],ref,profiles,scope,contract)
            gaps_by_class=[missing_cells(results[n],p,scope,motion,prior,ref/body.TIME_SCALE,horizon) for n,p in profiles.items()]
            if any(g is None for g in gaps_by_class):return None
            gaps=np.concatenate(gaps_by_class)
            if not len(gaps):return packet(o,r[chosen],ref,profiles,scope,contract,motion,prior,horizon,sequence)
        return None
    except (ValueError,TypeError,KeyError,OverflowError,IndexError):return None


def reference_repair(template,points,origin,observed,reference,profiles,scope,contract,motion,prior,horizon=.4,sequence=0):
    """Frozen repair algorithm generalized ONLY from 400 ms to an input horizon."""
    try:
        proposal=propose(template,points,origin,observed,reference,profiles,scope,contract,motion)
        if proposal is None:return None
        o,r,ref,ids,current,chosen=proposal;tree=None
        for k in [0,4,16]:
            if k:
                results=projections(o,r[chosen],ref,profiles,scope,contract)
                gaps=[missing_cells(results[n],p,scope,motion,prior,ref/body.TIME_SCALE,horizon) for n,p in profiles.items()]
                if any(g is None for g in gaps):return None
                gaps=np.concatenate(gaps)
                if len(gaps):
                    if tree is None:tree=cKDTree(current)
                    _,j=tree.query(gaps,k=min(k,len(current)))
                    chosen=np.unique(np.concatenate([chosen,ids[np.asarray(j).reshape(-1)]]))
            if not len(chosen) or len(chosen)>body.MAX_RAYS:return None
            blob=packet(o,r[chosen],ref,profiles,scope,contract,motion,prior,horizon,sequence)
            if body.verify(blob,profiles,scope,contract,motion,prior,ref/body.TIME_SCALE,0):return blob
        return None
    except (ValueError,TypeError,KeyError,OverflowError,IndexError):return None
