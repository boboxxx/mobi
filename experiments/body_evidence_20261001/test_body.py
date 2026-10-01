import unittest,math,json
import numpy as np
from body import *


class BodyTests(unittest.TestCase):
    def setUp(self):
        self.scope=Scope('test','world',(0.,0.),.6);self.c=Contract(.001,.001,.001)
        self.p={'small':Profile(r_min=.2,r_max=.4,query_radius=0.,error=0.,speed=1.,acceleration=0.,step=.1,domain=8.)}
        self.m=Motion(.5,.25,acceleration=.2,yaw_rate=.1)
        axis=np.arange(-3.,3.01,.05);x,y=np.meshgrid(axis,axis)
        self.points=np.column_stack([x.ravel()*2,y.ravel()*2,np.full(x.size,-.6)])
        self.origin=np.array([0.,0.,1.8])

    def test_fresh_full_body_proof_and_expiry(self):
        b=pack(self.points,self.origin,1.,1.,self.p,self.scope,self.c,self.m,None,.4)
        self.assertIsNotNone(b)
        self.assertTrue(verify(b,self.p,self.scope,self.c,self.m,None,1.1,.1))
        self.assertFalse(verify(b,self.p,self.scope,self.c,self.m,None,1.4,0))
        self.assertFalse(verify(b,self.p,self.scope,self.c,Motion(2.,1.),None,1.1,0))
        region=established_region(b,self.p,self.scope,self.c,self.m,None,1.1)
        self.assertEqual(region.expires,1.4)

    def test_prior_cannot_be_invented_renewed_or_used_after_expiry(self):
        prior=Region((0.,0.),0.,(-.5,-.25),(.5,.25),0.,0.,1.2,'explicit-initial-condition','test')
        b=pack(self.points,self.origin,1.,1.,self.p,self.scope,self.c,self.m,prior,.4)
        self.assertIsNotNone(b)
        self.assertFalse(verify(b,self.p,self.scope,self.c,self.m,None,1.1,0))
        # A very short proof can establish current knowledge from a still-valid
        # prior; its later receipt does not invalidate the historical premise.
        self.assertTrue(verify(b,self.p,self.scope,self.c,self.m,prior,1.3,0))
        with self.assertRaises(ValueError):pack(self.points,self.origin,1.2,1.2,self.p,self.scope,self.c,self.m,prior,.4)
        self.assertIsNone(pack(np.array([[0.,0.,2.]]),self.origin,1.,1.,self.p,self.scope,self.c,self.m,prior,.4))

    def test_rotating_accelerating_body_is_contained(self):
        rng=np.random.default_rng(281)
        for _ in range(500):
            yaw=rng.uniform(-math.pi,math.pi);m=Motion(2.,1.,yaw,*rng.uniform(-2,2,2),3.,.4,.03)
            h=.4;lo,hi,margin=envelope(m,h,.02);t=rng.uniform(0,h+.02)
            acc=rng.normal(size=2);acc*=rng.uniform(0,m.acceleration)/np.linalg.norm(acc)
            angle=yaw+rng.uniform(-m.yaw_rate,m.yaw_rate)*t
            corners=np.array([[x,y] for x in [-2.,2.] for y in [-1.,1.]])@rotation(angle).T
            position=np.array([m.vx,m.vy])*t+.5*acc*t*t
            local=(corners+position)@rotation(yaw)
            self.assertTrue(np.all(box_distance(local,lo,hi)<=margin+1e-10))

    def test_braking_duration_includes_age_and_reaction(self):
        t=action_duration(1.,.1)
        self.assertAlmostEqual(t,.4475)
        self.assertGreater(t,action_duration(1.,0.))
        with self.assertRaises(ValueError):action_duration(1.,0.,braking=0.)

    def test_bootstrap_is_only_an_instant(self):
        prior=Region((0.,0.),0.,(-.5,-.25),(.5,.25),0.,1.,1.,'bootstrap','test')
        cells=np.array([[0.,0.]])
        self.assertTrue(prior_covers(cells,self.scope,self.m,prior,next(iter(self.p.values())),1.).all())
        with self.assertRaises(ValueError):prior_covers(cells,self.scope,self.m,prior,next(iter(self.p.values())),1.000001)

    def test_no_domain_truncation(self):
        self.assertIsNone(required(next(iter(self.p.values())),Motion(2.,1.,vx=50.),.4))


if __name__=='__main__':unittest.main()
