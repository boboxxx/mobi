"""Semantics-preserving renewal: shared-pose encoding and one support lookup."""
from functools import lru_cache
import math
import numpy as np
from scipy.spatial import cKDTree
from proof import (QUANTUM,TIME_SCALE,encode_source as reference_encode,decode,
                   projections,serialize,verify,uniform_errors)


def encode_source(points,origins,observed_at,reference_at):
    p=np.asarray(points,dtype=float);o=np.asarray(origins,dtype=float)
    if o.shape!=(3,):return reference_encode(points,origins,observed_at,reference_at)
    t=np.broadcast_to(np.asarray(observed_at,dtype=float),(len(p),))
    if p.ndim!=2 or p.shape[1]!=3 or not np.isfinite(p).all() or not np.isfinite(o).all() or not np.isfinite(t).all() or not math.isfinite(reference_at):
        raise ValueError('Invalid raw rays')
    if np.any(t>reference_at) or max(np.max(np.abs(p),initial=0),np.max(np.abs(o),initial=0))>1e6 or np.max(np.abs(t),initial=0)>1e9 or abs(reference_at)>1e9:
        raise ValueError('Unsupported coordinates/times or future rays')
    origins_q=np.rint(o/QUANTUM).astype(np.int64).reshape(1,3)
    rays=np.column_stack([np.zeros(len(p),dtype=np.int64),np.rint(p/QUANTUM).astype(np.int64),np.floor(t*TIME_SCALE).astype(np.int64)])
    return origins_q,rays,int(math.ceil(reference_at*TIME_SCALE))


@lru_cache(maxsize=32)
def _template(blob,profile_items,scope,contract):
    profiles=dict(profile_items);p,o,r=decode(blob,profiles,scope,contract)
    # Crossing eligibility and nominal positions do not depend on object class.
    first=next(iter(profiles));old=projections(o,r,p['reference_us'],{first:profiles[first]},scope,contract)[first]
    return p,old['witnesses']


def renew(template,points,origins,observed_at,reference_at,profiles,scope,contract,sequence,mode='heterogeneous'):
    try:
        if mode not in ['heterogeneous','uniform'] or type(sequence) is not int:return None
        p,support=_template(template,tuple(profiles.items()),scope,contract)
        if sequence<=p['sequence'] or reference_at<=p['reference_us']/TIME_SCALE:return None
        o,r,ref=encode_source(points,origins,observed_at,reference_at)
        first=next(iter(profiles));current=projections(o,r,ref,{first:profiles[first]},scope,contract)[first]
        if not len(current['witnesses']):return None
        idx=cKDTree(current['witnesses']).query(support,k=1)[1]
        selected=r[np.unique(current['ray_indices'][idx])];horizon=p['horizon_us']/TIME_SCALE
        if mode=='uniform':
            actual=projections(o,selected,ref,profiles,scope,contract)
            if any(uniform_errors(actual[n],profile,horizon) is None for n,profile in profiles.items()):return None
        blob=serialize(o,selected,ref,profiles,scope,contract,horizon,sequence)
        return blob if verify(blob,profiles,scope,contract,ref/TIME_SCALE,0) else None
    except (ValueError,TypeError,KeyError,OverflowError,IndexError):return None
