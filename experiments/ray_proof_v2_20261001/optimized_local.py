"""Exact support lookup with bounded local search; full receiver check retained."""
import math
import numpy as np
from scipy.spatial import cKDTree
from optimized import encode_source,_template
from proof import QUANTUM,TIME_SCALE,projections,uniform_errors,serialize,verify


def renew(template,points,origins,observed_at,reference_at,profiles,scope,contract,sequence,mode='heterogeneous'):
    try:
        if mode not in ['heterogeneous','uniform'] or type(sequence) is not int:return None
        p,support=_template(template,tuple(profiles.items()),scope,contract)
        if sequence<=p['sequence'] or reference_at<=p['reference_us']/TIME_SCALE:return None
        oq,r,ref=encode_source(points,origins,observed_at,reference_at)
        ages=(ref-r[:,4])/TIME_SCALE
        if np.any(ages<0) or np.any(ages>contract.max_ray_age):return None
        o=oq[r[:,0]]*QUANTUM;end=r[:,1:4]*QUANTUM
        oe=contract.origin_error+QUANTUM/2;pe=contract.point_error+QUANTUM/2
        valid=(o[:,2]-oe>scope.plane_z+1e-9)&(end[:,2]+pe<scope.plane_z-1e-9)
        ids=np.flatnonzero(valid);o=o[valid];end=end[valid]
        if not len(ids) or not len(support):return None
        # Same nominal formula and eligibility as bounded_witnesses. Full
        # uncertainty is needed only for the ultimately selected raw rays.
        t=(o[:,2]-scope.plane_z)/(o[:,2]-end[:,2])
        w=(1-t[:,None])*o[:,:2]+t[:,None]*end[:,:2]-scope.query
        margin=.25;low=np.min(support,axis=0)-margin;high=np.max(support,axis=0)+margin
        local=np.flatnonzero(np.all((w>=low)&(w<=high),axis=1))
        use_local=False
        if len(local)>=2:
            d,j=cKDTree(w[local]).query(support,k=2)
            # An excluded point cannot be closer than margin to any support.
            # Ties fall back to the same full-tree lookup as the reference.
            use_local=bool(np.all(d[:,0]<margin-1e-9) and np.all(d[:,1]-d[:,0]>1e-12))
        if use_local:chosen=local[j[:,0]]
        else:chosen=cKDTree(w).query(support,k=1)[1]
        selected=r[np.unique(ids[chosen])];horizon=p['horizon_us']/TIME_SCALE
        if mode=='uniform':
            actual=projections(oq,selected,ref,profiles,scope,contract)
            if any(uniform_errors(actual[n],profile,horizon) is None for n,profile in profiles.items()):return None
        blob=serialize(oq,selected,ref,profiles,scope,contract,horizon,sequence)
        return blob if verify(blob,profiles,scope,contract,ref/TIME_SCALE,0) else None
    except (ValueError,TypeError,KeyError,OverflowError,IndexError):return None
