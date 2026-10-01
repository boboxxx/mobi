"""Bounded current-ray proposal repair; only the full verifier grants geometry.

Four then sixteen nominal nearest candidates per uncovered center are proposals,
not free-space assertions. Failure after both rounds returns None. No error,
region, horizon or ray limit is relaxed. This is a post-analysis diagnostic;
fresh closed-loop evaluation has not yet run.
"""
import json,numpy as np
from scipy.spatial import cKDTree
from fast_path import body,nearest,QUANTUM
from renew import support
from diagnose_transition import missing_cells


def renew(template,points,origin,observed,reference,profiles,scope,contract,motion,prior,horizon=.4,sequence=0):
    if horizon!=.4:raise ValueError('Diagnostic has a fixed 400 ms horizon')
    try:
        w=support(template,tuple(profiles.items()),contract);o,r,ref=body.encode_source(points,origin,observed,reference)
        origins=o[r[:,0]]*QUANTUM;end=r[:,1:4]*QUANTUM
        valid=(origins[:,2]-contract.origin_error-QUANTUM/2>scope.plane_z+1e-9)&(end[:,2]+contract.point_error+QUANTUM/2<scope.plane_z-1e-9)
        ids=np.flatnonzero(valid);origins=origins[valid];end=end[valid]
        t=(origins[:,2]-scope.plane_z)/(origins[:,2]-end[:,2]);current=((1-t[:,None])*origins[:,:2]+t[:,None]*end[:,:2]-scope.query)@body.rotation(motion.yaw)
        if not len(current) or not len(w):return None
        j,_=nearest(current,w);chosen=np.unique(ids[j]);tree=None
        for k in [0,4,16]:
            if k:
                results=body.projections(o,r[chosen],ref,profiles,scope,contract)
                gaps=[missing_cells(results[n],pr,scope,motion,prior,ref/body.TIME_SCALE) for n,pr in profiles.items()];gaps=np.concatenate(gaps)
                if len(gaps):
                    if tree is None:tree=cKDTree(current)
                    _,j=tree.query(gaps,k=min(k,len(current)));chosen=np.unique(np.concatenate([chosen,ids[np.asarray(j).reshape(-1)]]))
            if not len(chosen) or len(chosen)>body.MAX_RAYS:return None
            raw=json.loads(body.serialize(o,r[chosen],ref,profiles,scope,contract,horizon,sequence));blob=body.canonical(dict(kind='body-evidence-v1',motion=body.asdict(motion),prior=prior.identity if prior else None,raw=raw))
            if body.verify(blob,profiles,scope,contract,motion,prior,ref/body.TIME_SCALE,0):return blob
        return None
    except (ValueError,TypeError,KeyError,OverflowError,IndexError):return None
