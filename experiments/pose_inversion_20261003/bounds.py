"""Conservative score bounds over continuous translation/Euler-pose cells."""
import math
from dataclasses import dataclass
from fractions import Fraction
import numpy as np
from scipy.spatial import cKDTree

PAD=.03
GUARD=1e-7
@dataclass(frozen=True)
class Cell:
    # xyz in the public road frame, then pitch/yaw/roll in radians.
    lo:tuple
    hi:tuple
    def __post_init__(self):
        if len(self.lo)!=6 or len(self.hi)!=6 or not all(math.isfinite(x) for x in self.lo+self.hi) or any(a>b for a,b in zip(self.lo,self.hi)):raise ValueError('Pose cell')
    def center(self):return (np.asarray(self.lo)+self.hi)/2
    def half(self):return (np.asarray(self.hi)-self.lo)/2
    def split(self,extent):
        h=self.half();r=float(np.linalg.norm(np.asarray(extent)+PAD));weight=np.r_[h[:3],2*r*np.sin(np.minimum(h[3:],math.pi)/2)];axis=int(np.argmax(weight));mid=(self.lo[axis]+self.hi[axis])/2
        if mid==self.lo[axis] or mid==self.hi[axis]:raise ValueError('Cell cannot be split')
        l=list(self.lo);u=list(self.hi);u[axis]=mid;left=Cell(self.lo,tuple(u));l[axis]=mid;return left,Cell(tuple(l),self.hi)

def rotation(p,y,r):
    cp,sp=math.cos(p),math.sin(p);cy,sy=math.cos(y),math.sin(y);cr,sr=math.cos(r),math.sin(r)
    return np.array([[cp*cy,cy*sp*sr-sy*cr,-cy*sp*cr-sy*sr],[cp*sy,sy*sp*sr+cy*cr,-sy*sp*cr+cy*sr],[sp,-cp*sr,cp*cr]])

def enclosures(cell,extent,anchor,road_rotation,anisotropic=True):
    m=cell.center();h=cell.half();r=rotation(*m[3:]);e=np.asarray(extent)+PAD
    # Product-rotation geodesic deviation <= sum of Euler half widths.
    angle=min(math.pi,float(sum(h[3:])));turn=2*float(np.linalg.norm(e))*math.sin(angle/2)
    shift=np.abs(r.T@road_rotation)@h[:3] if anisotropic else np.full(3,float(np.linalg.norm(h[:3])))
    uncertainty=shift+turn+GUARD
    return np.asarray(anchor)+road_rotation@m[:3],r,e-uncertainty,e+uncertainty

def intersections(local_origin,directions,extent):
    n=len(directions);enter=np.full(n,-np.inf);leave=np.full(n,np.inf);valid=np.ones(n,bool)
    for j in range(3):
        nz=abs(directions[:,j])>1e-12;valid&=nz|(abs(local_origin[j])<=extent[j]);a=np.divide(-extent[j]-local_origin[j],directions[:,j],out=np.full(n,-np.inf),where=nz);b=np.divide(extent[j]-local_origin[j],directions[:,j],out=np.full(n,np.inf),where=nz);enter=np.maximum(enter,np.minimum(a,b));leave=np.minimum(leave,np.maximum(a,b))
    eligible=valid&(leave>=np.maximum(enter,0))&(enter<=1+1e-10)&(leave>=0)
    return eligible,leave

class RayIndex:
    def __init__(self,points,origin):
        self.points=np.asarray(points,dtype=float);self.origin=np.asarray(origin,dtype=float)
        if self.points.ndim!=2 or self.points.shape[1]!=3 or self.origin.shape!=(3,) or not np.isfinite(self.points).all() or not np.isfinite(self.origin).all():raise ValueError('Rays')
        self.d=self.points-self.origin;self.length=np.linalg.norm(self.d,axis=1);self.nonzero=np.flatnonzero(self.length>1e-12);self.unit=self.d[self.nonzero]/self.length[self.nonzero,None];self.tree=cKDTree(self.unit)
    def candidates(self,center,outer,enabled=True):
        if not enabled:return np.arange(len(self.points))
        vector=center-self.origin;distance=float(np.linalg.norm(vector));radius=float(np.linalg.norm(outer))+GUARD
        if distance<=radius:return np.arange(len(self.points))
        cosine=math.sqrt(max(0,1-(radius/distance)**2));chord=math.sqrt(max(0,2*(1-cosine)))+1e-10
        return self.nonzero[np.asarray(self.tree.query_ball_point(vector/distance,chord),dtype=int)]
    def bound(self,cell,extent,anchor,road_rotation,indexed=True,anisotropic=True):
        center,r,inner,outer=enclosures(cell,extent,anchor,road_rotation,anisotropic);o=(self.origin-center)@r
        if np.any(inner<=0) or np.all(abs(o)<=outer):return dict(numerator=0,denominator=1,definitely_eligible=0,possibly_eligible=0,definitely_passed=0,reason='unresolved_enclosure',examined=0)
        ids=self.candidates(center,outer,indexed);d=self.d[ids]@r;possible,outer_leave=intersections(o,d,outer);definite,_=intersections(o,d,inner);n=int(np.sum(possible));support=int(np.sum(definite));k=int(np.sum(definite&(outer_leave<1-1e-10)))
        assert k<=support<=n
        return dict(numerator=k if support>=8 else 0,denominator=n if support>=8 and n else 1,definitely_eligible=support,possibly_eligible=n,definitely_passed=k,reason=None if support>=8 else 'insufficient_guaranteed_support',examined=len(ids))

def value(result):return Fraction(result['numerator'],result['denominator'])
