"""Conservative heterogeneous witness-error exclusion using upward error bins."""
import math
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'visibility_certificate_20261001'))
from geometry import grid, inverse_travel


def certify_weighted(witnesses, errors, profile, bin_width=.01, return_mask=False):
    """Each supplied error is a full projection+temporal exclusion debit.

    profile.error must be zero to avoid silently ignoring or double-counting
    an additional common error. Other physical bounds retain their meaning.
    Upward bucketing is conservative: it can only shrink the excluded set.
    """
    w=np.asarray(witnesses,dtype=float).reshape(-1,2);e=np.asarray(errors,dtype=float)
    if e.shape!=(len(w),) or not np.isfinite(w).all() or not np.isfinite(e).all() or np.any(e<0):
        raise ValueError('Invalid witnesses or error bounds')
    if not math.isfinite(bin_width) or bin_width<=0 or profile.error!=0:
        raise ValueError('Use positive bin width and zero additional common error')
    centers,dist=grid(profile.domain,profile.step)
    excluded=np.zeros(len(centers),dtype=bool)
    usable=e < profile.r_min-profile.step/math.sqrt(2)
    w,e=w[usable],e[usable]
    bins=np.ceil(e/bin_width).astype(np.int64)
    for b in np.unique(bins):
        radius=profile.r_min-float(b)*bin_width-profile.step/math.sqrt(2)-1e-9
        if radius<=0:continue
        idx=np.flatnonzero(~excluded)
        if not len(idx):break
        nearest=cKDTree(w[bins==b]).query(centers[idx],k=1)[0]
        excluded[idx[nearest<radius]]=True
    inflated=profile.query_radius+profile.r_max
    outside=profile.domain-inflated
    internal=float(np.min(dist[~excluded])-inflated) if np.any(~excluded) else outside
    clearance=max(0.,min(outside,internal))
    result=dict(clearance_m=clearance,validity_s=inverse_travel(clearance,profile),
                witnesses=len(w),error_bins=len(np.unique(bins)),excluded_tiles=int(excluded.sum()))
    if return_mask:result['excluded']=excluded
    return result


def best_uniform(witnesses, errors, profile, bin_width=.01):
    """Strong baseline: best common error budget over the SAME upward bins.

    Each threshold retains every witness below it. Shared nearest-distance
    updates avoid rebuilding all cumulative trees, and do not use labels.
    """
    w=np.asarray(witnesses,dtype=float).reshape(-1,2);e=np.asarray(errors,dtype=float)
    if e.shape!=(len(w),) or not np.isfinite(w).all() or not np.isfinite(e).all() or np.any(e<0):
        raise ValueError('Invalid witnesses or error bounds')
    if not math.isfinite(bin_width) or bin_width<=0 or profile.error!=0:
        raise ValueError('Invalid common error or bin width')
    usable=e<profile.r_min-profile.step/math.sqrt(2);w,e=w[usable],e[usable]
    bins=np.ceil(e/bin_width).astype(np.int64);centers,dist=grid(profile.domain,profile.step)
    nearest=np.full(len(centers),np.inf);best=dict(validity_s=0.,error_budget_m=0.)
    inflated=profile.query_radius+profile.r_max;outside=profile.domain-inflated
    for b in np.unique(bins):
        budget=float(b)*bin_width
        if budget+profile.step/math.sqrt(2)>=profile.r_min:continue
        nearest=np.minimum(nearest,cKDTree(w[bins==b]).query(centers,k=1)[0])
        excluded=nearest+budget+profile.step/math.sqrt(2)<profile.r_min-1e-9
        internal=float(np.min(dist[~excluded])-inflated) if np.any(~excluded) else outside
        ttl=inverse_travel(max(0.,min(outside,internal)),profile)
        if ttl>best['validity_s']:best=dict(validity_s=ttl,error_budget_m=budget)
    return best
