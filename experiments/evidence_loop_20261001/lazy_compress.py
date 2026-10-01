"""Exact lazy greedy: same maximum uncovered gain, same smallest-ID tie break."""
import heapq,json
import numpy as np
from scipy.spatial import cKDTree
from fast_path import body


def choose(neighborhoods,total,limit):
    neighbors={i:np.asarray(v,dtype=np.int64) for i,v in neighborhoods.items()}
    heap=[(-len(v),i) for i,v in neighbors.items() if len(v)];heapq.heapify(heap)
    missing=np.ones(total,dtype=bool);remaining=total;selected=[]
    while remaining:
        if not heap:return None
        _,i=heapq.heappop(heap);gain=int(missing[neighbors[i]].sum())
        if heap and (-gain,i)>heap[0]:heapq.heappush(heap,(-gain,i));continue
        if gain==0 or len(selected)>=limit:return None
        selected.append(i);missing[neighbors[i]]=False;remaining-=gain
    return selected


def pack(points,origin,observed,reference,profiles,scope,contract,motion,prior,horizon=.4,sequence=0):
    if len({p.clock for p in profiles.values()})!=1:raise ValueError('Classes need identical clock contract')
    o,r,ref=body.encode_source(points,origin,observed,reference);stamp=ref/body.TIME_SCALE
    results=body.projections(o,r,ref,profiles,scope,contract);candidates=set()
    for n,pr in profiles.items():
        ok,ids=body.coverage(results[n],pr,scope,motion,horizon,prior,stamp,True)
        if not ok:return None
        candidates.update(ids)
    neighborhoods={i:[] for i in candidates};offset=0
    for n,pr in profiles.items():
        cells=body.required(pr,motion,horizon);cells=cells[~body.prior_covers(cells,scope,motion,prior,pr,stamp)]
        if not len(cells):continue
        result=results[n];mask=np.isin(result['ray_indices'],list(candidates));ids=result['ray_indices'][mask];w=result['witnesses'][mask]@body.rotation(motion.yaw)
        radius=pr.r_min-result['error'][mask]-pr.step/np.sqrt(2)-1e-9;use=radius>0
        found=cKDTree(cells).query_ball_point(w[use],radius[use])
        for ray,near in zip(ids[use],found):neighborhoods[int(ray)].extend(offset+j for j in near)
        offset+=len(cells)
    selected=choose(neighborhoods,offset,body.MAX_RAYS)
    if selected is None:return None
    if not selected:
        if not len(r):return None
        selected=[0]
    raw=json.loads(body.serialize(o,r[selected],ref,profiles,scope,contract,horizon,sequence))
    blob=body.canonical(dict(kind='body-evidence-v1',motion=body.asdict(motion),prior=prior.identity if prior else None,raw=raw))
    return blob if body.verify(blob,profiles,scope,contract,motion,prior,stamp,0) else None
