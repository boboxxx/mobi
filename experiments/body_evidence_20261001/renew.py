"""Fresh raw-ray support renewal for a translated/rotated body query."""
from functools import lru_cache
import json
import numpy as np
from scipy.spatial import cKDTree
from body import *


@lru_cache(maxsize=32)
def support(template,profiles,contract):
    packet=json.loads(template);p=packet['raw']['payload']
    s=p['scope'];scope=Scope(s['episode'],s['frame_id'],tuple(s['query']),s['plane_z'])
    motion=Motion(**packet['motion']);profiles=dict(profiles)
    p,o,r=decode(canonical(packet['raw']),profiles,scope,contract)
    result=projections(o,r,p['reference_us'],profiles,scope,contract)
    w=next(iter(result.values()))['witnesses']@rotation(motion.yaw)
    return w


def renew(template,points,origin,observed,reference,profiles,scope,contract,motion,prior,horizon=.4,sequence=0):
    try:
        w=support(template,tuple(profiles.items()),contract)
        if not len(w):return None
        o,r,ref=encode_source(points,origin,observed,reference)
        result=projections(o,r,ref,profiles,scope,contract)
        first=next(iter(result.values()));current=first['witnesses']@rotation(motion.yaw)
        if not len(current):return None
        nearest=cKDTree(current).query(w,k=1)[1]
        chosen=np.unique(first['ray_indices'][nearest])
        if not len(chosen) or len(chosen)>MAX_RAYS:return None
        raw=json.loads(serialize(o,r[chosen],ref,profiles,scope,contract,horizon,sequence))
        blob=canonical(dict(kind='body-evidence-v1',motion=asdict(motion),prior=prior.identity if prior else None,raw=raw))
        return blob if verify(blob,profiles,scope,contract,motion,prior,ref/TIME_SCALE,0) else None
    except (ValueError,TypeError,KeyError,OverflowError,IndexError):return None
