"""Free-region leases derived from fully verified current-ray certificates.

The geometry proves absence in a region. The parameters used to construct that
region are not evidence that a vehicle can execute any particular controller.
Actuation containment is checked separately, under explicit external bounds.
"""
from dataclasses import dataclass,asdict
from fractions import Fraction
from pathlib import Path
import hashlib,json,math,sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'policy_runtime_20261001'))
from binary_proof import PREFIX,decode,BinaryVerifier,pp
from tube import Policy,envelope


def ticks(time):
    if not math.isfinite(time):raise ValueError('Nonfinite time')
    return math.ceil(Fraction.from_float(float(time))*pp.TIME_SCALE)


@dataclass(frozen=True)
class FreeRegion:
    identity:str
    reference_us:int
    expires_us:int
    sequence:int
    center:tuple
    yaw:float
    low:tuple
    high:tuple
    margin:float


class Reader:
    def __init__(self,profiles,contract,episode,frame_id):
        self.profiles=profiles;self.contract=contract;self.episode=episode;self.frame_id=frame_id
        self.verifier=BinaryVerifier();self.regions={};self.last_sequence=-1;self.last_reference=-10**15

    def accept(self,blob,scope,now):
        try:
            if scope.episode!=self.episode or scope.frame_id!=self.frame_id:return None
            if len(blob)<PREFIX.size+32 or len(blob)>2_100_000:return None
            _,n,_,_=PREFIX.unpack_from(blob)
            if not 0<n<=16384:return None
            header=json.loads(blob[PREFIX.size:PREFIX.size+n]);shape=Policy(**header['policy']);speed=header['speed'];yaw=header['yaw']
            if not self.verifier.verify(blob,self.profiles,scope,self.contract,shape,speed,yaw,now,self.last_sequence+1):return None
            p,_,_=decode(blob,self.profiles,scope,self.contract,shape,speed,yaw)
            if p['reference_us']<=self.last_reference:return None
            lo,hi,margin=envelope(speed,p['horizon_us']/pp.TIME_SCALE,max(pr.clock for pr in self.profiles.values()),shape)
            identity=hashlib.sha256(blob).hexdigest()
            region=FreeRegion(identity,p['reference_us'],p['reference_us']+p['horizon_us'],p['sequence'],tuple(scope.query),yaw,tuple(lo),tuple(hi),margin)
            self.regions[identity]=region;self.last_sequence=p['sequence'];self.last_reference=p['reference_us']
            self.regions={k:v for k,v in self.regions.items() if v.expires_us>ticks(now)}
            return identity
        except (ValueError,TypeError,KeyError,IndexError,OverflowError):return None


@dataclass(frozen=True)
class State:
    x:float
    y:float
    yaw:float
    speed:float

    def __post_init__(self):
        if not all(math.isfinite(v) for v in asdict(self).values()) or self.speed<0:raise ValueError('Invalid state')


@dataclass(frozen=True)
class Actuation:
    half_length:float=2.
    half_width:float=1.
    command:float=.05
    reaction:float=.02
    traction:float=3.
    braking:float=4.
    yaw_rate:float=.2
    slip:float=.03
    pose_error:float=.03
    speed_error:float=.02
    residual_speed:float=.02

    def __post_init__(self):
        if not all(math.isfinite(v) and v>=0 for v in asdict(self).values()) or min(self.half_length,self.half_width,self.braking,self.command)<=0:raise ValueError('Invalid external actuation contract')


def maneuver(state,bound):
    """Enclose one command followed by complete backup, from CURRENT state.

    Preconditions include bounded forward speed growth until brake activation,
    guaranteed braking thereafter, bounded direction/yaw and terminal drift.
    None is inferred from a message or a finite actuator diagnostic.
    """
    v=state.speed+bound.speed_error;t=bound.command+bound.reaction
    peak=v+bound.traction*t;duration=t+peak/bound.braking
    path=v*t+.5*bound.traction*t*t+peak*peak/(2*bound.braking)
    angle=bound.yaw_rate*duration+bound.slip
    if angle>=math.pi/2:raise ValueError('Direction contract too wide')
    lateral=path*math.sin(angle);lo=np.array([-bound.half_length,-bound.half_width-lateral]);hi=np.array([bound.half_length+path,bound.half_width+lateral])
    margin=bound.pose_error+2*math.hypot(bound.half_length,bound.half_width)*math.sin(min(math.pi,bound.yaw_rate*duration)/2)+bound.residual_speed*duration
    return lo,hi,margin,duration


def contains(region,state,lo,hi,margin):
    corners=np.array([[x,y] for x in [lo[0],hi[0]] for y in [lo[1],hi[1]]])@pp.rotation(state.yaw).T+np.array([state.x,state.y])
    local=(corners-np.asarray(region.center))@pp.rotation(region.yaw)
    low=np.asarray(region.low);high=np.asarray(region.high)
    q=np.abs(local-(low+high)/2)-(high-low)/2
    signed=np.linalg.norm(np.maximum(q,0),axis=1)+np.minimum(np.max(q,axis=1),0)
    return bool(np.all(signed+margin+1e-9<region.margin))


@dataclass(frozen=True)
class Commitment:
    lease_id:str
    issued_us:int
    command_until_us:int
    complete_us:int
    state:State
    low:tuple
    high:tuple
    margin:float


class Handoff:
    def __init__(self,reader,bound=Actuation()):
        self.reader=reader;self.bound=bound;self.active=None;self.last_now=-10**15;self.breached=False

    def admissible(self,identity,state,now):
        try:
            if self.breached:return False
            region=self.reader.regions[identity];now_us=ticks(now)
            if Fraction.from_float(float(now))*pp.TIME_SCALE<region.reference_us:return False
            lo,hi,margin,duration=maneuver(state,self.bound)
            if now_us+ticks(duration)>=region.expires_us:return False
            return contains(region,state,lo,hi,margin)
        except (ValueError,TypeError,KeyError,OverflowError):return False

    def decide(self,state,now,identity=None):
        """Conditional model decision, not physical authorization.

        With no accepted plan, report NO_GUARANTEE. Backup is covered only until
        the active finite commitment completes, never indefinitely after expiry.
        A new commitment starts only after full receiver proof and containment.
        An independent control watchdog MUST enforce command_until_us; this
        geometric state machine cannot guarantee remote actuator scheduling.
        """
        now_us=ticks(now)
        if now_us<self.last_now:raise ValueError('Nonmonotone decision clock')
        self.last_now=now_us
        if self.active is not None and now_us<self.active.complete_us:
            old=self.active;b=self.bound;elapsed=(now_us-old.issued_us)/pp.TIME_SCALE
            positive=min(elapsed,b.command+b.reaction)
            upper=max(0.,old.state.speed+b.speed_error+b.traction*positive-b.braking*max(0.,elapsed-b.command-b.reaction))
            region=FreeRegion('active-maneuver',old.issued_us,old.complete_us,0,(old.state.x,old.state.y),old.state.yaw,old.low,old.high,old.margin)
            if state.speed-b.speed_error>upper+b.residual_speed+1e-9 or not contains(region,state,np.array([-b.half_length,-b.half_width]),np.array([b.half_length,b.half_width]),b.pose_error):self.breached=True
        if self.breached:return 'CONTRACT_BREACH'
        if identity is not None and self.admissible(identity,state,now):
            lo,hi,margin,duration=maneuver(state,self.bound)
            exact=Fraction.from_float(float(now))*pp.TIME_SCALE
            command_end=math.floor(exact+Fraction.from_float(float(self.bound.command))*pp.TIME_SCALE)
            complete=math.floor(exact+Fraction.from_float(float(duration))*pp.TIME_SCALE)
            self.active=Commitment(identity,now_us,command_end,complete,state,tuple(lo),tuple(hi),margin)
            return 'ADVANCE_CONDITIONAL'
        if self.active is not None and now_us<self.active.complete_us:
            return 'BACKUP_CONDITIONAL'
        return 'NO_GUARANTEE'

    def watchdog_command(self,now):
        # The scheduler must call this independently of sensor processing.
        if self.breached or self.active is None or ticks(now)>=self.active.command_until_us:return 'FULL_BRAKE'
        return 'CONTINUE_COMMITTED_COMMAND'
