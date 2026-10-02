"""Finite independent contact normal and motion heading family."""
import math
import numpy as np
import ellipsoid

def contacts(core,outer):
    angles=np.arange(128)*math.pi/64;u=np.column_stack([np.cos(angles),np.sin(angles)])
    normals=np.arange(64)*math.pi/32;n=np.column_stack([np.cos(normals),np.sin(normals)])
    b=np.sign(n)*[2.3,1.3];nn=[n];bb=[b]
    for direction,axis in [([1.,0.],0),([-1.,0.],0),([0.,1.],1),([0.,-1.],1)]:
        extra=np.repeat(np.array(direction)[None,:],7,axis=0);edge=np.zeros((7,2));edge[:,axis]=direction[axis]*[2.3,1.3][axis];edge[:,1-axis]=np.linspace(-1,1,9)[1:-1]*[2.3,1.3][1-axis];nn.append(extra);bb.append(edge)
    n=np.concatenate(nn);b=np.concatenate(bb);uu=np.repeat(u,len(n),axis=0);nn=np.tile(n,(len(u),1));bb=np.tile(b,(len(u),1))
    # E's support point with outward normal n: Sigma*n/sqrt(n^T*Sigma*n).
    sn=core*core*nn+(outer*outer-core*core)*uu*np.sum(uu*nn,axis=1)[:,None]
    support=sn/np.sqrt(np.sum(nn*sn,axis=1))[:,None];future=bb+support-.001*nn
    return future,uu,nn

def find(rays,plane,query,yaw,ref,last_stamp,core,outer,error):
    future,u,n=contacts(core,outer);c,s=math.cos(yaw),math.sin(yaw);rotation=np.array([[c,-s],[s,c]]);world_u=u@rotation.T;world_future=future@rotation.T+query;v=5+3*(ref-last_stamp)/1e6;calls=0;tested=0
    def test(h):
        nonlocal calls,tested
        center=world_future+world_u*(v*h+1.5*h*h)
        for start in range(0,len(u),2000):
            candidate=np.column_stack([center[start:start+2000],world_u[start:start+2000]])
            flags=ellipsoid.clear(candidate,rays,plane,core,outer,error);calls+=1;tested+=len(flags)
            if flags.any():
                j=start+int(np.flatnonzero(flags)[0]);return dict(time_us=round(h*1e6),contact_index=j,center_reference=center[j].tolist(),outward_direction=world_u[j].tolist(),center_future=world_future[j].tolist(),contact_normal=(n[j]@rotation.T).tolist())
        return None
    for index in range(31):
        w=test(index*.05)
        if w:
            if index:
                for tick in range((index-1)*10+1,index*10):
                    finer=test(tick*.005)
                    if finer:w=finer;break
            return w,dict(native_calls=calls,candidates=tested)
    return None,dict(native_calls=calls,candidates=tested)
