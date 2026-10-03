import ctypes as C,importlib.util,time
from pathlib import Path
import numpy as np
from codec import decode,decode_full,ROOT
spec=importlib.util.spec_from_file_location('base_runtime',ROOT/'experiments/expiry_runtime_20261003/runtime.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
F64,I64,I32=base.F64,base.I64,base.I32

def library(path):
    lib=base.library(path);lib.tube_build.argtypes=lib.build.argtypes+[C.c_double];lib.tube_build.restype=C.c_void_p;lib.tube_destroy.argtypes=[C.c_void_p];lib.tube_revalidate.argtypes=[C.c_void_p,F64,I32,C.c_int,F64,I32,C.c_int,F64,I32,C.c_int,C.c_int,I64,I32,F64];lib.tube_test_counts.argtypes=[F64,I32,C.c_int,F64,F64,F64,F64,F64,C.c_double,I64];return lib
class Proof:
    def __init__(self,lib,packet,digest,bps,source,query,threshold,budget,radius_um):
        begin=time.perf_counter();self.lib=lib;self.packet=packet;self.digest=digest;self.bps=bps;self.radius_um=radius_um;d=decode_full(packet,digest,len(bps));self.old=d
        if type(radius_um)is not int or not 0<=radius_um<=100000 or d['stride']!=4:raise ValueError('Fixed ball/budget contract')
        self.world=np.ascontiguousarray(d['views'][-1]['points']);self.strides=np.where(np.arange(len(self.world))%4==0,16,4).astype(np.int32);ext=np.asarray(source['extent'],np.float64);self.ptr=lib.tube_build(ext,np.asarray(source['anchor'],np.float64),np.ascontiguousarray(source['road_rotation'],dtype=np.float64),np.ascontiguousarray(d['origin']),*query,int(np.ceil(np.linalg.norm(ext)*1e6)),threshold['numerator'],threshold['denominator'],self.world,self.strides,len(self.world),budget,radius_um/1e6)
        if not self.ptr:raise ValueError('Tube proof contract')
        self.n=lib.size(self.ptr);self.stat=np.zeros(5);lib.stats(self.ptr,self.stat);self.total_s=time.perf_counter()-begin
    def export(self):
        cells=np.empty((self.n,12));meta=np.empty((self.n,6),np.int64);counts=np.empty((self.n,2,4),np.int64);self.lib.export_nodes(self.ptr,cells,meta,counts);return dict(cells=cells,meta=meta,counts=counts)
    def check(self,wire,incremental=True):
        begin=time.perf_counter();d=decode(wire,self.packet,self.digest,self.bps)
        if d['radius_um']!=self.radius_um:raise ValueError('Cache radius')
        ids=d['indices'];empty=np.empty((0,3));emptyi=np.empty(0,np.int32);mask=np.ones(len(self.world),bool);mask[ids]=False;inliers=np.ascontiguousarray(self.world[mask]) if not incremental else empty;ins=np.ascontiguousarray(self.strides[mask]) if not incremental else emptyi;oldp=np.ascontiguousarray(self.world[ids]) if incremental else empty;olds=np.ascontiguousarray(self.strides[ids]) if incremental else emptyi;newp=d['exact_world'];news=np.ascontiguousarray(self.strides[ids]);counts=np.zeros((self.n,2,4),np.int64);accepted=np.full(self.n,-9,np.int32);stat=np.zeros(5);self.lib.tube_revalidate(self.ptr,inliers,ins,len(inliers),oldp,olds,len(oldp),newp,news,len(newp),int(incremental),counts,accepted,stat)
        if np.any(counts<0) or np.any(counts[:,:,1]>counts[:,:,0]) or np.any(counts[:,:,2]>counts[:,:,1]) or np.any(counts[:,:,3]>counts[:,:,0]):raise AssertionError('Count invariant')
        return dict(counts=counts,accepted=accepted,stat=stat,total_s=time.perf_counter()-begin,frame=d['frame'],timestamp=d['timestamp'],exceptions=len(ids))
    def close(self):
        if self.ptr:self.lib.tube_destroy(self.ptr);self.ptr=None
