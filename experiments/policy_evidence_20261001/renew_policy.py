"""Reuse support locations only; every certificate contains current raw rays."""
from functools import lru_cache
import json
import numpy as np
from scipy.spatial import cKDTree
import policy_proof as pp
from proof import QUANTUM
from strict_policy import verify


@lru_cache(maxsize=32)
def support(template,profiles,contract):
    packet=json.loads(template);p=packet['raw']['payload'];s=p['scope']
    scope=pp.Scope(s['episode'],s['frame_id'],tuple(s['query']),s['plane_z'])
    p,o,r=pp.decode(pp.canonical(packet['raw']),dict(profiles),scope,contract)
    res=pp.projections(o,r,p['reference_us'],dict(profiles),scope,contract)
    return next(iter(res.values()))['witnesses']@pp.rotation(packet['yaw'])


def renew(template,points,origin,observed,reference,profiles,scope,contract,policy,speed,yaw,horizon,sequence,fast=True):
    try:
        previous=json.loads(template)
        if pp.canonical(previous['policy'])!=pp.canonical(pp.asdict(policy)) or previous['speed']!=speed:return None
        w=support(template,tuple(profiles.items()),contract)
        o,r,ref=pp.encode_source(points,origin,observed,reference)
        if fast:
            origins=o[r[:,0]]*QUANTUM;end=r[:,1:4]*QUANTUM
            valid=(origins[:,2]-contract.origin_error-QUANTUM/2>scope.plane_z+1e-9)&(end[:,2]+contract.point_error+QUANTUM/2<scope.plane_z-1e-9)
            ids=np.flatnonzero(valid);origins=origins[valid];end=end[valid]
            t=(origins[:,2]-scope.plane_z)/(origins[:,2]-end[:,2])
            current=((1-t[:,None])*origins[:,:2]+t[:,None]*end[:,:2]-scope.query)@pp.rotation(yaw)
        else:
            res=pp.projections(o,r,ref,profiles,scope,contract);first=next(iter(res.values()))
            ids=first['ray_indices'];current=first['witnesses']@pp.rotation(yaw)
        if not len(current) or not len(w):return None
        chosen=np.unique(ids[cKDTree(current).query(w,k=1)[1]])
        if not len(chosen) or len(chosen)>pp.MAX_RAYS:return None
        raw=json.loads(pp.serialize(o,r[chosen],ref,profiles,scope,contract,horizon,sequence))
        blob=pp.canonical(dict(kind='policy-evidence-v1',policy=pp.asdict(policy),speed=speed,yaw=yaw,raw=raw))
        return blob if verify(blob,profiles,scope,contract,policy,speed,yaw,float(np.nextafter(ref/pp.TIME_SCALE,np.inf))) else None
    except (ValueError,TypeError,KeyError,IndexError,OverflowError):return None
