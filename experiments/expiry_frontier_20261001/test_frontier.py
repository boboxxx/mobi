import math, unittest
import numpy as np
from frontier import body, frontier, root_ready


class FrontierTests(unittest.TestCase):
    def test_unobserved_region_has_no_positive_lifetime(self):
        p=body.Profile(domain=3,step=.1,r_min=.2,r_max=.4,error=0,query_radius=0)
        s=body.Scope('test','map',(0.,0.),.6);m=body.Motion(half_length=.3,half_width=.2,acceleration=0,yaw_rate=0)
        r=dict(witnesses=np.empty((0,2)),error=np.empty(0))
        self.assertEqual(frontier({'x':r},{'x':p},s,m,None,0)['horizon_us'],0)

    def test_random_masks_match_full_reference_and_boundary(self):
        rng=np.random.default_rng(314)
        for seed in range(8):
            p=body.Profile(domain=3,step=.1,r_min=.2,r_max=.3,error=0,query_radius=0,speed=.4,acceleration=.1,clock=.02)
            m=body.Motion(half_length=.3,half_width=.2,acceleration=0,yaw_rate=0,yaw=seed*.1)
            s=body.Scope('test','map',(0.,0.),.6)
            axis=np.arange(-1.4,1.41,.1);xx,yy=np.meshgrid(axis,axis)
            w=np.column_stack([xx.ravel(),yy.ravel()])+rng.normal(0,.004,(len(xx.ravel()),2))
            w=w@body.rotation(m.yaw).T
            r=dict(witnesses=w,error=rng.choice([.01,.02],len(w)))
            a=frontier({'x':r},{'x':p},s,m,None,0);h=a['horizon_us']
            self.assertGreater(h,0)
            for us in [1,h,h+1,200000,800000,1500000]:
                if us<=2000000:
                    self.assertEqual(body.coverage(r,p,s,m,us/1e6,None,0)[0],us<=h)

    def test_moving_envelope_is_rejected(self):
        from frontier import class_frontier
        with self.assertRaises(ValueError):
            class_frontier(None,body.Profile(),None,body.Motion(),None,0,100)

    def test_fractional_root_boundary_does_not_seed_history(self):
        # Old floating root-ready passes; encoding next sample reaches expiry.
        self.assertTrue(.35+.05 < .400001)
        self.assertFalse(root_ready(1,400000,.3500008))
        self.assertTrue(root_ready(1,400000,.3000008))


if __name__=='__main__':unittest.main()
