"""Version-two joint raw-ray proof with receiver-side error recomputation.

The source must be physically trustworthy. SHA-256 detects corruption only;
this module does not authenticate sensors or establish their error contracts.
"""
from dataclasses import asdict, dataclass
from functools import lru_cache
import hashlib, heapq, json, math, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'visibility_uncertainty_20261001'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'visibility_certificate_20261001'))
from projection import bounded_witnesses
from geometry import Profile,grid,travel

QUANTUM=.001
TIME_SCALE=1000000
MAX_RAYS=8192


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


@dataclass(frozen=True)
class Contract:
    point_error: float=.01
    origin_error: float=.01
    query_error: float=.01
    max_ray_age: float=.2
    error_bin: float=.01

    def __post_init__(self):
        if not all(math.isfinite(x) and x>=0 for x in asdict(self).values()) or self.error_bin<=0:
            raise ValueError('Invalid error contract')


@dataclass(frozen=True)
class Scope:
    episode: str
    frame_id: str
    query: tuple
    plane_z: float

    def __post_init__(self):
        if not self.episode or not self.frame_id or len(self.query)!=2 or not all(math.isfinite(x) for x in (*self.query,self.plane_z)):
            raise ValueError('Invalid scope')


def check_profiles(profiles):
    if not profiles or any(p.error!=0 for p in profiles.values()):
        raise ValueError('Nonempty receiver-required classes with per-ray error required')
    if len({p.query_radius for p in profiles.values()})!=1:
        raise ValueError('All classes must cover the same action disk')


@lru_cache(maxsize=64)
def required(profile,horizon):
    centers,dist=grid(profile.domain,profile.step)
    radius=profile.query_radius+profile.r_max+travel(horizon+profile.clock,profile)
    if radius>=profile.domain:return None
    return centers[dist<=radius]


def encode_source(points,origins,observed_at,reference_at):
    p=np.asarray(points,dtype=float);o=np.broadcast_to(np.asarray(origins,dtype=float),p.shape)
    t=np.broadcast_to(np.asarray(observed_at,dtype=float),(len(p),))
    if p.ndim!=2 or p.shape[1]!=3 or not np.isfinite(p).all() or not np.isfinite(o).all() or not np.isfinite(t).all() or not math.isfinite(reference_at):
        raise ValueError('Invalid raw rays')
    if np.any(t>reference_at) or max(np.max(np.abs(p),initial=0),np.max(np.abs(o),initial=0))>1e6 or np.max(np.abs(t),initial=0)>1e9 or abs(reference_at)>1e9:
        raise ValueError('Unsupported coordinates/times or future rays')
    origins_q,indices=np.unique(np.rint(o/QUANTUM).astype(np.int64),axis=0,return_inverse=True)
    rays=np.column_stack([indices,np.rint(p/QUANTUM).astype(np.int64),np.floor(t*TIME_SCALE).astype(np.int64)])
    return origins_q,rays,int(math.ceil(reference_at*TIME_SCALE))


def projections(origins_q,rays,reference_us,profiles,scope,contract):
    ages=(reference_us-rays[:,4])/TIME_SCALE
    if np.any(ages<0) or np.any(ages>contract.max_ray_age):raise ValueError('Invalid ray ages')
    o=origins_q[rays[:,0]]*QUANTUM;p=rays[:,1:4]*QUANTUM
    outputs={}
    for name,profile in profiles.items():
        result=bounded_witnesses(p,o,scope.query,scope.plane_z,
            contract.point_error+QUANTUM/2,contract.origin_error+QUANTUM/2,contract.query_error,
            ages,profile.speed,profile.acceleration)
        # Encode full uncertainty upward. No sender-supplied error is accepted.
        result['error']=np.ceil(result['error']/contract.error_bin)*contract.error_bin
        outputs[name]=result
    return outputs


def covered(result,profile,horizon):
    cells=required(profile,horizon)
    if cells is None:return False
    missing=np.ones(len(cells),dtype=bool)
    for error in np.unique(result['error']):
        radius=profile.r_min-error-profile.step/math.sqrt(2)-1e-9
        if radius<=0:continue
        indices=np.flatnonzero(missing)
        if not len(indices):return True
        tree=cKDTree(result['witnesses'][result['error']==error])
        near=tree.query(cells[indices],k=1)[0]
        missing[indices[near<radius]]=False
    return not missing.any()


def uniform_errors(result,profile,horizon):
    cells=required(profile,horizon)
    if cells is None:return None
    errors=result['error']
    for candidate in np.unique(errors):
        radius=profile.r_min-candidate-profile.step/math.sqrt(2)-1e-9
        if radius<=0:break
        distances=cKDTree(result['witnesses'][errors<=candidate]).query(cells,k=1)[0]
        if np.all(distances<radius):return np.where(errors<=candidate,candidate,np.inf)
    return None


def serialize(origins_q,rays,reference_us,profiles,scope,contract,horizon,sequence):
    # Compact the origin dictionary after selecting rays.
    used,new_index=np.unique(rays[:,0],return_inverse=True);rays=rays.copy();rays[:,0]=new_index
    payload=dict(version=2,scope=asdict(scope),contract=asdict(contract),profiles={k:asdict(v) for k,v in profiles.items()},
                 reference_us=reference_us,horizon_us=int(math.floor(horizon*TIME_SCALE)),sequence=int(sequence),
                 origins=origins_q[used].tolist(),rays=rays.tolist())
    return canonical(dict(payload=payload,sha256=hashlib.sha256(canonical(payload)).hexdigest()))


def decode(blob,profiles,scope,contract):
    check_profiles(profiles)
    if len(blob)>2_000_000:raise ValueError('Oversized proof')
    env=json.loads(blob);p=env['payload']
    if set(env)!={'payload','sha256'} or hashlib.sha256(canonical(p)).hexdigest()!=env['sha256']:raise ValueError('Checksum')
    if set(p)!={'version','scope','contract','profiles','reference_us','horizon_us','sequence','origins','rays'} or p['version']!=2:raise ValueError('Schema')
    for name,expected in [('scope',asdict(scope)),('contract',asdict(contract)),('profiles',{k:asdict(v) for k,v in profiles.items()})]:
        if canonical(p[name])!=canonical(expected):raise ValueError('Receiver contract mismatch')
    for k in ['reference_us','horizon_us','sequence']:
        if type(p[k]) is not int or abs(p[k])>10**15:raise ValueError('Invalid integer metadata')
    if p['horizon_us']<=0 or p['sequence']<0:raise ValueError('Invalid horizon/sequence')
    if not isinstance(p['rays'],list) or not 0<len(p['rays'])<=MAX_RAYS:raise ValueError('Ray count')
    if not isinstance(p['origins'],list) or not 0<len(p['origins'])<=MAX_RAYS:raise ValueError('Origin count')
    for rows,width in [(p['rays'],5),(p['origins'],3)]:
        if any(not isinstance(r,list) or len(r)!=width or any(type(x) is not int or abs(x)>10**15 for x in r) for r in rows):raise ValueError('Integer ray encoding')
    origins=np.asarray(p['origins'],dtype=np.int64);rays=np.asarray(p['rays'],dtype=np.int64)
    if np.any(rays[:,0]<0) or np.any(rays[:,0]>=len(origins)):raise ValueError('Origin index')
    if np.max(np.abs(origins))>1e9 or np.max(np.abs(rays[:,1:4]))>1e9:raise ValueError('Coordinate range')
    return p,origins,rays


def verify(blob,profiles,scope,contract,now,execution_s,min_sequence=0):
    try:
        if not math.isfinite(now) or not math.isfinite(execution_s) or execution_s<0:return False
        p,o,r=decode(blob,profiles,scope,contract)
        reference=p['reference_us']/TIME_SCALE;horizon=p['horizon_us']/TIME_SCALE
        if p['sequence']<min_sequence or reference>now or now+execution_s>=reference+horizon:return False
        results=projections(o,r,p['reference_us'],profiles,scope,contract)
        return all(covered(results[name],profile,horizon) for name,profile in profiles.items())
    except (ValueError,TypeError,KeyError,OverflowError,IndexError):return False


def pack(points,origins,observed_at,reference_at,profiles,scope,contract,horizon=.2,sequence=0,mode='heterogeneous'):
    check_profiles(profiles)
    if not math.isfinite(horizon) or horizon<=0 or type(sequence) is not int or sequence<0 or mode not in ['heterogeneous','uniform']:raise ValueError('Invalid request')
    o,r,ref=encode_source(points,origins,observed_at,reference_at)
    results=projections(o,r,ref,profiles,scope,contract)
    if not all(covered(results[n],p,horizon) for n,p in profiles.items()):return None
    neighborhoods=[[] for _ in r];offset=0
    for name,profile in profiles.items():
        result=results[name];cells=required(profile,horizon);errors=result['error'].copy()
        if mode=='uniform':
            errors=uniform_errors(result,profile,horizon)
            if errors is None:return None
        radius=profile.r_min-errors-profile.step/math.sqrt(2)-1e-9;usable=radius>0
        found=cKDTree(cells).query_ball_point(result['witnesses'][usable],radius[usable])
        for ray,c in zip(result['ray_indices'][usable],found):neighborhoods[ray].extend(offset+x for x in c)
        offset+=len(cells)
    inverted=[[] for _ in range(offset)]
    for i,cells in enumerate(neighborhoods):
        for cell in cells:inverted[cell].append(i)
    if any(not x for x in inverted):return None
    gains=[len(x) for x in neighborhoods];heap=[(-g,i) for i,g in enumerate(gains) if g];heapq.heapify(heap)
    uncovered=np.ones(offset,dtype=bool);selected=[]
    while uncovered.any():
        while heap:
            ng,i=heapq.heappop(heap)
            if -ng==gains[i]:break
        else:return None
        if not gains[i] or len(selected)>=MAX_RAYS:return None
        selected.append(i);changed=set()
        for cell in neighborhoods[i]:
            if not uncovered[cell]:continue
            uncovered[cell]=False
            for other in inverted[cell]:gains[other]-=1;changed.add(other)
        for other in changed:
            if gains[other]>0:heapq.heappush(heap,(-gains[other],other))
    blob=serialize(o,r[selected],ref,profiles,scope,contract,horizon,sequence)
    return blob if verify(blob,profiles,scope,contract,ref/TIME_SCALE,0) else None


def renew(template,points,origins,observed_at,reference_at,profiles,scope,contract,sequence,mode='heterogeneous'):
    """Only template support locations are reused; all new rays are current."""
    try:
        if mode not in ['heterogeneous','uniform'] or type(sequence) is not int:return None
        p,old_o,old_r=decode(template,profiles,scope,contract)
        if sequence<=p['sequence'] or reference_at<=p['reference_us']/TIME_SCALE:return None
        old=projections(old_o,old_r,p['reference_us'],profiles,scope,contract)
        o,r,ref=encode_source(points,origins,observed_at,reference_at)
        current=projections(o,r,ref,profiles,scope,contract);chosen=set()
        for name in profiles:
            if not len(current[name]['witnesses']):return None
            idx=cKDTree(current[name]['witnesses']).query(old[name]['witnesses'],k=1)[1]
            chosen.update(int(x) for x in current[name]['ray_indices'][idx])
        selected=r[sorted(chosen)];horizon=p['horizon_us']/TIME_SCALE
        if mode=='uniform':
            actual=projections(o,selected,ref,profiles,scope,contract)
            if any(uniform_errors(actual[n],profile,horizon) is None for n,profile in profiles.items()):return None
        blob=serialize(o,selected,ref,profiles,scope,contract,horizon,sequence)
        return blob if verify(blob,profiles,scope,contract,ref/TIME_SCALE,0) else None
    except (ValueError,TypeError,KeyError,OverflowError,IndexError):return None
