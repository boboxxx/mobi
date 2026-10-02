import ctypes,functools,math,os
import numpy as np

def edge_distance(u,lam,core,outer):
    q=np.array([[-2.3,-1.3],[2.3,-1.3],[2.3,1.3],[-2.3,1.3]])
    perp=np.column_stack([-u[:,1],u[:,0]])
    whiten=np.stack([u/outer,perp/core],axis=2)
    edges=q@whiten;end=np.roll(edges,-1,axis=1);delta=end-edges
    target=np.zeros((len(u),2));target[:,0]=lam/outer
    relative=target[:,None,:]-edges;parameter=np.clip(np.sum(relative*delta,axis=2)/np.sum(delta*delta,axis=2),0,1)
    distance=np.sqrt(np.min(np.sum((relative-parameter[:,:,None]*delta)**2,axis=2),axis=1))
    inside=(np.abs(u*lam[:,None])<=[2.3,1.3]).all(axis=1)
    return np.where(inside,0.,distance)

def contact(u,core,outer):
    lo=np.zeros(len(u));hi=np.full(len(u),math.hypot(2.3,1.3)+outer)
    for _ in range(60):
        mid=(lo+hi)/2;inside=edge_distance(u,mid,core,outer)<=1;lo=np.where(inside,mid,lo);hi=np.where(inside,hi,mid)
    return lo

@functools.lru_cache(maxsize=1)
def library():
    f=ctypes.CDLL(os.environ['MOBI_ELLIPSOID_LIBRARY']).ellipsoid_clear
    d=np.ctypeslib.ndpointer(dtype=np.float64,ndim=1,flags='C_CONTIGUOUS');b=np.ctypeslib.ndpointer(dtype=np.uint8,ndim=1,flags='C_CONTIGUOUS')
    f.argtypes=[d,ctypes.c_int64,d,ctypes.c_int64,ctypes.c_double,ctypes.c_double,ctypes.c_double,ctypes.c_double,b];f.restype=ctypes.c_int;return f

def clear(candidates,rays,plane,core,outer,error):
    c=np.ascontiguousarray(candidates,dtype=np.float64);r=np.ascontiguousarray(rays,dtype=np.float64)
    if c.ndim!=2 or c.shape[1]!=4 or r.ndim!=2 or r.shape[1]!=7 or not np.isfinite(c).all() or not np.isfinite(r).all() or not np.allclose(np.linalg.norm(c[:,2:],axis=1),1,rtol=0,atol=1e-14):raise ValueError('Finite unit ellipsoid inputs')
    out=np.empty(len(c),dtype=np.uint8)
    if library()(c.ravel(),len(c),r.ravel(),len(r),plane,core,outer,error,out):raise ValueError('Ellipsoid bounds')
    return out.astype(bool)

def find(rays,plane,query,yaw,ref,last_stamp,core,outer,error):
    angles=np.arange(720)*math.pi/360;u=np.column_stack([np.cos(angles),np.sin(angles)]);boundary=contact(u,core,outer);c,s=math.cos(yaw),math.sin(yaw);rotation=np.array([[c,-s],[s,c]]);world=u@rotation.T;v=5+3*(ref-last_stamp)/1e6;calls=0
    def test(h):
        nonlocal calls
        centers=(u*(boundary+v*h+1.5*h*h-.001)[:,None])@rotation.T+query;candidate=np.column_stack([centers,world]);flags=clear(candidate,rays,plane,core,outer,error);calls+=1
        if not flags.any():return None
        j=int(np.flatnonzero(flags)[0]);return dict(time_us=round(h*1e6),direction_index=j,center_reference=centers[j].tolist(),outward_direction=world[j].tolist(),radial_contact=float(boundary[j]))
    for k in range(31):
        w=test(k*.05)
        if w:
            if k:
                for tick in range((k-1)*10+1,k*10):
                    refined=test(tick*.005)
                    if refined:w=refined;break
            return w,dict(native_calls=calls,candidates=720*calls)
    return None,dict(native_calls=calls,candidates=720*calls)
