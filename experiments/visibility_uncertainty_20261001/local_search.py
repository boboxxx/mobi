"""Exact nearest-unknown search for the SAME conservative binned geometry.

Order tiles by their lower distance to the query center. Once an unresolved
tile is found, farther tiles cannot decrease clearance. No spatial assumption
is relaxed. The exhaustive weighted implementation is the reference.
"""
from functools import lru_cache
import math
import numpy as np
from scipy.spatial import cKDTree
from weighted import grid, inverse_travel


@lru_cache(maxsize=8)
def ordered_grid(domain,step):
    c,d=grid(domain,step);order=np.argsort(d,kind='stable')
    # Beyond this distance, the already retained outside-domain set dominates.
    order=order[d[order]<domain]
    return c[order],d[order]


def compare_local(witnesses,errors,profile,bin_width=.01,chunk=1024):
    w=np.asarray(witnesses,dtype=float).reshape(-1,2);e=np.asarray(errors,dtype=float)
    if e.shape!=(len(w),) or not np.isfinite(w).all() or not np.isfinite(e).all() or np.any(e<0):
        raise ValueError('Invalid witness bounds')
    if profile.error!=0 or not math.isfinite(bin_width) or bin_width<=0 or not isinstance(chunk,int) or chunk<=0:
        raise ValueError('Invalid common error, bin width or chunk')
    usable=e<profile.r_min-profile.step/math.sqrt(2);w,e=w[usable],e[usable]
    bins=np.ceil(e/bin_width).astype(np.int64)
    keys=[int(b) for b in np.unique(bins) if b*bin_width+profile.step/math.sqrt(2)<profile.r_min]
    trees={b:cKDTree(w[bins==b]) for b in keys};centers,dist=ordered_grid(profile.domain,profile.step)
    cache={};queried=0
    def distances(b,start):
        nonlocal queried
        key=(b,start)
        if key not in cache:
            cache[key]=trees[b].query(centers[start:start+chunk],k=1)[0]
            queried+=len(cache[key])
        return cache[key]
    def expiry(unknown_distance):
        clearance=max(0.,min(profile.domain,unknown_distance)-profile.query_radius-profile.r_max)
        return inverse_travel(clearance,profile)
    # Heterogeneous union: cover each tile by any sufficiently precise ray.
    first=profile.domain
    for start in range(0,len(centers),chunk):
        covered=np.zeros(len(centers[start:start+chunk]),dtype=bool)
        for b in keys:
            covered|=distances(b,start)+b*bin_width+profile.step/math.sqrt(2)<profile.r_min-1e-9
            if covered.all():break
        missing=np.flatnonzero(~covered)
        if len(missing):first=float(dist[start+missing[0]]);break
    heterogeneous=expiry(first)
    # Strong baseline uses all rays up to each budget. Reuse exact group queries.
    best=0.;budget_best=0.
    for index,b in enumerate(keys):
        first=profile.domain
        for start in range(0,len(centers),chunk):
            nearest=np.full(len(centers[start:start+chunk]),np.inf)
            for previous in keys[:index+1]:nearest=np.minimum(nearest,distances(previous,start))
            covered=nearest+b*bin_width+profile.step/math.sqrt(2)<profile.r_min-1e-9
            missing=np.flatnonzero(~covered)
            if len(missing):first=float(dist[start+missing[0]]);break
        ttl=expiry(first)
        if ttl>best:best=ttl;budget_best=b*bin_width
    return dict(validity_s=heterogeneous,best_uniform_ttl_s=best,
                best_uniform_budget_m=budget_best,tree_point_queries=queried)
