import ctypes as C,math,time
import numpy as np
from repair_runtime import library as base_library,decode,F64,I64,I32

def library(path):
 lib=base_library(path);lib.adaptive_repair_proof.argtypes=lib.repair_proof.argtypes+[C.c_int64,C.c_int64,I64];lib.adaptive_repair_proof.restype=C.c_void_p;return lib

def repaired(proof,wire,external_us):
 begin=time.perf_counter();warm=proof.check(wire,True);spent=math.ceil(external_us+(time.perf_counter()-begin)*1e6);lo,hi=map(int,warm['stat'][:2]);margin=5000
 if lo-spent>=margin or hi<=spent:
  receiver=time.perf_counter()-begin;tree=proof.saved_tree;cells=tree['cells'];meta=tree['meta'].copy();counts=warm['counts'];flags=np.where(tree['meta'][:,3]==2,1,0).astype(np.int64);leaf=tree['meta'][:,3]!=1;meta[leaf,3]=np.where(warm['accepted'][leaf]==1,2,0);stat=np.array([lo,hi,0,0,0,0,0,0.]);return dict(cells=cells,meta=meta,counts=counts,flags=flags,witness=np.full(6,np.nan),stat=stat,receiver_s=receiver,baseline_s=warm['total_s'],gate=np.array([1 if lo-spent>=margin else 2,lo,spent],np.int64))
 d=decode(wire,proof.packet,proof.digest,proof.bps);mask=np.ones(len(proof.world),bool);mask[d['indices']]=False;inp=np.ascontiguousarray(proof.world[mask]);ins=np.ascontiguousarray(proof.strides[mask]);newp=d['exact_world'];news=np.ascontiguousarray(proof.strides[d['indices']]);fixed=math.ceil(external_us+(time.perf_counter()-begin)*1e6);gate=np.zeros(3,np.int64);ptr=proof.lib.adaptive_repair_proof(proof.ptr,warm['counts'],warm['accepted'],inp,ins,len(inp),newp,news,len(newp),4096,fixed,margin,gate)
 if not ptr:raise ValueError('Adaptive repair failed')
 n=proof.lib.size(ptr);flags=np.empty(n,np.int64);stat=np.zeros(8);witness=np.full(6,np.nan);proof.lib.repair_info(ptr,flags,stat,witness);receiver=time.perf_counter()-begin;cells=np.empty((n,12));meta=np.empty((n,6),np.int64);counts=np.empty((n,2,4),np.int64);proof.lib.export_nodes(ptr,cells,meta,counts);proof.lib.repair_destroy(ptr);assert stat[0]>=lo and stat[0]<=stat[1];return dict(cells=cells,meta=meta,counts=counts,flags=flags,witness=witness,stat=stat,receiver_s=receiver,baseline_s=warm['total_s'],gate=gate)
