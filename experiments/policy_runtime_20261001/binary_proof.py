"""Lossless integer transport of the existing conditional policy proof.

20 bytes per ray: origin index, three coordinates, age in microseconds.
This changes serialization only, not uncertainty, geometry or deadlines.
Checksum is corruption detection; sensor authentication remains external.
"""
from dataclasses import asdict
from fractions import Fraction
import hashlib,json,math,struct
import numpy as np
from incremental import pp,Verifier
from proof import check_profiles

PREFIX=struct.Struct('>4sIHH')
RAY_DTYPE=np.dtype([('origin','<u4'),('xyz','<i4',(3,)),('age','<i4')])


def encode(o,r,ref,profiles,scope,contract,policy,speed,yaw,horizon,sequence):
    if not 0<len(o)<=pp.MAX_RAYS or not 0<len(r)<=pp.MAX_RAYS:raise ValueError('Count')
    if o.dtype!=np.int64 or r.dtype!=np.int64 or o.shape[1:]!=(3,) or r.shape[1:]!=(5,):raise ValueError('Integer arrays')
    if np.max(np.abs(o))>10**9 or np.max(np.abs(r[:,1:4]))>10**9 or np.any(r[:,0]<0) or np.any(r[:,0]>=len(o)):raise ValueError('Coordinates')
    age=ref-r[:,4]
    if np.any(age<0) or np.any(age>2**31-1):raise ValueError('Age range')
    used,indices=np.unique(r[:,0],return_inverse=True);o=o[used]
    header=dict(kind='policy-evidence-binary-v1',policy=asdict(policy),speed=speed,yaw=yaw,version=2,scope=asdict(scope),contract=asdict(contract),profiles={k:asdict(v) for k,v in profiles.items()},reference_us=ref,horizon_us=int(math.floor(horizon*pp.TIME_SCALE)),sequence=sequence)
    h=pp.canonical(header);rays=np.empty(len(r),dtype=RAY_DTYPE);rays['origin']=indices;rays['xyz']=r[:,1:4];rays['age']=age
    wire=PREFIX.pack(b'PVX1',len(h),len(o),len(r))+h+o.astype('<i4').tobytes()+rays.tobytes()
    return wire+hashlib.sha256(wire).digest()


def decode(blob,profiles,scope,contract,policy,speed,yaw):
    check_profiles(profiles)
    if len(blob)<PREFIX.size+32 or len(blob)>2_100_000:raise ValueError('Packet size')
    magic,header_size,norigin,nray=PREFIX.unpack_from(blob)
    if magic!=b'PVX1' or not 0<header_size<=16384 or not 0<norigin<=pp.MAX_RAYS or not 0<nray<=pp.MAX_RAYS:raise ValueError('Prefix')
    size=PREFIX.size+header_size+norigin*12+nray*RAY_DTYPE.itemsize+32
    if len(blob)!=size or hashlib.sha256(blob[:-32]).digest()!=blob[-32:]:raise ValueError('Size/checksum')
    header=json.loads(blob[PREFIX.size:PREFIX.size+header_size])
    if set(header)!={'kind','policy','speed','yaw','version','scope','contract','profiles','reference_us','horizon_us','sequence'} or header['kind']!='policy-evidence-binary-v1' or type(header['version']) is not int or header['version']!=2:raise ValueError('Schema')
    for name,expected in [('policy',asdict(policy)),('scope',asdict(scope)),('contract',asdict(contract)),('profiles',{k:asdict(v) for k,v in profiles.items()})]:
        if pp.canonical(header[name])!=pp.canonical(expected):raise ValueError('Contract mismatch')
    for name,expected in [('speed',speed),('yaw',yaw)]:
        if type(header[name]) not in (int,float) or not math.isfinite(header[name]) or header[name]!=expected:raise ValueError('State mismatch')
    for name in ['reference_us','horizon_us','sequence']:
        if type(header[name]) is not int or abs(header[name])>10**15:raise ValueError('Metadata range')
    if header['horizon_us']<=0 or header['sequence']<0:raise ValueError('Metadata sign')
    offset=PREFIX.size+header_size
    o=np.frombuffer(blob,dtype='<i4',count=norigin*3,offset=offset).reshape(-1,3).astype(np.int64)
    encoded=np.frombuffer(blob,dtype=RAY_DTYPE,count=nray,offset=offset+norigin*12)
    r=np.empty((nray,5),dtype=np.int64);r[:,0]=encoded['origin'];r[:,1:4]=encoded['xyz'];r[:,4]=header['reference_us']-encoded['age'].astype(np.int64)
    if np.any(r[:,0]>=norigin) or np.max(np.abs(o))>10**9 or np.max(np.abs(r[:,1:4]))>10**9 or np.max(np.abs(r[:,4]))>10**15:raise ValueError('Ray range')
    if np.any(encoded['age']<0) or np.any(encoded['age']/pp.TIME_SCALE>contract.max_ray_age):raise ValueError('Ray age')
    return header,o,r


class BinaryVerifier:
    def __init__(self,hints=True):self.hints=hints;self.cover=Verifier()

    def verify(self,blob,profiles,scope,contract,policy,speed,yaw,now,min_sequence=0):
        try:
            if not math.isfinite(now) or len({p.clock for p in profiles.values()})!=1:return False
            p,o,r=decode(blob,profiles,scope,contract,policy,speed,yaw)
            exact_now=Fraction.from_float(float(now))*pp.TIME_SCALE;receipt=math.ceil(exact_now)
            if p['sequence']<min_sequence or exact_now<p['reference_us'] or receipt>=p['reference_us']+p['horizon_us']:return False
            res=pp.projections(o,r,p['reference_us'],profiles,scope,contract)
            for name,profile in profiles.items():
                args=(res[name],profile,policy,speed,yaw,p['horizon_us']/pp.TIME_SCALE)
                if not (self.cover.covered(*args) if self.hints else pp.coverage(*args)[0]):return False
            return True
        except (ValueError,TypeError,KeyError,IndexError,OverflowError,struct.error):return False


def timing_after_verified(blob,policy,speed,now):
    """Timing-only helper after verification of these exact immutable bytes."""
    try:
        _,n,_,_=PREFIX.unpack_from(blob);p=json.loads(blob[PREFIX.size:PREFIX.size+n]);exact=Fraction.from_float(float(now))*pp.TIME_SCALE
        if exact<p['reference_us']:return False
        receipt=math.ceil(exact);duration=pp.stop_duration(speed,(receipt-p['reference_us'])/pp.TIME_SCALE,policy)
        return receipt+math.ceil(Fraction.from_float(float(duration))*pp.TIME_SCALE)<p['reference_us']+p['horizon_us']
    except (ValueError,TypeError,KeyError,OverflowError,struct.error):return False
