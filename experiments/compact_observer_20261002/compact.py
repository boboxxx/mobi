"""Established exact caches/temporal dictionary plus conservative local grids."""
import copy,ctypes,functools,hashlib,json,math,os,sys,zlib
from dataclasses import replace
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'set_observer_20261002'))
import observer
body=observer.body;base=observer.base;stream=observer.stream
MAGIC=b'MOBICTD1\0'
LIMIT=base.MAX_BYTES


def integer(x):return type(x) is int and abs(x)<=10**15


def normalize(raw):
    if not isinstance(raw,dict) or set(raw)!={'payload','sha256'}:raise ValueError('Raw schema')
    p=raw['payload']
    if not isinstance(p,dict) or set(p)!={'version','scope','contract','profiles','reference_us','horizon_us','sequence','origins','rays'}:raise ValueError('Payload schema')
    if any(not integer(p[k]) for k in ['reference_us','horizon_us','sequence']):raise ValueError('Time metadata')
    if not isinstance(p['rays'],list) or not 1<=len(p['rays'])<=body.MAX_RAYS or any(not isinstance(r,list) or len(r)!=5 or any(not integer(x) for x in r) for r in p['rays']):raise ValueError('Rays')
    q={k:v for k,v in p.items() if k not in ['reference_us','horizon_us','sequence']}
    q['rays']=[r[:4]+[p['reference_us']-r[4]] for r in p['rays']]
    return q


def encode(packet):
    if not isinstance(packet,dict) or set(packet)!={'kind','dynamics','anchor','steps'} or not isinstance(packet['steps'],list) or not 1<=len(packet['steps'])<=base.MAX_STEPS:raise ValueError('Bundle schema')
    if len(body.canonical(packet))>LIMIT:raise ValueError('Original bound')
    templates=[];keys={};steps=[]
    for raw in packet['steps']:
        q=normalize(raw);key=body.canonical(q)
        if key not in keys:keys[key]=len(templates);templates.append(q)
        p=raw['payload'];steps.append([keys[key],p['reference_us'],p['horizon_us'],p['sequence'],raw['sha256']])
    header={k:packet[k] for k in ['kind','dynamics','anchor']}
    data=body.canonical(dict(version=1,header=header,templates=templates,steps=steps))
    if len(data)>LIMIT:raise ValueError('Dictionary bound')
    result=MAGIC+zlib.compress(data,1)
    if len(result)>LIMIT:raise ValueError('Wire bound')
    return result


def decode(data):
    if not isinstance(data,bytes) or len(data)>LIMIT or data[:len(MAGIC)]!=MAGIC:raise ValueError('Transport')
    z=zlib.decompressobj();decoded=z.decompress(data[len(MAGIC):],LIMIT+1)
    if len(decoded)>LIMIT or not z.eof or z.unused_data or z.unconsumed_tail:raise ValueError('Expansion/trailing/incomplete')
    b=json.loads(decoded)
    if not isinstance(b,dict) or set(b)!={'version','header','templates','steps'} or type(b['version']) is not int or b['version']!=1:raise ValueError('Dictionary schema')
    if not isinstance(b['header'],dict) or set(b['header'])!={'kind','dynamics','anchor'}:raise ValueError('Header')
    templates=b['templates'];steps=b['steps']
    if not isinstance(templates,list) or not 1<=len(templates)<=base.MAX_STEPS or not isinstance(steps,list) or not 1<=len(steps)<=base.MAX_STEPS:raise ValueError('Count')
    for q in templates:
        if not isinstance(q,dict) or set(q)!={'version','scope','contract','profiles','origins','rays'}:raise ValueError('Template schema')
        if not isinstance(q['rays'],list) or not 1<=len(q['rays'])<=body.MAX_RAYS or any(not isinstance(r,list) or len(r)!=5 or any(not integer(x) for x in r) for r in q['rays']):raise ValueError('Template rays')
        if not isinstance(q['origins'],list) or not 1<=len(q['origins'])<=body.MAX_RAYS:raise ValueError('Template origins')
    result=dict(b['header']);result['steps']=[];expanded=len(body.canonical(result))
    for row in steps:
        if not isinstance(row,list) or len(row)!=5 or any(not integer(x) for x in row[:4]) or not 0<=row[0]<len(templates) or not isinstance(row[4],str) or len(row[4])!=64:raise ValueError('Step metadata')
        tid,ref,horizon,seq,checksum=row;q=templates[tid]
        p=dict(q,reference_us=ref,horizon_us=horizon,sequence=seq)
        p['rays']=[r[:4]+[ref-r[4]] for r in q['rays']]
        raw=dict(payload=p,sha256=checksum);expanded+=len(body.canonical(raw))+1
        if expanded>LIMIT:raise ValueError('Reconstructed bound')
        result['steps'].append(raw)
    if len(body.canonical(result))>LIMIT:raise ValueError('Final bound')
    return result


def geometry_key(o,r,ref):
    return o.tobytes(),r[:,:4].tobytes(),(ref-r[:,4]).tobytes()


@functools.lru_cache(maxsize=1)
def library():
    f=ctypes.CDLL(os.environ['MOBI_PROPAGATE_LIBRARY']).tile_propagate
    b=np.ctypeslib.ndpointer(dtype=np.uint8,ndim=1,flags='C_CONTIGUOUS')
    f.argtypes=[b,ctypes.c_int64,ctypes.c_double,ctypes.c_double,b];f.restype=ctypes.c_int
    return f


def propagate(possible,step,distance):
    if possible.ndim!=2 or possible.shape[0]!=possible.shape[1] or possible.dtype!=bool:raise ValueError('State')
    src=np.ascontiguousarray(possible,dtype=np.uint8).ravel();out=np.empty_like(src)
    if library()(src,len(possible),step,distance,out):raise ValueError('Propagation contract')
    return out.reshape(possible.shape).astype(bool)


class FixedReceiver(stream.Receiver):
    def inspect(self,transport):
        b=decode(transport)
        if b['kind']!='center-continuity-v1' or b['dynamics']!='observation-speed-age-v1':raise ValueError('Type')
        anchor=self._anchors[b['anchor']];end,previous,seq=anchor.endpoint_us,anchor.reference_us,anchor.sequence
        verified={};stats=dict(cover_hits=0,cover_misses=0)
        for raw in b['steps']:
            p,o,r=body.decode(body.canonical(raw),self.profiles,anchor.scope,self.contract);ref=p['reference_us'];h=p['horizon_us']
            if not previous<ref<end or p['sequence']<=seq or ref+h<=end:raise ValueError('Temporal cover')
            key=(geometry_key(o,r,ref),h)
            if key not in verified:
                v=body.projections(o,r,ref,self.profiles,anchor.scope,self.contract)
                c={n:base.collar(profile,anchor,h/body.TIME_SCALE,r,ref) for n,profile in self.profiles.items()}
                verified[key]=stream.cover(v,self.profiles,anchor.motion,c,len(r));stats['cover_misses']+=1
            else:stats['cover_hits']+=1
            if not verified[key]:raise ValueError('Unexcluded collar')
            end,previous,seq=ref+h,ref,p['sequence']
        return dict(reference_us=previous,endpoint_us=end,sequence=seq,horizon_us=end-previous,steps=len(b['steps']),anchor=anchor.identity,cache=stats)


class PositionReceiver(observer.Receiver):
    def __init__(self,profiles,contract,windows,factor):
        if type(factor) is not int or factor not in [1,2] or set(windows)!=set(profiles):raise ValueError('Grid contract')
        super().__init__(profiles,contract);self.factor=factor;self.grid_profiles={};self.offsets={}
        for n,p in profiles.items():
            d=windows[n];offset=(p.domain-d)/p.step;size=2*d/p.step
            if not math.isfinite(d) or not 0<d<=p.domain or abs(offset-round(offset))>1e-8 or abs(size-round(size))>1e-8:raise ValueError('Aligned computational window')
            self.grid_profiles[n]=replace(p,domain=d,step=p.step/factor);self.offsets[n]=(round(offset),round(size))

    def register(self,legacy,blob,scope,motion):
        anchor=super().register(legacy,blob,scope,motion);coarse=self._states[anchor.identity]
        p,o,r=body.decode(body.canonical(json.loads(blob)['raw']),self.profiles,scope,self.contract)
        v=body.projections(o,r,p['reference_us'],self.profiles,scope,self.contract);possible={};effective={}
        for n,g in self.grid_profiles.items():
            offset,size=self.offsets[n];mask=coarse.possible[n][offset:offset+size,offset:offset+size]
            mask=np.repeat(np.repeat(mask,self.factor,axis=0),self.factor,axis=1)
            possible[n]=mask&~observer.exclusion(v[n],g,motion);effective[n]=base.reference_speed(g,r,p['reference_us'])
        self._states[anchor.identity]=observer.State(anchor.reference_us,anchor.sequence,possible,effective)
        return anchor

    def rebuild(self,transport):
        b=decode(transport)
        if b['kind']!='position-observations-v1' or b['dynamics']!='observation-speed-age-v1':raise ValueError('Type')
        anchor=self._anchors[b['anchor']];state=self._states[anchor.identity]
        masks={};updates={};stats=dict(mask_hits=0,mask_misses=0,update_hits=0,update_misses=0)
        for raw in b['steps']:
            p,o,r=body.decode(body.canonical(raw),self.profiles,anchor.scope,self.contract);ref=p['reference_us']
            if ref<=state.reference_us or p['sequence']<=state.sequence:raise ValueError('Order')
            key=geometry_key(o,r,ref)
            if key not in masks:
                v=body.projections(o,r,ref,self.profiles,anchor.scope,self.contract)
                masks[key]={n:observer.exclusion(v[n],g,anchor.motion) for n,g in self.grid_profiles.items()}
                for x in masks[key].values():x.setflags(write=False)
                stats['mask_misses']+=1
            else:stats['mask_hits']+=1
            dt=(ref-state.reference_us)/1e6;possible={};effective={}
            for n,g in self.grid_profiles.items():
                distance=body.travel(dt,state.effective_profiles[n]);ukey=(n,key,distance,state.possible[n].tobytes())
                if ukey not in updates:
                    updates[ukey]=propagate(state.possible[n],g.step,distance)&~masks[key][n]
                    updates[ukey].setflags(write=False);stats['update_misses']+=1
                else:stats['update_hits']+=1
                possible[n]=updates[ukey];effective[n]=base.reference_speed(g,r,ref)
            state=observer.State(ref,p['sequence'],possible,effective)
        classes={n:observer.frontier(state.possible[n],state.effective_profiles[n],anchor.motion) for n in self.profiles};h=min(x['horizon_us'] for x in classes.values())
        return dict(reference_us=state.reference_us,endpoint_us=state.reference_us+h,sequence=state.sequence,horizon_us=h,
                    classes=classes,steps=len(b['steps']),anchor=anchor.identity,grid_factor=self.factor,windows={n:g.domain for n,g in self.grid_profiles.items()},cache=stats),state
