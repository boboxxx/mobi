"""Finite tick driver for a synchronous delay co-simulation, not a real watchdog."""
from pathlib import Path
import math,sys
from fractions import Fraction
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'lease_handoff_20261001'))
from lease import State,contains,ticks,pp


class TickControl:
    def __init__(self,bound):
        self.bound=np.asarray(bound);assert self.bound.shape==(4,) and np.isfinite(self.bound).all()
        self.duration_ticks=math.ceil(Fraction.from_float(float(self.bound[3]))/Fraction.from_float(.05))
        assert self.duration_ticks*.05+1e-12>=self.bound[3]
        self.active=None;self.breach=None;self.issued=0

    def issue(self,region,state,frame,stamp):
        if self.breach or region is None:return False
        low=np.array([-2-self.bound[1],-1-self.bound[2]]);high=np.array([2+self.bound[0],1+self.bound[2]])
        s=State(state['x'],state['y'],math.radians(state['yaw']),state['speed'])
        if ticks(stamp)+self.duration_ticks*50000>=math.floor(region.expires*1e6):return False
        if not contains(region,s,low,high,.03):return False
        throttle=.45 if s.speed<.5 else 0.;brake=min(.2,.2*(s.speed-.5)) if s.speed>.6 else 0.
        self.active=dict(start=frame,command_until=frame+1,complete=frame+self.duration_ticks,reference=state,low=low,high=high,throttle=throttle,brake=brake)
        self.issued+=1;return True

    def command(self,frame):
        if not self.breach and self.active and frame<self.active['command_until']:
            return self.active['throttle'],self.active['brake'],'COMMITTED'
        return 0.,1.,'FULL_BRAKE'

    def observe(self,state):
        a=self.active
        if not a or state['frame']>a['complete']:return
        ref=a['reference'];yaw=math.radians(ref['yaw'])
        points=(np.asarray(state['body_vertices'])[:,:2]-[ref['x'],ref['y']])@pp.rotation(yaw)
        distance=np.linalg.norm(np.maximum(np.maximum(a['low']-points,points-a['high']),0),axis=1)
        if np.any(distance>.03+1e-9):self.breach='BODY_BOUND'
        if state['frame']==a['complete'] and state['speed']>.02+1e-9:self.breach='STOP_TIME'
