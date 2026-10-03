"""Tighter rotation/score enclosures; unchanged point score and posterior."""
import math
from fractions import Fraction
import numpy as np
from bounds import RayIndex,rotation,intersections,PAD,GUARD

def rotation_difference(center_angles,half_angles):
    p,y,r=center_angles;hp,hy,hr=half_angles
    # R0^T R(theta) = Ay Ap Ar, rotations about fixed local axes.
    xp=rotation(0,0,-r);yp=rotation(-p,0,0)
    axes=[xp@yp@np.array([0.,0.,1.]),xp@np.array([0.,1.,0.]),np.array([1.,0.,0.])]
    result=np.eye(3)
    for axis,h in zip(axes,[hy,hp,hr]):
        x,y0,z=axis;cross=np.array([[0.,-z,y0],[z,0.,-x],[-y0,x,0.]])
        sine=1. if h>=math.pi/2 else math.sin(h);versine=2. if h>=math.pi else 1-math.cos(h)
        delta=sine*np.abs(cross)+versine*np.abs(np.outer(axis,axis)-np.eye(3))
        result=result@(np.eye(3)+delta)
    return np.maximum(0,result-np.eye(3))+1e-14

def refined_enclosures(cell,extent,anchor,road_rotation):
    m=cell.center();h=cell.half();r=rotation(*m[3:]);e=np.asarray(extent)+PAD;delta=rotation_difference(m[3:],h[3:]);shift=np.abs(r.T@road_rotation)@h[:3]
    # Outer: C*B + translated center. Inner: C^T*(B - center offset).
    outer=e+delta@e+shift+GUARD;inner=e-delta.T@(e+shift)-shift-GUARD
    return np.asarray(anchor)+road_rotation@m[:3],r,inner,outer

class RefinedIndex(RayIndex):
    def __init__(self,points,origin,rotation_refinement=True,count_refinement=True):
        super().__init__(points,origin);self.rotation_refinement=rotation_refinement;self.count_refinement=count_refinement
    def bound(self,cell,extent,anchor,road_rotation,indexed=True,anisotropic=True):
        if self.rotation_refinement:center,r,inner,outer=refined_enclosures(cell,extent,anchor,road_rotation)
        else:
            from bounds import enclosures
            center,r,inner,outer=enclosures(cell,extent,anchor,road_rotation,anisotropic)
        o=(self.origin-center)@r
        if np.any(inner<=0) or np.all(abs(o)<=outer):return dict(numerator=0,denominator=1,definitely_eligible=0,possibly_eligible=0,definitely_passed=0,possibly_nonpassing=0,reason='unresolved_enclosure',examined=0)
        ids=self.candidates(center,outer,indexed);d=self.d[ids]@r;possible,outer_leave=intersections(o,d,outer);definite,_=intersections(o,d,inner);n=int(possible.sum());support=int(definite.sum());k=int(np.sum(definite&(outer_leave<1-1e-10)));hits=int(np.sum(possible&(outer_leave>=1-1e-10)));assert k<=support<=n
        b=Fraction(0)
        if support>=8:
            b=Fraction(k,n)
            if self.count_refinement:b=max(b,Fraction(max(0,support-hits),support))
        return dict(numerator=b.numerator,denominator=b.denominator,definitely_eligible=support,possibly_eligible=n,definitely_passed=k,possibly_nonpassing=hits,reason=None if support>=8 else 'insufficient_guaranteed_support',examined=len(ids))
