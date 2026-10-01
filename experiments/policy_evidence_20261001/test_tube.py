import math,unittest
import numpy as np
from tube import *


class TubeTests(unittest.TestCase):
    def test_hold_deadline_and_known_integral(self):
        p=Policy();s,t=policy_limits(.5,.12,p)
        self.assertAlmostEqual(s,.1872625);self.assertAlmostEqual(t,.3825)
        with self.assertRaises(ValueError):stop_duration(.5,.120001,p)

    def test_random_trajectories_and_corners_stay_in_tube(self):
        rng=np.random.default_rng(2801);p=Policy();dt=.0005;maximum_violation=0.
        for trial in range(120):
            v=float(rng.uniform(0,1));h=.6;clock=.02;hold=float(rng.uniform(0,p.hold_budget+clock));lo,hi,margin=envelope(v,h,clock,p)
            xy=np.zeros(2);yaw=0.;time=0.;speed=v
            while time<h+clock:
                # Explicit-Euler speed integration uses end-speed position and
                # a small discretization tolerance in the containment check.
                if time<min(hold,p.reaction) or hold<=time<hold+p.control+p.reaction:a=rng.uniform(0,p.traction)
                else:a=-rng.uniform(p.braking,8.)
                speed=max(0,speed+a*dt);yaw+=rng.uniform(-p.yaw_rate,p.yaw_rate)*dt;direction=yaw+rng.uniform(-p.slip,p.slip)
                xy+=speed*dt*np.array([math.cos(direction),math.sin(direction)]);time+=dt
                c,s=math.cos(yaw),math.sin(yaw);rot=np.array([[c,-s],[s,c]])
                corners=np.array([[x,y] for x in [-p.half_length,p.half_length] for y in [-p.half_width,p.half_width]])@rot.T+xy
                distance=np.linalg.norm(np.maximum(np.maximum(lo-corners,corners-hi),0),axis=1)
                maximum_violation=max(maximum_violation,float(np.max(distance-margin)))
            self.assertLessEqual(maximum_violation,2e-3)

    def test_worst_nonbraking_hold_and_maximum_go(self):
        p=Policy();v=.5;hold=.12;r=.02;go=.07
        expected=v*hold+3*(r*hold-.5*r*r)+(v+3*r)*go+1.5*go*go+(v+3*r+3*go)**2/8
        self.assertAlmostEqual(policy_limits(v,hold,p)[0],expected)
        lo,hi,m=envelope(v,.4,.02,p);self.assertGreater(hi[0],p.half_length+expected)


if __name__=='__main__':unittest.main()
