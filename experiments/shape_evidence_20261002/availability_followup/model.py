"""3D box-hypothesis ray-consistency score; calibrated, not a solid-core proof."""
import math
from fractions import Fraction
import numpy as np
STRIDES=(1,4,16)
MIN_SUPPORT=8
PADDING=.03

def score(points,origin,center,rotation,extent):
    p=np.asarray(points,dtype=float);o=np.asarray(origin,dtype=float);c=np.asarray(center,dtype=float);rot=np.asarray(rotation,dtype=float);e=np.asarray(extent,dtype=float)+PADDING
    if p.ndim!=2 or p.shape[1]!=3 or o.shape!=(3,) or c.shape!=(3,) or rot.shape!=(3,3) or e.shape!=(3,) or not all(np.isfinite(x).all() for x in [p,o,c,rot,e]) or np.any(e<=PADDING):raise ValueError('Geometry')
    if not np.allclose(rot.T@rot,np.eye(3),rtol=0,atol=1e-6):raise ValueError('Rotation')
    start=(o-c)@rot;d=(p-o)@rot
    if np.all(np.abs(start)<=e):return dict(pass_count=0,visible_count=0,numerator=0,denominator=1,reason='sensor_inside_hypothesis')
    lower=np.full(len(p),-np.inf);upper=np.full(len(p),np.inf);valid=np.ones(len(p),bool)
    for axis in range(3):
        nonzero=np.abs(d[:,axis])>1e-12;valid&=nonzero|(abs(start[axis])<=e[axis]);a=np.divide(-e[axis]-start[axis],d[:,axis],out=np.full(len(p),-np.inf),where=nonzero);b=np.divide(e[axis]-start[axis],d[:,axis],out=np.full(len(p),np.inf),where=nonzero);lower=np.maximum(lower,np.minimum(a,b));upper=np.minimum(upper,np.maximum(a,b))
    eligible=valid&(upper>=np.maximum(lower,0))&(lower<=1+1e-10)&(upper>=0);n=int(eligible.sum());passed=int(np.sum(eligible&(upper<1-1e-10)))
    return dict(pass_count=passed,visible_count=n,numerator=passed if n>=MIN_SUPPORT else 0,denominator=n if n>=MIN_SUPPORT else 1,reason=None if n>=MIN_SUPPORT else 'insufficient_visible_rays')
def fraction(s):return Fraction(s['numerator'],s['denominator'])
def threshold(scores,alpha=Fraction(1,20)):
    if not 0<alpha<1:raise ValueError('Risk level')
    n=len(scores);rank=math.ceil((n+1)*(1-alpha));values=sorted(scores)
    if rank>n:return dict(n=n,rank=rank,numerator=1,denominator=1,vacuous=True)
    x=values[rank-1];return dict(n=n,rank=rank,numerator=x.numerator,denominator=x.denominator,vacuous=x==1)
def rejected(s,q):return s['reason'] is None and fraction(s)>Fraction(q['numerator'],q['denominator'])
