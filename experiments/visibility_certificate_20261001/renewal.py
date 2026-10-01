"""Refresh proof support using CURRENT rays; old witnesses cannot renew time."""
from dataclasses import asdict
import hashlib,json,math
import numpy as np
from scipy.spatial import cKDTree
from geometry import covers_horizon
from proof_packet import QUANTUM,QUANT_ERROR,canonical,verify


def renew(template,current_witnesses,profile,scope,produced_at):
    if not math.isfinite(produced_at):return None
    try:
        old=json.loads(template);body=old['payload']
        if hashlib.sha256(canonical(body)).hexdigest()!=old['sha256']:return None
        if body['profile']!=asdict(profile) or body['quantum']!=QUANTUM:return None
        target=body['target_s'];support=np.asarray(body['witnesses'],dtype=float)*QUANTUM
        current=np.asarray(current_witnesses,dtype=float).reshape(-1,2)
        if not len(current) or not np.isfinite(current).all():return None
        # Template points are query positions only, never treated as new evidence.
        indices=cKDTree(current).query(support,k=1)[1]
        quant=np.unique(np.rint(current[indices]/QUANTUM).astype(np.int64),axis=0)
        if not covers_horizon(quant*QUANTUM,profile,target,QUANT_ERROR):return None
        payload=dict(version=1,scope=scope,profile=asdict(profile),produced_at=produced_at,
                     target_s=target,quantum=QUANTUM,witnesses=quant.tolist())
        return canonical(dict(payload=payload,sha256=hashlib.sha256(canonical(payload)).hexdigest()))
    except (ValueError,TypeError,KeyError,OverflowError):return None


def verify_all(blobs,profiles,scopes,now,execution_s):
    """Every receiver-required obstacle class must be certified, not just cars."""
    if not profiles or set(blobs)!=set(profiles) or set(scopes)!=set(profiles):return False
    return all(verify(blobs[k],p,scopes[k],now,execution_s) for k,p in profiles.items())
