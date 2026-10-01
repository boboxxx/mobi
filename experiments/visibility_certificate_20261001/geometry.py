"""Conditional center-space exclusion from empty ray witnesses.

The opaque-core/outer-radius and bounded-error contract is indispensable.
No interpolation between rays and no obstacle-size-free safety claim.
"""
from dataclasses import dataclass, asdict
from functools import lru_cache
import math
import numpy as np
from scipy.spatial import cKDTree


@dataclass(frozen=True)
class Profile:
    r_min: float = .55
    r_max: float = 2.5
    query_radius: float = .5
    error: float = .05
    speed: float = 5.
    acceleration: float = 3.
    clock: float = .02
    domain: float = 15.
    step: float = .1

    def __post_init__(self):
        values=list(asdict(self).values())
        if not all(math.isfinite(x) for x in values):raise ValueError('Nonfinite profile')
        if min(values)<0 or self.step<=0 or self.domain<=0:raise ValueError('Invalid profile')
        if self.r_max<self.r_min or self.r_min<=0:raise ValueError('Invalid obstacle radii')
        if self.query_radius+self.r_max>=self.domain:raise ValueError('Domain must enclose inflated query')
        if abs(2*self.domain/self.step-round(2*self.domain/self.step))>1e-7:raise ValueError('Grid must tile domain exactly')


@lru_cache(maxsize=16)
def grid(domain,step):
    axis=-domain+(np.arange(round(2*domain/step))+.5)*step
    x,y=np.meshgrid(axis,axis,indexing='ij')
    centers=np.column_stack([x.ravel(),y.ravel()])
    # Exact distance of an axis-aligned square tile to the query origin.
    distance=np.linalg.norm(np.maximum(np.abs(centers)-step/2,0),axis=1)
    return centers,distance


def plane_witnesses(points,origin,query,probe_z=.6):
    """Intersect first-return rays with a plane strictly before the return.

    Coordinate errors must already be bounded at the resulting witness plane.
    This function does not infer such a bound from arbitrary sensor noise.
    """
    points=np.asarray(points,dtype=float);origin=np.asarray(origin,dtype=float)
    if points.ndim!=2 or points.shape[1]!=3 or origin.shape!=(3,):raise ValueError('Bad ray array')
    if not np.isfinite(points).all() or not np.isfinite(origin).all():raise ValueError('Nonfinite rays')
    if origin[2]<=probe_z:return np.empty((0,2))
    valid=points[:,2]<probe_z-1e-6
    endpoints=points[valid]
    t=(origin[2]-probe_z)/(origin[2]-endpoints[:,2])
    return origin[:2]+t[:,None]*(endpoints[:,:2]-origin[:2])-np.asarray(query)


def travel(seconds,profile):
    return profile.speed*seconds+.5*profile.acceleration*seconds**2


def inverse_travel(distance,profile):
    if distance<=0:return 0.
    if profile.acceleration>0:
        t=2*distance/(profile.speed+math.sqrt(profile.speed**2+2*profile.acceleration*distance))
    elif profile.speed>0:t=distance/profile.speed
    else:return math.inf
    return max(0.,t-profile.clock)


def certify(witnesses,profile,extra_error=0.,return_mask=False):
    witnesses=np.asarray(witnesses,dtype=float).reshape(-1,2)
    if not np.isfinite(witnesses).all() or extra_error<0 or not math.isfinite(extra_error):raise ValueError('Invalid witnesses/error')
    centers,dist=grid(profile.domain,profile.step)
    radius=profile.r_min-profile.error-extra_error
    if len(witnesses) and radius>0:
        nearest=cKDTree(witnesses).query(centers,k=1)[0]
        excluded=nearest+profile.step/math.sqrt(2)<radius-1e-9
    else:excluded=np.zeros(len(centers),dtype=bool)
    inflated=profile.query_radius+profile.r_max
    outside=profile.domain-inflated
    internal=float(np.min(dist[~excluded])-inflated) if np.any(~excluded) else outside
    clearance=max(0.,min(outside,internal))
    result=dict(clearance_m=clearance,validity_s=inverse_travel(clearance,profile),
                witnesses=len(witnesses),excluded_tiles=int(excluded.sum()),total_tiles=len(centers))
    if return_mask:result['excluded']=excluded
    return result


def covers_horizon(witnesses,profile,seconds,extra_error=0.):
    if not math.isfinite(seconds) or seconds<=0:return False
    centers,dist=grid(profile.domain,profile.step)
    radius=profile.query_radius+profile.r_max+travel(seconds+profile.clock,profile)
    if radius>=profile.domain:return False
    needed=centers[dist<=radius]
    w=np.asarray(witnesses,dtype=float).reshape(-1,2)
    if not len(w) or not np.isfinite(w).all():return False
    distances=cKDTree(w).query(needed,k=1)[0]
    return bool(np.all(distances+profile.step/math.sqrt(2)<profile.r_min-profile.error-extra_error-1e-9))
