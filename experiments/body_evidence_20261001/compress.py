"""Coverage-preserving greedy reduction of full-body raw-ray candidates."""
import heapq,json
import numpy as np
from scipy.spatial import cKDTree
from body import *


def pack(points,origin,observed,reference,profiles,scope,contract,motion,prior,horizon=.4,sequence=0):
    if len({p.clock for p in profiles.values()})!=1:raise ValueError('Classes need identical clock contract')
    o,r,ref=encode_source(points,origin,observed,reference);stamp=ref/TIME_SCALE
    results=projections(o,r,ref,profiles,scope,contract);candidates=set()
    for n,pr in profiles.items():
        ok,ids=coverage(results[n],pr,scope,motion,horizon,prior,stamp,True)
        if not ok:return None
        candidates.update(ids)
    neighborhoods={i:[] for i in candidates};offset=0
    for n,pr in profiles.items():
        cells=required(pr,motion,horizon)
        cells=cells[~prior_covers(cells,scope,motion,prior,pr,stamp)]
        if not len(cells):continue
        result=results[n];mask=np.isin(result['ray_indices'],list(candidates))
        ids=result['ray_indices'][mask];w=result['witnesses'][mask]@rotation(motion.yaw)
        radius=pr.r_min-result['error'][mask]-pr.step/math.sqrt(2)-1e-9;use=radius>0
        found=cKDTree(cells).query_ball_point(w[use],radius[use])
        for ray,near in zip(ids[use],found):neighborhoods[int(ray)].extend(offset+j for j in near)
        offset+=len(cells)
    inverted=[[] for _ in range(offset)]
    for i,cells in neighborhoods.items():
        for cell in cells:inverted[cell].append(i)
    if any(not x for x in inverted):raise RuntimeError('Candidate selection lost coverage')
    gains={i:len(c) for i,c in neighborhoods.items()};heap=[(-g,i) for i,g in gains.items() if g];heapq.heapify(heap)
    missing=np.ones(offset,dtype=bool);selected=[];remaining=offset
    while remaining:
        while heap:
            ng,i=heapq.heappop(heap)
            if -ng==gains[i]:break
        else:raise RuntimeError('Greedy failed complete cover')
        if not gains[i] or len(selected)>=MAX_RAYS:return None
        selected.append(i);changed=set()
        for cell in neighborhoods[i]:
            if not missing[cell]:continue
            missing[cell]=False;remaining-=1
            for other in inverted[cell]:gains[other]-=1;changed.add(other)
        for other in changed:
            if gains[other]>0:heapq.heappush(heap,(-gains[other],other))
    if not selected:
        if not len(r):return None
        selected=[0]
    raw=json.loads(serialize(o,r[selected],ref,profiles,scope,contract,horizon,sequence))
    blob=canonical(dict(kind='body-evidence-v1',motion=asdict(motion),prior=prior.identity if prior else None,raw=raw))
    return blob if verify(blob,profiles,scope,contract,motion,prior,stamp,0) else None
