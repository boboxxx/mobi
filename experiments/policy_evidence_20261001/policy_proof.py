"""No-history raw-ray certificate for a specified hold/go/brake maneuver.

Conditional geometry only. A receiver must independently establish actuation,
sensor and opaque-core contracts before using this certificate for movement.
The packet cannot establish these physical contracts by asserting a Boolean.
"""
from pathlib import Path
from functools import lru_cache
from dataclasses import asdict
from fractions import Fraction
import heapq,json,math,sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'body_evidence_20261001'))
from body import Profile,Scope,Contract,canonical,decode,serialize,projections,encode_source,TIME_SCALE,MAX_RAYS,grid,travel,rotation,box_distance
from tube import Policy,envelope,stop_duration


@lru_cache(maxsize=128)
def required(profile,policy,speed,horizon):
    lo,hi,margin=envelope(speed,horizon,profile.clock,policy)
    inflate=margin+profile.r_max+travel(horizon+profile.clock,profile)
    if np.any(np.maximum(np.abs(lo),np.abs(hi))+inflate>=profile.domain):return None
    cells,_=grid(profile.domain,profile.step)
    return cells[box_distance(cells,lo,hi)<=inflate+profile.step/math.sqrt(2)]


def coverage(result,profile,policy,speed,yaw,horizon,select=False):
    cells=required(profile,policy,speed,horizon)
    if cells is None:return False,[]
    missing=np.ones(len(cells),dtype=bool);chosen=[]
    w=result['witnesses']@rotation(yaw)
    for error in np.unique(result['error']):
        radius=profile.r_min-error-profile.step/math.sqrt(2)-1e-9
        if radius<=0:continue
        todo=np.flatnonzero(missing)
        if not len(todo):break
        group=np.flatnonzero(result['error']==error)
        d,j=cKDTree(w[group]).query(cells[todo],k=1)
        hit=d<radius;missing[todo[hit]]=False
        if select:chosen.extend(result['ray_indices'][group[j[hit]]].tolist())
    return not missing.any(),chosen


def pack(points,origin,observed,reference,profiles,scope,contract,policy,speed,yaw,horizon,sequence=0):
    if len({p.clock for p in profiles.values()})!=1:raise ValueError('Unequal class clocks')
    o,r,ref=encode_source(points,origin,observed,reference)
    result=projections(o,r,ref,profiles,scope,contract);candidates=set()
    for name,pr in profiles.items():
        ok,ids=coverage(result[name],pr,policy,speed,yaw,horizon,True)
        if not ok:return None
        candidates.update(ids)
    neighborhoods={i:[] for i in candidates};offset=0
    for name,pr in profiles.items():
        cells=required(pr,policy,speed,horizon);res=result[name]
        mask=np.isin(res['ray_indices'],list(candidates));ids=res['ray_indices'][mask]
        w=res['witnesses'][mask]@rotation(yaw)
        radius=pr.r_min-res['error'][mask]-pr.step/math.sqrt(2)-1e-9;use=radius>0
        near=cKDTree(cells).query_ball_point(w[use],radius[use])
        for ray,neighbors in zip(ids[use],near):neighborhoods[int(ray)].extend(offset+j for j in neighbors)
        offset+=len(cells)
    inverted=[[] for _ in range(offset)]
    for i,cells in neighborhoods.items():
        for cell in cells:inverted[cell].append(i)
    if any(not x for x in inverted):raise RuntimeError('Incomplete candidate cover')
    gains={i:len(cells) for i,cells in neighborhoods.items()}
    heap=[(-g,i) for i,g in gains.items() if g];heapq.heapify(heap)
    missing=np.ones(offset,dtype=bool);remaining=offset;selected=[]
    while remaining:
        while heap:
            ng,i=heapq.heappop(heap)
            if -ng==gains[i]:break
        else:raise RuntimeError('Incomplete greedy cover')
        if not gains[i] or len(selected)>=MAX_RAYS:return None
        selected.append(i);changed=set()
        for cell in neighborhoods[i]:
            if not missing[cell]:continue
            missing[cell]=False;remaining-=1
            for other in inverted[cell]:gains[other]-=1;changed.add(other)
        for other in changed:
            if gains[other]>0:heapq.heappush(heap,(-gains[other],other))
    if not selected:return None
    raw=json.loads(serialize(o,r[selected],ref,profiles,scope,contract,horizon,sequence))
    blob=canonical(dict(kind='policy-evidence-v1',policy=asdict(policy),speed=speed,yaw=yaw,raw=raw))
    return blob if verify(blob,profiles,scope,contract,policy,speed,yaw,ref/TIME_SCALE) else None


def verify(blob,profiles,scope,contract,policy,speed,yaw,now,min_sequence=0):
    """Recompute geometry, physical contracts remain external prerequisites."""
    try:
        if len(blob)>2_100_000 or not math.isfinite(now) or len({p.clock for p in profiles.values()})!=1:return False
        packet=json.loads(blob)
        if set(packet)!={'kind','policy','speed','yaw','raw'} or packet['kind']!='policy-evidence-v1':return False
        if canonical(packet['policy'])!=canonical(asdict(policy)) or packet['speed']!=speed or packet['yaw']!=yaw:return False
        p,o,r=decode(canonical(packet['raw']),profiles,scope,contract)
        receipt=math.ceil(Fraction.from_float(float(now))*TIME_SCALE)
        if p['sequence']<min_sequence or not p['reference_us']<=receipt<p['reference_us']+p['horizon_us']:return False
        res=projections(o,r,p['reference_us'],profiles,scope,contract)
        return all(coverage(res[name],pr,policy,speed,yaw,p['horizon_us']/TIME_SCALE)[0] for name,pr in profiles.items())
    except (ValueError,TypeError,KeyError,OverflowError,IndexError):return False


def conditional_stop_gate(blob,profiles,scope,contract,policy,speed,yaw,now):
    """Timing diagnostic, NOT physical movement authorization."""
    if not verify(blob,profiles,scope,contract,policy,speed,yaw,now):return False
    try:
        p=json.loads(blob)['raw']['payload']
        receipt=math.ceil(Fraction.from_float(float(now))*TIME_SCALE)
        age=(receipt-p['reference_us'])/TIME_SCALE
        duration=stop_duration(speed,age,policy)
        ticks=math.ceil(Fraction.from_float(float(duration))*TIME_SCALE)
        return receipt+ticks<p['reference_us']+p['horizon_us']
    except (ValueError,TypeError,KeyError,OverflowError):return False
