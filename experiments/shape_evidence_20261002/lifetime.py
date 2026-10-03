"""Exact expiry in an explicitly supplied finite union-of-discs motion model.

Does not turn shape calibration into a complete state estimator. Callers must
establish simultaneous coverage of ALL relevant states, including unseen objects.
Integer micrometres/microseconds and rational arithmetic avoid upward rounding.
"""
from dataclasses import dataclass
from fractions import Fraction

S=1000000
@dataclass(frozen=True)
class State:
    x_um:int
    y_um:int
    radius_um:int
    speed_um_s:int
    acceleration_um_s2:int
    def __post_init__(self):
        if any(type(v) is not int for v in (self.x_um,self.y_um,self.radius_um,self.speed_um_s,self.acceleration_um_s2)):raise ValueError('Integer units required')
        if min(self.radius_um,self.speed_um_s,self.acceleration_um_s2)<0:raise ValueError('Negative envelope')

def safe_at(state,query_xy_um,query_radius_um,age_us):
    t=Fraction(age_us,S)
    reach=state.radius_um+query_radius_um+state.speed_um_s*t+Fraction(state.acceleration_um_s2,2)*t*t
    d2=(state.x_um-query_xy_um[0])**2+(state.y_um-query_xy_um[1])**2
    return Fraction(d2)>reach*reach

def expiry(states,query_xy_um,query_radius_um,cap_us,complete_support=False):
    """Last safe age tick from ORIGINAL observation; touching is unsafe.

    Unknown/unrepresented support returns zero authority. `complete_support` is
    an explicit caller premise, not a check or automatic claim of physical safety.
    """
    if type(cap_us) is not int or cap_us<0 or type(query_radius_um) is not int or query_radius_um<0 or len(query_xy_um)!=2 or any(type(x) is not int for x in query_xy_um):raise ValueError('Query units')
    if not complete_support or not states:return dict(safe_through_us=0,witness_index=None,capped=False,reason='unestablished_support')
    limits=[]
    for i,s in enumerate(states):
        if not safe_at(s,query_xy_um,query_radius_um,0):return dict(safe_through_us=0,witness_index=i,capped=False,reason='unsafe_at_observation')
        if safe_at(s,query_xy_um,query_radius_um,cap_us):limits.append((cap_us,i,True,None));continue
        low=0;high=cap_us
        while high-low>1:
            mid=(high+low)//2
            if safe_at(s,query_xy_um,query_radius_um,mid):low=mid
            else:high=mid
        limits.append((low,i,False,None))
    age,i,capped,reason=min(limits,key=lambda x:(x[0],x[2],x[1]))
    return dict(safe_through_us=age,witness_index=i,capped=capped,reason=reason)

def remaining(result,observation_us,receiver_now_us,clock_error_us,reserve_us=0):
    if any(type(x) is not int for x in (observation_us,receiver_now_us,clock_error_us,reserve_us)) or min(clock_error_us,reserve_us)<0:raise ValueError('Time units')
    # Future-dated observations outside the supplied clock interval are invalid.
    if result['reason'] is not None or receiver_now_us+clock_error_us<observation_us:return 0
    age=max(0,receiver_now_us-observation_us+clock_error_us)
    return max(0,result['safe_through_us']-age-reserve_us)
