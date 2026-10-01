import json,math,unittest
from pathlib import Path
import numpy as np
from lease import *


class LeaseTests(unittest.TestCase):
    def setUp(self):
        root=Path(__file__).resolve().parents[2]/'results/policy_runtime_20261001/binary/packets'
        self.blob=(root/'dense_0_free_03_v0.5_h0.4.pvx').read_bytes();self.next_blob=(root/'dense_0_free_04_v0.5_h0.4.pvx').read_bytes()
        _,n,_,_=PREFIX.unpack_from(self.blob);self.header=json.loads(self.blob[PREFIX.size:PREFIX.size+n]);h=self.header;s=h['scope']
        self.scope=pp.Scope(s['episode'],s['frame_id'],tuple(s['query']),s['plane_z']);self.profiles={k:pp.Profile(**v) for k,v in h['profiles'].items()};self.reader=Reader(self.profiles,pp.Contract(),s['episode'],s['frame_id']);self.kernel=Handoff(self.reader);self.ref=h['reference_us']/pp.TIME_SCALE
        q=np.asarray(s['query']);offset=.5*.13*np.array([math.cos(h['yaw']),math.sin(h['yaw'])]);self.state=State(*(q+offset),h['yaw'],.5)

    def test_current_state_can_use_free_region_after_old_hold_budget(self):
        now=self.ref+.13;identity=self.reader.accept(self.blob,self.scope,now);self.assertIsNotNone(identity)
        self.assertTrue(self.kernel.admissible(identity,self.state,now))
        self.assertEqual(self.kernel.decide(self.state,now,identity),'ADVANCE_CONDITIONAL')
        self.assertEqual(self.kernel.watchdog_command(now+.051),'FULL_BRAKE')

    def test_bad_or_unregistered_input_cannot_reset_commitment(self):
        now=self.ref+.13;identity=self.reader.accept(self.blob,self.scope,now);self.kernel.decide(self.state,now,identity);old=self.kernel.active
        self.assertIsNone(self.reader.accept(self.blob,self.scope,now+.001))
        self.assertIsNone(self.reader.accept(self.blob[:-1]+b'?',self.scope,now+.002))
        self.assertEqual(self.kernel.decide(self.state,now+.003,'invented'),'BACKUP_CONDITIONAL');self.assertEqual(old,self.kernel.active)
        self.assertFalse(self.kernel.admissible(identity,State(self.state.x+30,self.state.y,self.state.yaw,.5),now))

    def test_valid_handoff_and_finite_fallback(self):
        now=self.ref+.13;identity=self.reader.accept(self.blob,self.scope,now);self.kernel.decide(self.state,now,identity)
        later=now+.04;new=self.reader.accept(self.next_blob,self.scope,later);self.assertIsNotNone(new)
        state=State(self.state.x+.02*math.cos(self.state.yaw),self.state.y+.02*math.sin(self.state.yaw),self.state.yaw,.5)
        self.assertEqual(self.kernel.decide(state,later,new),'ADVANCE_CONDITIONAL');self.assertEqual(self.kernel.active.lease_id,new)
        self.assertEqual(self.kernel.decide(state,later+.06),'BACKUP_CONDITIONAL')
        self.assertEqual(self.kernel.decide(state,later+1),'NO_GUARANTEE')

    def test_expiry_future_and_monotone_clock(self):
        self.assertIsNone(self.reader.accept(self.blob,self.scope,float(np.nextafter(self.ref,-np.inf))))
        self.assertIsNone(self.reader.accept(self.blob,self.scope,self.ref+.4))
        self.kernel.decide(self.state,self.ref+.2)
        with self.assertRaises(ValueError):self.kernel.decide(self.state,self.ref+.1)

    def test_rounding_watchdog_never_extends_command(self):
        now=self.ref+.13;identity=self.reader.accept(self.blob,self.scope,now);self.kernel.decide(self.state,now,identity)
        exact=(Fraction.from_float(now)+Fraction.from_float(self.kernel.bound.command))*pp.TIME_SCALE
        self.assertLessEqual(self.kernel.active.command_until_us,exact)
        self.assertLess(self.kernel.active.complete_us,self.reader.regions[identity].expires_us)

    def test_observed_contract_breach_latches_and_cannot_be_reset_by_packet(self):
        now=self.ref+.13;identity=self.reader.accept(self.blob,self.scope,now);self.kernel.decide(self.state,now,identity)
        fast=State(self.state.x,self.state.y,self.state.yaw,20.)
        self.assertEqual(self.kernel.decide(fast,now+.01,identity),'CONTRACT_BREACH')
        self.assertEqual(self.kernel.watchdog_command(now+.011),'FULL_BRAKE')
        self.assertFalse(self.kernel.admissible(identity,self.state,now+.02))

    def test_rounded_rectangle_containment(self):
        region=FreeRegion('test',0,10**6,0,(0.,0.),0.,(-3.,-2.),(3.,2.),.1);state=State(0.,0.,.5,0.)
        lo=np.array([-.5,-.2]);hi=np.array([.8,.2]);self.assertTrue(contains(region,state,lo,hi,.2))
        self.assertFalse(contains(region,State(3.,0.,.5,0.),lo,hi,.2))

    def test_bounded_maneuver_trajectory_enclosure(self):
        rng=np.random.default_rng(1002);b=Actuation();dt=.0005
        for _ in range(30):
            state=State(0.,0.,0.,float(rng.uniform(0,1)));lo,hi,margin,duration=maneuver(state,b);position=np.zeros(2);yaw=0.;speed=state.speed+b.speed_error
            corners=np.array([[x,y] for x in [-b.half_length,b.half_length] for y in [-b.half_width,b.half_width]])
            for t in np.arange(0,duration,dt):
                acceleration=rng.uniform(0,b.traction) if t<b.command+b.reaction else -rng.uniform(b.braking,8.)
                speed=max(0,speed+acceleration*dt);yaw+=rng.uniform(-b.yaw_rate,b.yaw_rate)*dt;direction=yaw+rng.uniform(-b.slip,b.slip)
                position+=speed*dt*np.array([math.cos(direction),math.sin(direction)])
                actual=corners@pp.rotation(yaw).T+position;d=np.linalg.norm(np.maximum(np.maximum(lo-actual,actual-hi),0),axis=1)
                self.assertLessEqual(float(max(d)),margin+.001)


if __name__=='__main__':unittest.main()
