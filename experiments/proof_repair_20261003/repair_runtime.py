import ctypes as C,importlib.util,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'experiments/tube_evidence_20261003'))
spec=importlib.util.spec_from_file_location('tube_implementation',ROOT/'experiments/tube_evidence_20261003/runtime.py');tube=importlib.util.module_from_spec(spec);spec.loader.exec_module(tube)
from codec import decode,decode_full
F64,I64,I32=tube.F64,tube.I64,tube.I32

def library(path):
 lib=tube.library(path);lib.restore_proof.argtypes=[F64,F64,F64,F64,C.c_double,C.c_double,C.c_int64,C.c_int64,C.c_int64,C.c_double,F64,I64,I64,C.c_int];lib.restore_proof.restype=C.c_void_p;lib.repair_proof.argtypes=[C.c_void_p,I64,I32,F64,I32,C.c_int,F64,I32,C.c_int,C.c_int];lib.repair_proof.restype=C.c_void_p;lib.repair_info.argtypes=[C.c_void_p,I64,F64,F64];lib.repair_destroy.argtypes=[C.c_void_p];return lib
class Proof(tube.Proof):
 def __init__(self,lib,packet,digest,bps,source,query,threshold,radius_um,tree):
  t=time.perf_counter();self.lib=lib;self.packet=packet;self.digest=digest;self.bps=bps;self.radius_um=radius_um;self.old=decode_full(packet,digest,len(bps));self.world=np.ascontiguousarray(self.old['views'][-1]['points']);self.strides=np.where(np.arange(len(self.world))%4==0,16,4).astype(np.int32);ext=np.asarray(source['extent'],np.float64);self.ptr=lib.restore_proof(ext,np.asarray(source['anchor'],np.float64),np.ascontiguousarray(source['road_rotation'],dtype=np.float64),np.ascontiguousarray(self.old['origin']),*query,int(np.ceil(np.linalg.norm(ext)*1e6)),threshold['numerator'],threshold['denominator'],radius_um/1e6,np.ascontiguousarray(tree['cells']),np.ascontiguousarray(tree['meta']),np.ascontiguousarray(tree['counts']),len(tree['cells']))
  if not self.ptr:raise ValueError('Restore failed')
  self.n=lib.size(self.ptr);self.restore_s=time.perf_counter()-t
 def repaired(self,wire,budget):
  begin=time.perf_counter();warm=self.check(wire,True);d=decode(wire,self.packet,self.digest,self.bps);mask=np.ones(len(self.world),bool);mask[d['indices']]=False;inp=np.ascontiguousarray(self.world[mask]);ins=np.ascontiguousarray(self.strides[mask]);newp=d['exact_world'];news=np.ascontiguousarray(self.strides[d['indices']]);ptr=self.lib.repair_proof(self.ptr,warm['counts'],warm['accepted'],inp,ins,len(inp),newp,news,len(newp),budget)
  if not ptr:raise ValueError('Repair failed')
  n=self.lib.size(ptr);flags=np.empty(n,np.int64);stat=np.zeros(8);witness=np.full(6,np.nan);self.lib.repair_info(ptr,flags,stat,witness);seconds=time.perf_counter()-begin
  # Export is audit logging; timed interval already contains clone, queues and search.
  cells=np.empty((n,12));meta=np.empty((n,6),np.int64);counts=np.empty((n,2,4),np.int64);self.lib.export_nodes(ptr,cells,meta,counts);self.lib.repair_destroy(ptr)
  assert int(stat[0])>=int(warm['stat'][0]) and int(stat[0])<=int(stat[1]);return dict(cells=cells,meta=meta,counts=counts,flags=flags,stat=stat,witness=witness,receiver_s=seconds,baseline_s=warm['total_s'],baseline_lower_us=int(warm['stat'][0]))
