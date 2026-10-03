"""Ray score of an OBB intersected with a fixed public above-road halfspace."""
import numpy as np

def score(points,origin,center,rotation,extent,cut_z=.15):
    points=np.asarray(points,float);origin=np.asarray(origin,float);center=np.asarray(center,float);rotation=np.asarray(rotation,float);extent=np.asarray(extent,float)+.03
    if points.ndim!=2 or points.shape[1]!=3 or origin.shape!=(3,) or center.shape!=(3,) or rotation.shape!=(3,3) or extent.shape!=(3,) or not all(np.isfinite(x).all() for x in [points,origin,center,rotation,extent]) or not np.isfinite(cut_z) or np.any(extent<=.03) or not np.allclose(rotation.T@rotation,np.eye(3),atol=1e-6,rtol=0):raise ValueError('Geometry')
    o=(origin-center)@rotation;d=(points-origin)@rotation
    if np.all(abs(o)<=extent) and origin[2]>=cut_z:return dict(numerator=0,denominator=1,visible_count=0,pass_count=0,reason='sensor_inside')
    lo=np.zeros(len(points));hi=np.full(len(points),np.inf);valid=np.ones(len(points),bool)
    for axis in range(3):
        nz=abs(d[:,axis])>1e-12;valid&=nz|(abs(o[axis])<=extent[axis]);a=np.divide(-extent[axis]-o[axis],d[:,axis],out=np.full(len(points),-np.inf),where=nz);b=np.divide(extent[axis]-o[axis],d[:,axis],out=np.full(len(points),np.inf),where=nz);lo=np.maximum(lo,np.minimum(a,b));hi=np.minimum(hi,np.maximum(a,b))
    dz=points[:,2]-origin[2];up=dz>1e-12;down=dz< -1e-12;flat=~(up|down);valid&=~flat|(origin[2]>=cut_z)
    cross=np.divide(cut_z-origin[2],dz,out=np.zeros(len(points)),where=~flat);lo=np.maximum(lo,np.where(up,cross,-np.inf));hi=np.minimum(hi,np.where(down,cross,np.inf))
    eligible=valid&(hi>=lo)&(lo<=1+1e-10);n=int(eligible.sum());k=int(np.sum(eligible&(hi<1-1e-10)))
    return dict(numerator=k if n>=8 else 0,denominator=n if n>=8 else 1,visible_count=n,pass_count=k,reason=None if n>=8 else 'insufficient_support')
