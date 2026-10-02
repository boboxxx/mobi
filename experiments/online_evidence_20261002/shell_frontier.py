"""Exact joint fixed-region horizon, stopping at the first unknown distance shell.

This changes search order only. All unexamined cells are farther than the tested
boundary; they cannot improve a rejected horizon or defeat a passed capped one.
"""
import math, sys
from functools import lru_cache
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'expiry_frontier_20261001'))
from frontier import body
from geometry import grid, travel


@lru_cache(maxsize=32)
def ordered(domain,step,half_length,half_width):
    cells,_=grid(domain,step)
    low=np.array([-half_length,-half_width]);high=-low
    distance=body.box_distance(cells,low,high)
    indices=np.argsort(distance,kind='stable')
    return cells[indices],distance[indices]


def class_frontier(result,profile,scope,motion,prior,reference,cap_us,batch_size=2048):
    if any(x!=0 for x in [motion.vx,motion.vy,motion.acceleration,motion.yaw_rate]):
        raise ValueError('Only fixed regions are supported')
    if type(cap_us) is not int or cap_us<1 or type(batch_size) is not int or batch_size<1:
        raise ValueError('Positive integer cap and batch size required')
    cells,distances=ordered(profile.domain,profile.step,motion.half_length,motion.half_width)
    low,high,margin=body.envelope(motion,0,profile.clock)
    extent=np.maximum(np.abs(low),np.abs(high))
    def inflate(h):return margin+profile.r_max+travel(h/body.TIME_SCALE+profile.clock,profile)
    # There is no need to inspect beyond the largest horizon allowed by domain.
    lo,hi=0,cap_us+1
    while hi-lo>1:
        mid=(lo+hi)//2
        if np.all(extent+inflate(mid)<profile.domain):lo=mid
        else:hi=mid
    domain_cap=lo
    if domain_cap==0:
        return dict(horizon_us=0,cap_limited=False,cells_examined=0,grid_cells=len(cells),
                    nearest_unexcluded_cell=None,nearest_unexcluded_distance_m=None,limiter='domain')
    cutoff=inflate(domain_cap)+profile.step/math.sqrt(2)
    end=int(np.searchsorted(distances,cutoff,side='right'))
    witnesses=result['witnesses']@body.rotation(motion.yaw)
    groups=[]
    for error in np.unique(result['error']):
        radius=profile.r_min-error-profile.step/math.sqrt(2)-1e-9
        if radius>0:groups.append((radius,cKDTree(witnesses[result['error']==error])))
    nearest=math.inf;unknown=None;examined=0
    for begin in range(0,end,batch_size):
        stop=min(begin+batch_size,end);chunk=cells[begin:stop]
        missing=~body.prior_covers(chunk,scope,motion,prior,profile,reference)
        for radius,tree in groups:
            todo=np.flatnonzero(missing)
            if not len(todo):break
            near=tree.query(chunk[todo],k=1)[0]
            missing[todo[near<radius]]=False
        examined+=len(chunk)
        if missing.any():
            first=begin+int(np.flatnonzero(missing)[0]);nearest=float(distances[first]);unknown=cells[first].tolist();break
    def passes(h):
        b=inflate(h)
        return bool(np.all(extent+b<profile.domain) and nearest>b+profile.step/math.sqrt(2))
    lo,hi=0,cap_us+1
    while hi-lo>1:
        mid=(lo+hi)//2
        if passes(mid):lo=mid
        else:hi=mid
    assert lo==0 or passes(lo)
    assert lo==cap_us or not passes(lo+1)
    return dict(horizon_us=lo,cap_limited=lo==cap_us,cells_examined=examined,grid_cells=len(cells),
                nearest_unexcluded_cell=unknown,nearest_unexcluded_distance_m=nearest if math.isfinite(nearest) else None,
                limiter='cap' if lo==cap_us else ('unknown_cell' if unknown is not None else 'domain'))


def frontier(results,profiles,scope,motion,prior,reference,cap_us=2_000_000):
    if type(cap_us) is not int or cap_us<1:raise ValueError('Positive integer cap required')
    cap=cap_us;classes={}
    # Large footprint / coarse grid tends to locate a limiting boundary first.
    order=sorted(profiles,key=lambda n:-(profiles[n].r_max+profiles[n].step))
    for name in order:
        if cap==0:break
        classes[name]=class_frontier(results[name],profiles[name],scope,motion,prior,reference,cap)
        cap=min(cap,classes[name]['horizon_us'])
    return dict(horizon_us=cap,classes=classes,limiting_classes=[n for n,v in classes.items() if v['horizon_us']==cap],
                classes_not_examined=[n for n in profiles if n not in classes])
