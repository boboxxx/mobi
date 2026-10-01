"""Build an UNVERIFIED current-ray proposal; receiver proof checking is mandatory."""
import json
import numpy as np
from scipy.spatial import cKDTree
from incremental import pp
from binary_proof import encode,BinaryVerifier
from renew_policy import support
from proof import QUANTUM


def nearest(current,supports,margin=.25):
    low=np.min(supports,axis=0)-margin;high=np.max(supports,axis=0)+margin
    local=np.flatnonzero(np.all((current>=low)&(current<=high),axis=1))
    if len(local)>=2:
        distance,j=cKDTree(current[local]).query(supports,k=2)
        # Excluded points are >= margin from every support. Ties use the
        # reference full tree, including duplicate current rays.
        if np.all(distance[:,0]<margin-1e-9) and np.all(distance[:,1]-distance[:,0]>1e-12):return local[j[:,0]],True
    return cKDTree(current).query(supports,k=1)[1],False


class ProposalBuilder:
    def __init__(self,local=True,incremental=True):
        self.local=local;self.incremental=incremental;self.local_hits=0;self.fallbacks=0

    def renew(self,template,points,origin,observed,reference,profiles,scope,contract,policy,speed,yaw,horizon,sequence):
        try:
            previous=json.loads(template)
            if pp.canonical(previous['policy'])!=pp.canonical(pp.asdict(policy)) or previous['speed']!=speed:return None
            w=support(template,tuple(profiles.items()),contract)
            o,r,ref=pp.encode_source(points,origin,observed,reference)
            origins=o[r[:,0]]*QUANTUM;end=r[:,1:4]*QUANTUM
            valid=(origins[:,2]-contract.origin_error-QUANTUM/2>scope.plane_z+1e-9)&(end[:,2]+contract.point_error+QUANTUM/2<scope.plane_z-1e-9)
            ids=np.flatnonzero(valid);origins=origins[valid];end=end[valid]
            t=(origins[:,2]-scope.plane_z)/(origins[:,2]-end[:,2])
            current=((1-t[:,None])*origins[:,:2]+t[:,None]*end[:,:2]-scope.query)@pp.rotation(yaw)
            if not len(current) or not len(w):return None
            if self.local:
                j,local=nearest(current,w);self.local_hits+=int(local);self.fallbacks+=int(not local)
            else:j=cKDTree(current).query(w,k=1)[1]
            chosen=np.unique(ids[j])
            if not len(chosen) or len(chosen)>pp.MAX_RAYS:return None
            blob=encode(o,r[chosen],ref,profiles,scope,contract,policy,speed,yaw,horizon,sequence)
            return blob  # Unverified candidate; the receiving verifier decides.
        except (ValueError,TypeError,KeyError,IndexError,OverflowError):return None
