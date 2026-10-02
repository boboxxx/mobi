"""Lossless bounded transport and exact lattice cover; same continuity semantics."""
import ctypes, functools, json, os, sys, zlib
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'continuity_recovery_20261002'))
import continuity as base
body=base.body
MAGIC=b'MOBICV1Z\0'


@functools.lru_cache(maxsize=1)
def library():
    f=ctypes.CDLL(os.environ['MOBI_RASTER_LIBRARY']).raster_cover
    i=np.ctypeslib.ndpointer(dtype=np.int64,ndim=1,flags='C_CONTIGUOUS')
    d=np.ctypeslib.ndpointer(dtype=np.float64,ndim=1,flags='C_CONTIGUOUS')
    f.argtypes=[ctypes.c_int64,ctypes.c_int64,ctypes.c_int64,d,i,i,
                ctypes.c_int64,i,i,d,d,ctypes.c_int64,i,ctypes.c_int,i]
    f.restype=ctypes.c_int64;return f


def cover(results,profiles,motion,cells,nrays,select=False):
    maps=[];w=[];ids=[];classes=[];dims=[];starts=[];axes=[];steps=[];offset=0;start=0
    for k,(n,p) in enumerate(profiles.items()):
        c=cells[n]
        if c is None:return None if select else False
        size=round(2*p.domain/p.step);axis=-p.domain+.5*p.step
        m=np.full(size*size,-1,dtype=np.int64)
        loc=np.rint((c-axis)/p.step).astype(np.int64)
        if len(loc) and (np.any(loc<0) or np.any(loc>=size)):raise ValueError('Off-grid cells')
        m[loc[:,0]*size+loc[:,1]]=offset+np.arange(len(c));maps.append(m)
        offset+=len(c);dims.append(size);starts.append(start);start+=len(m);axes.append(p.domain);steps.append(p.step)
        v=results[n];xy=v['witnesses']@body.rotation(motion.yaw)
        radii=p.r_min-v['error']-p.step/np.sqrt(2)-1e-9
        w.append(np.column_stack([xy,radii]));ids.append(v['ray_indices']);classes.append(np.full(len(xy),k,dtype=np.int64))
    args=[np.concatenate(w).ravel(),np.concatenate(ids),np.concatenate(classes),
          np.asarray(dims),np.asarray(starts),np.asarray(axes),np.asarray(steps),np.concatenate(maps)]
    args=[np.ascontiguousarray(x,dtype=np.float64 if j in [0,5,6] else np.int64) for j,x in enumerate(args)]
    output=np.empty(nrays,dtype=np.int64)
    count=library()(nrays,offset,len(args[1]),*args[:3],len(profiles),*args[3:7],len(args[7]),args[7],int(select),output)
    if count==-2:return None if select else False
    if count<0:raise ValueError('Invalid bounded raster cover')
    return output[:count] if select else True


def step(points,origin,observed,reference,profiles,contract,anchor,horizon,sequence,full=False):
    if not base.fixed(anchor.motion):raise ValueError('Only fixed region')
    o,r,ref=body.encode_source(points,origin,observed,reference)
    v=base.shared_projections(o,r,ref,profiles,anchor.scope,contract)
    cells={n:(body.required(base.reference_speed(p,r,ref),anchor.motion,horizon) if full else
                base.collar(p,anchor,horizon,r,ref)) for n,p in profiles.items()}
    chosen=cover(v,profiles,anchor.motion,cells,len(r),True)
    if chosen is None:return None
    chosen=np.unique(np.append(chosen,int(np.argmax(r[:,4]))))
    if not len(chosen) or len(chosen)>body.MAX_RAYS:return None
    return json.loads(body.serialize(o,r[chosen],ref,profiles,anchor.scope,contract,horizon,sequence))


def encode(blob):
    if not isinstance(blob,bytes) or len(blob)>base.MAX_BYTES:raise ValueError('Bundle bound')
    out=MAGIC+zlib.compress(blob,1)
    if len(out)>base.MAX_BYTES:raise ValueError('Transport bound')
    return out


def decode(blob):
    if not isinstance(blob,bytes) or len(blob)>base.MAX_BYTES or not blob.startswith(MAGIC):raise ValueError('Wrong transport')
    d=zlib.decompressobj();out=d.decompress(blob[len(MAGIC):],base.MAX_BYTES+1)
    if len(out)>base.MAX_BYTES or not d.eof or d.unused_data or d.unconsumed_tail:raise ValueError('Unbounded/incomplete/trailing transport')
    return out


class Receiver(base.Receiver):
    def inspect(self,transport):
        blob=decode(transport);b=json.loads(blob)
        if set(b)!={'kind','dynamics','anchor','steps'} or b['kind']!='center-continuity-v1' or b['dynamics']!='observation-speed-age-v1':raise ValueError('Wrong typed packet')
        anchor=self._anchors[b['anchor']]
        if not isinstance(b['steps'],list) or not 1<=len(b['steps'])<=base.MAX_STEPS:raise ValueError('Invalid step count')
        end,previous,sequence=anchor.endpoint_us,anchor.reference_us,anchor.sequence
        for raw in b['steps']:
            p,o,r=body.decode(body.canonical(raw),self.profiles,anchor.scope,self.contract)
            ref,seq,h=p['reference_us'],p['sequence'],p['horizon_us']
            if not previous<ref<end or seq<=sequence or ref+h<=end:raise ValueError('Temporal gap')
            v=body.projections(o,r,ref,self.profiles,anchor.scope,self.contract)
            cells={n:base.collar(profile,anchor,h/body.TIME_SCALE,r,ref) for n,profile in self.profiles.items()}
            if not cover(v,self.profiles,anchor.motion,cells,len(r)):raise ValueError('Unexcluded collar')
            end,previous,sequence=ref+h,ref,seq
        return dict(reference_us=previous,endpoint_us=end,sequence=sequence,steps=len(b['steps']),anchor=anchor.identity)

    def accept(self,blob,now,execution=0.):
        try:return super().accept(blob,now,execution)
        except zlib.error:return False
