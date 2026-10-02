"""Constructive bounded-motion witnesses, not an optimality solver."""
import ctypes,functools,math,os
import numpy as np

def backwards(stamps,ref,v,a):
    times=np.unique(stamps);assert times[-1]<=ref
    gaps=np.diff(times)/1e6;dist=v*gaps+.25*a*gaps*gaps
    age=(ref-int(times[-1]))/1e6;offset=v*age+.5*a*age*age
    cumulative=np.r_[np.cumsum(dist[::-1])[::-1],0.]+offset
    return cumulative[np.searchsorted(times,stamps)],times,cumulative

def contact_radius(directions,extent,radius):
    lo=np.zeros(len(directions));hi=np.full(len(directions),float(np.linalg.norm(extent))+radius)
    for _ in range(60):
        mid=(lo+hi)/2;dist=np.linalg.norm(np.maximum(np.abs(directions*mid[:,None])-extent,0),axis=1)
        inside=dist<=radius;lo=np.where(inside,mid,lo);hi=np.where(inside,hi,mid)
    return lo

@functools.lru_cache(maxsize=1)
def library():
    f=ctypes.CDLL(os.environ['MOBI_SEGMENT_LIBRARY']).clear_candidates
    d=np.ctypeslib.ndpointer(dtype=np.float64,ndim=1,flags='C_CONTIGUOUS');b=np.ctypeslib.ndpointer(dtype=np.uint8,ndim=1,flags='C_CONTIGUOUS')
    f.argtypes=[d,ctypes.c_int64,d,ctypes.c_int64,ctypes.c_double,ctypes.c_double,b];f.restype=ctypes.c_int;return f

def clear(candidates,rays,plane,radius):
    c=np.ascontiguousarray(candidates,dtype=np.float64);r=np.ascontiguousarray(rays,dtype=np.float64)
    if c.ndim!=2 or c.shape[1]!=4 or r.ndim!=2 or r.shape[1]!=7 or not np.isfinite(c).all() or not np.isfinite(r).all():raise ValueError('Finite segment inputs')
    out=np.empty(len(c),dtype=np.uint8)
    if library()(c.ravel(),len(c),r.ravel(),len(r),plane,radius,out):raise ValueError('Segment bounds')
    return out.astype(bool)

def find(rays,plane,query,yaw,ref,last_stamp,core,error,v=5.,a=3.):
    angles=np.arange(720)*math.pi/360;directions=np.c_[np.cos(angles),np.sin(angles)]
    contact=contact_radius(directions,np.array([2.3,1.3]),core);c,s=math.cos(yaw),math.sin(yaw);rotation=np.array([[c,-s],[s,c]])
    world_u=directions@rotation.T;effective=v+a*(ref-last_stamp)/1e6;calls=0;tested=0
    def test(h):
        nonlocal calls,tested
        radius=contact+effective*h+.5*a*h*h-.001
        centers=(directions*radius[:,None])@rotation.T+query
        candidates=np.column_stack([centers,world_u]);ok=clear(candidates,rays,plane,core+error+1e-8);calls+=1;tested+=len(ok)
        if not ok.any():return None
        j=int(np.flatnonzero(ok)[0]);return dict(time_us=round(h*1e6),direction_index=j,center_reference=candidates[j,:2].tolist(),outward_direction=world_u[j].tolist(),radial_contact=float(contact[j]))
    for index in range(31):
        h=index*.05;result=test(h)
        if result:
            if index:
                for tick in range((index-1)*10+1,index*10):
                    finer=test(tick*.005)
                    if finer:result=finer;break
            return result,dict(native_calls=calls,candidates=tested)
    return None,dict(native_calls=calls,candidates=tested)
