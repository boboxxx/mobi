"""Conditional swept-body evidence with explicit, expiring receiver history.

A bootstrap external-free region is an explicit INITIAL CONDITION, not inferred
from an empty detection list. No expired region may seed a new certificate.
The same geometry covers the full body, its motion, and obstacle reachability.
"""
from dataclasses import dataclass,asdict
from functools import lru_cache
from pathlib import Path
import hashlib,json,math,sys
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ray_proof_v2_20261001'))
from proof import Contract,Scope,Profile,canonical,decode,serialize,projections,TIME_SCALE,MAX_RAYS
from optimized import encode_source
from geometry import grid,travel


@dataclass(frozen=True)
class Motion:
    half_length: float=2.0
    half_width: float=1.0
    yaw: float=0.
    vx: float=0.  # world-frame measured ego velocity, bounded by the caller contract
    vy: float=0.
    acceleration: float=3.
    yaw_rate: float=.2
    pose_error: float=.03  # radial body registration allowance

    def __post_init__(self):
        if not all(math.isfinite(x) for x in asdict(self).values()):raise ValueError('Nonfinite motion')
        if min(self.half_length,self.half_width)<=0 or min(self.acceleration,self.yaw_rate,self.pose_error)<0:raise ValueError('Invalid motion')


@dataclass(frozen=True)
class Region:
    center: tuple
    yaw: float
    low: tuple
    high: tuple
    margin: float
    established: float
    expires: float
    identity: str
    episode: str

    def __post_init__(self):
        values=(*self.center,self.yaw,*self.low,*self.high,self.margin,self.established,self.expires)
        if len(self.center)!=2 or len(self.low)!=2 or len(self.high)!=2 or not all(math.isfinite(x) for x in values):raise ValueError('Invalid region')
        if self.margin<0 or self.established>self.expires or any(a>=b for a,b in zip(self.low,self.high)) or not self.identity or not self.episode:raise ValueError('Invalid region bounds')


def rotation(yaw):
    c,s=math.cos(yaw),math.sin(yaw)
    return np.array([[c,-s],[s,c]])


def envelope(motion,horizon,clock):
    t=horizon+clock
    velocity=np.array([motion.vx,motion.vy])@rotation(motion.yaw)
    extent=np.array([motion.half_length,motion.half_width])
    low=-extent+np.minimum(0,velocity*t);high=extent+np.maximum(0,velocity*t)
    turn=2*np.linalg.norm(extent)*math.sin(min(math.pi,motion.yaw_rate*t)/2)
    margin=motion.pose_error+.5*motion.acceleration*t*t+turn
    return low,high,float(margin)


def box_distance(points,low,high):
    return np.linalg.norm(np.maximum(np.maximum(low-points,points-high),0),axis=1)


def prior_covers(cells,scope,motion,prior,profile,reference):
    if prior is None:return np.zeros(len(cells),dtype=bool)
    instant=prior.established==prior.expires==reference
    if prior.episode!=scope.episode or not (instant or prior.established<=reference<prior.expires):raise ValueError('Stale/mismatched prior')
    world=cells@rotation(motion.yaw).T+scope.query
    local=(world-prior.center)@rotation(prior.yaw)
    # Intersecting the opaque core with a known external-free region is impossible.
    d=box_distance(local,np.asarray(prior.low),np.asarray(prior.high))-prior.margin
    return d+profile.step/math.sqrt(2)<profile.r_min-1e-9


@lru_cache(maxsize=64)
def required(profile,motion,horizon):
    if not math.isfinite(horizon) or horizon<=0:raise ValueError('Bad horizon')
    low,high,margin=envelope(motion,horizon,profile.clock)
    inflate=margin+profile.r_max+travel(horizon+profile.clock,profile)
    if np.any(np.maximum(np.abs(low),np.abs(high))+inflate>=profile.domain):return None
    cells,_=grid(profile.domain,profile.step)
    # Superset of every tile touching the expanded action occupancy.
    return cells[box_distance(cells,low,high)<=inflate+profile.step/math.sqrt(2)]


def coverage(result,profile,scope,motion,horizon,prior,reference,select=False):
    cells=required(profile,motion,horizon)
    if cells is None:return False,[]
    missing=~prior_covers(cells,scope,motion,prior,profile,reference);chosen=[]
    w=result['witnesses']@rotation(motion.yaw)
    for error in np.unique(result['error']):
        radius=profile.r_min-error-profile.step/math.sqrt(2)-1e-9
        if radius<=0:continue
        todo=np.flatnonzero(missing)
        if not len(todo):break
        group=np.flatnonzero(result['error']==error)
        d,j=cKDTree(w[group]).query(cells[todo],k=1)
        hit=d<radius;missing[todo[hit]]=False
        if select:chosen.extend(result['ray_indices'][group[j[hit]]].tolist())
    return not missing.any(),chosen


def pack(points,origin,observed,reference,profiles,scope,contract,motion,prior,horizon=.4,sequence=0):
    if len({p.clock for p in profiles.values()})!=1:raise ValueError('Classes need identical clock contract')
    o,r,ref=encode_source(points,origin,observed,reference)
    stamp=ref/TIME_SCALE
    results=projections(o,r,ref,profiles,scope,contract);chosen=set()
    for n,profile in profiles.items():
        ok,ids=coverage(results[n],profile,scope,motion,horizon,prior,stamp,True)
        if not ok:return None
        chosen.update(ids)
    # An empty ray subset may only be supported by a receiver-local prior. For
    # this finite implementation retain one actual ray for the v2 wire schema.
    if not chosen:
        if not len(r):return None
        chosen.add(0)
    if len(chosen)>MAX_RAYS:return None
    raw=json.loads(serialize(o,r[sorted(chosen)],ref,profiles,scope,contract,horizon,sequence))
    packet=dict(kind='body-evidence-v1',motion=asdict(motion),prior=prior.identity if prior else None,raw=raw)
    blob=canonical(packet)
    return blob if verify(blob,profiles,scope,contract,motion,prior,stamp,0) else None


def verify(blob,profiles,scope,contract,motion,prior,now,execution,min_sequence=0):
    try:
        if len(blob)>2_100_000 or not math.isfinite(now) or not math.isfinite(execution) or execution<0:return False
        if len({p.clock for p in profiles.values()})!=1:return False
        packet=json.loads(blob)
        if set(packet)!={'kind','motion','prior','raw'} or packet['kind']!='body-evidence-v1':return False
        if canonical(packet['motion'])!=canonical(asdict(motion)) or packet['prior']!=(prior.identity if prior else None):return False
        p,o,r=decode(canonical(packet['raw']),profiles,scope,contract)
        stamp=p['reference_us']/TIME_SCALE;h=p['horizon_us']/TIME_SCALE
        if p['sequence']<min_sequence or stamp>now or now+execution>=stamp+h:return False
        results=projections(o,r,p['reference_us'],profiles,scope,contract)
        return all(coverage(results[n],profile,scope,motion,h,prior,stamp)[0] for n,profile in profiles.items())
    except (ValueError,TypeError,KeyError,IndexError,OverflowError):return False


def established_region(blob,profiles,scope,contract,motion,prior,now):
    """Derive history only after full receiver validation. Store it locally."""
    if not verify(blob,profiles,scope,contract,motion,prior,now,0):raise ValueError('Cannot establish invalid proof')
    p=json.loads(blob)['raw']['payload'];stamp=p['reference_us']/TIME_SCALE;h=p['horizon_us']/TIME_SCALE
    low,high,margin=envelope(motion,h,max(x.clock for x in profiles.values()))
    # All class requirements must certify the SAME envelope. The current API
    # requires equal clocks; using max with unequal clocks would enlarge a claim.
    if len({x.clock for x in profiles.values()})!=1:raise ValueError('Classes need identical clock contract')
    return Region(tuple(scope.query),motion.yaw,tuple(low),tuple(high),margin,stamp,stamp+h,hashlib.sha256(blob).hexdigest(),scope.episode)


def action_duration(speed,age,acceleration=3.,braking=4.,control=.05,reaction=.02):
    """Time FROM RECEIPT through command interval, reaction and complete braking.

    Braking deceleration is a stipulated lower bound, not measured here. Speed
    may have risen during evidence acquisition/transport (age).
    """
    if not all(math.isfinite(x) and x>=0 for x in [speed,age,acceleration,braking,control,reaction]) or braking<=0:raise ValueError('Bad braking contract')
    return control+reaction+(speed+acceleration*(age+control+reaction))/braking
