"""Conditional full-body tube for a specified hold/go/brake policy.

This restricts the EXECUTED policy; it does not infer a dynamics bound from data.
Bounds require independent validation. No infinite-horizon safety is implied.
"""
from dataclasses import dataclass,asdict
import math
import numpy as np


@dataclass(frozen=True)
class Policy:
    half_length: float=2.
    half_width: float=1.
    hold_budget: float=.12
    control: float=.05
    reaction: float=.02
    traction: float=3.
    braking: float=4.
    yaw_rate: float=.2
    slip: float=.03
    pose_error: float=.03
    residual_speed: float=.02

    def __post_init__(self):
        if not all(math.isfinite(x) and x>=0 for x in asdict(self).values()) or min(self.half_length,self.half_width,self.braking)<=0:raise ValueError('Invalid policy')


def policy_limits(speed,hold,policy):
    if not math.isfinite(speed) or not math.isfinite(hold) or min(speed,hold)<0:raise ValueError('Invalid speed/age')
    r=min(hold,policy.reaction);a=policy.traction;t=policy.control+policy.reaction
    v=speed+a*r;peak=v+a*t
    path=speed*hold+a*(r*hold-.5*r*r)+v*t+.5*a*t*t+peak*peak/(2*policy.braking)
    complete=hold+t+peak/policy.braking
    return path,complete


def envelope(speed,horizon,clock,policy=Policy()):
    if not math.isfinite(horizon) or not math.isfinite(clock) or horizon<=0 or clock<0:raise ValueError('Invalid horizon')
    total=horizon+clock;angle=policy.yaw_rate*total+policy.slip
    if angle>=math.pi/2:raise ValueError('Direction contract cannot enclose forward policy')
    path,_=policy_limits(speed,policy.hold_budget+clock,policy)
    lateral=path*math.sin(angle)
    low=np.array([-policy.half_length,-policy.half_width-lateral])
    high=np.array([policy.half_length+path,policy.half_width+lateral])
    radius=math.hypot(policy.half_length,policy.half_width)
    margin=policy.pose_error+2*radius*math.sin(policy.yaw_rate*total/2)+policy.residual_speed*total
    return low,high,margin


def stop_duration(speed,age,policy=Policy()):
    if age>policy.hold_budget:raise ValueError('Delivery missed policy hold budget')
    return policy_limits(speed,age,policy)[1]-age
