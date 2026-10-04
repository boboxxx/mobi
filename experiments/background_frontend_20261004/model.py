"""Fixed background subtraction using current XYZ only, with an immutable old map."""
import importlib.util
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('parent_xyz_frontend',ROOT/'experiments/positive_state_20261003/model.py')
parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)

def voxel_codes(local):
    p=np.asarray(local,dtype=float)
    valid=(abs(p[:,0])<=12)&(abs(p[:,1])<=8)&(p[:,2]>.3)&(p[:,2]<3)
    out=np.full(len(p),-1,dtype=np.int64)
    g=np.floor(p[valid]*10).astype(np.int64)
    out[valid]=(g[:,0]+120)*161*27+(g[:,1]+80)*27+g[:,2]-3
    return out

def extract(xyz,matrix,anchor,road,extent,static_codes,shift_m=0):
    xyz=np.asarray(xyz,dtype=float)
    matrix=np.asarray(matrix);local=(xyz@matrix[:3,:3].T+matrix[:3,3]-anchor)@road
    local=local+float(shift_m)
    codes=voxel_codes(local);removed=(codes>=0)&np.isin(codes,np.asarray(static_codes,dtype=np.int64))
    c,meta=parent.centers(local[~removed],np.zeros(3),np.eye(3),extent)
    return c,dict(**meta,background_removed=int(removed.sum()))
