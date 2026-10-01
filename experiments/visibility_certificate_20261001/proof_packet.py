"""Greedy witness proof compression and receiver re-verification.

SHA-256 checks transport corruption, not sender authenticity or honest sensing.
The receiver fixes the physical profile; packet data cannot weaken its bounds.
"""
from dataclasses import asdict
import hashlib
import heapq
import json
import math
import numpy as np
from scipy.spatial import cKDTree
from geometry import grid,travel,covers_horizon

QUANTUM=.01
QUANT_ERROR=QUANTUM/math.sqrt(2)


def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def pack(witnesses,profile,scope,produced_at,target_s):
    if not math.isfinite(produced_at) or not math.isfinite(target_s) or target_s<=0:raise ValueError('Invalid time')
    w=np.asarray(witnesses,dtype=float).reshape(-1,2)
    quant=np.unique(np.rint(w/QUANTUM).astype(np.int64),axis=0);w=quant*QUANTUM
    centers,dist=grid(profile.domain,profile.step)
    needed_radius=profile.query_radius+profile.r_max+travel(target_s+profile.clock,profile)
    if needed_radius>=profile.domain:return None
    required=centers[dist<=needed_radius]
    radius=profile.r_min-profile.error-QUANT_ERROR-profile.step/math.sqrt(2)
    if radius<=0 or not len(w):return None
    neighborhoods=cKDTree(required).query_ball_point(w,radius-1e-10)
    inverted=[[] for _ in required]
    for i,cells in enumerate(neighborhoods):
        for cell in cells:inverted[cell].append(i)
    if any(not x for x in inverted):return None
    gains=[len(x) for x in neighborhoods];heap=[(-g,i) for i,g in enumerate(gains) if g];heapq.heapify(heap)
    uncovered=np.ones(len(required),dtype=bool);selected=[]
    while uncovered.any():
        while heap:
            ng,i=heapq.heappop(heap)
            if -ng==gains[i]:break
        else:return None
        if gains[i]==0:return None
        selected.append(i);changed=set()
        for cell in neighborhoods[i]:
            if not uncovered[cell]:continue
            uncovered[cell]=False
            for other in inverted[cell]:gains[other]-=1;changed.add(other)
        for other in changed:
            if gains[other]:heapq.heappush(heap,(-gains[other],other))
    payload=dict(version=1,scope=scope,profile=asdict(profile),produced_at=produced_at,target_s=target_s,
                 quantum=QUANTUM,witnesses=quant[selected].tolist())
    # Always verify the compressed proof instead of trusting the cover solver.
    if not covers_horizon(w[selected],profile,target_s,QUANT_ERROR):return None
    body=canonical(payload)
    return canonical(dict(payload=payload,sha256=hashlib.sha256(body).hexdigest()))


def verify(blob,profile,scope,now,execution_s):
    try:
        if not math.isfinite(now) or not math.isfinite(execution_s) or execution_s<0:return False
        envelope=json.loads(blob);payload=envelope['payload']
        if hashlib.sha256(canonical(payload)).hexdigest()!=envelope['sha256']:return False
        if payload['version']!=1 or payload['quantum']!=QUANTUM:return False
        if payload['scope']!=scope or payload['profile']!=asdict(profile):return False
        stamp=payload['produced_at'];target=payload['target_s']
        if not math.isfinite(stamp) or not math.isfinite(target) or stamp>now or target<=0:return False
        w=np.asarray(payload['witnesses'],dtype=float)*QUANTUM
        if not covers_horizon(w,profile,target,QUANT_ERROR):return False
        return now+execution_s < stamp+target
    except (ValueError,TypeError,KeyError,OverflowError):return False
