"""Validated packet boundary and native current-observation proof revalidation."""
import ctypes as C,hashlib,importlib.util,json,math,subprocess,sys,time,zlib
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'experiments/pose_inversion_20261003'))
from packet import encode,decode
from reference_codec import encode as encode_delta,decode as decode_delta
F64=np.ctypeslib.ndpointer(dtype=np.float64,flags='C_CONTIGUOUS');I64=np.ctypeslib.ndpointer(dtype=np.int64,flags='C_CONTIGUOUS');I32=np.ctypeslib.ndpointer(dtype=np.int32,flags='C_CONTIGUOUS')
def library(path):
    lib=C.CDLL(str(path));lib.build.argtypes=[F64,F64,F64,F64,C.c_double,C.c_double,C.c_int64,C.c_int64,C.c_int64,F64,I32,C.c_int,C.c_int];lib.build.restype=C.c_void_p;lib.size.argtypes=[C.c_void_p];lib.size.restype=C.c_int;lib.stats.argtypes=[C.c_void_p,F64];lib.export_nodes.argtypes=[C.c_void_p,F64,I64,I64];lib.destroy.argtypes=[C.c_void_p];lib.revalidate.argtypes=[C.c_void_p,F64,I32,C.c_int,F64,I32,C.c_int,C.c_int,I64,I32,F64];lib.exact_age.argtypes=[C.c_int64,C.c_int64,C.c_int64];lib.exact_age.restype=C.c_int;return lib

def compile_kernel(output):
    begin=time.perf_counter();cmd=['c++','-O3','-std=c++17','-ffp-contract=off','-shared','-fPIC',str(HERE/'kernel.cpp'),'-o',str(output)];subprocess.run(cmd,check=True);return dict(command=cmd,seconds=time.perf_counter()-begin,compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0],source_sha256=hashlib.sha256((HERE/'kernel.cpp').read_bytes()).hexdigest(),binary_sha256=hashlib.sha256(output.read_bytes()).hexdigest())

def make_packet(source,digest,bps):
    with np.load(ROOT/source['source_cloud']) as z:
        raw=z['raw'];return encode(np.c_[raw['x'],raw['y'],raw['z']],source['source_frame'],source['source_timestamp'],z['transform'],4,bps.index(source['blueprint']),digest)
class Proof:
    def __init__(self,lib,packet,digest,bps,extent,anchor,road,query,threshold,budget):
        begin=time.perf_counter();self.lib=lib;self.packet=packet;self.digest=digest;self.bps=bps;self.old=decode(packet,digest,len(bps));d=self.old
        if d['stride']!=4:raise ValueError('Fixed nested stride4 protocol')
        self.extent=np.asarray(extent,np.float64);self.anchor=np.asarray(anchor,np.float64);self.road=np.ascontiguousarray(road,dtype=np.float64)
        if self.extent.shape!=(3,) or self.anchor.shape!=(3,) or self.road.shape!=(3,3) or not all(np.isfinite(x).all() for x in (self.extent,self.anchor,self.road)) or np.any(self.extent<=0) or np.linalg.norm(self.extent)>10 or not np.allclose(self.road.T@self.road,np.eye(3),rtol=0,atol=1e-6) or len(query)!=2 or not all(math.isfinite(x) for x in query) or not(-12<query[0]<12 and -8<query[1]<8):raise ValueError('Declared geometry')
        self.world=np.ascontiguousarray(d['views'][-1]['points']);self.strides=np.where(np.arange(len(self.world))%4==0,16,4).astype(np.int32);radius=math.ceil(float(np.linalg.norm(self.extent))*1e6);self.ptr=lib.build(self.extent,self.anchor,self.road,np.ascontiguousarray(d['origin']),*query,radius,threshold['numerator'],threshold['denominator'],self.world,self.strides,len(self.world),budget)
        if not self.ptr:raise ValueError('Native input contract')
        self.n=lib.size(self.ptr);self.stat=np.zeros(5);lib.stats(self.ptr,self.stat);self.total_s=time.perf_counter()-begin
    def export(self):
        cells=np.empty((self.n,12));meta=np.empty((self.n,6),np.int64);counts=np.empty((self.n,2,4),np.int64);self.lib.export_nodes(self.ptr,cells,meta,counts);return dict(cells=cells,meta=meta,counts=counts)
    def check(self,packet,incremental=True):
        begin=time.perf_counter();new=decode(packet,self.digest,len(self.bps));old=self.old
        if new['blueprint_index']!=old['blueprint_index'] or new['stride']!=4 or new['original_count']!=old['original_count'] or not np.array_equal(new['matrix'].view(np.uint64),old['matrix'].view(np.uint64)) or new['frame']<=old['frame'] or new['timestamp']<=old['timestamp']:raise ValueError('Cache identity or time mismatch')
        changed=np.any(new['raw_xyz'].view(np.uint32)!=old['raw_xyz'].view(np.uint32),axis=1);world=np.ascontiguousarray(new['views'][-1]['points']);assert np.array_equal(world[~changed],self.world[~changed]);empty=np.empty((0,3));si=np.empty(0,np.int32)
        oldp=np.ascontiguousarray(self.world[changed]) if incremental else empty;olds=np.ascontiguousarray(self.strides[changed]) if incremental else si;newp=np.ascontiguousarray(world[changed]) if incremental else world;news=np.ascontiguousarray(self.strides[changed]) if incremental else self.strides
        counts=np.zeros((self.n,2,4),np.int64);accepted=np.full(self.n,-9,np.int32);stat=np.zeros(5);self.lib.revalidate(self.ptr,oldp,olds,len(oldp),newp,news,len(newp),int(incremental),counts,accepted,stat)
        if np.any(counts<0) or np.any(counts[:,:,1]>counts[:,:,0]) or np.any(counts[:,:,2]>counts[:,:,1]) or np.any(counts[:,:,3]>counts[:,:,0]):raise AssertionError('Invalid delta counts')
        return dict(counts=counts,accepted=accepted,stat=stat,total_s=time.perf_counter()-begin,changed_rays=int(changed.sum()),input_rays=len(world))
    def close(self):
        if self.ptr:self.lib.destroy(self.ptr);self.ptr=None
