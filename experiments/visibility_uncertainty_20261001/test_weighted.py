import unittest
import numpy as np
from weighted import certify_weighted,best_uniform
from geometry import Profile


class WeightedTests(unittest.TestCase):
    def setUp(self):
        self.p=Profile(r_min=.55,r_max=.6,error=0.,domain=3,step=.1)
        a=np.arange(-3,3,.1);x,y=np.meshgrid(a,a);self.w=np.column_stack([x.ravel(),y.ravel()])

    def test_errors_above_old_cap_can_still_support_geometry(self):
        self.assertGreater(certify_weighted(self.w,np.full(len(self.w),.1),self.p)['validity_s'],0)

    def test_worse_errors_never_improve_bound(self):
        a=certify_weighted(self.w,np.full(len(self.w),.03),self.p)
        b=certify_weighted(self.w,np.full(len(self.w),.4),self.p)
        self.assertLessEqual(b['clearance_m'],a['clearance_m'])

    def test_asynchronous_moving_centers_are_not_excluded(self):
        rng=np.random.default_rng(12)
        for _ in range(100):
            center=rng.uniform(-1,1,2);age=rng.uniform(0,.05,500)
            velocity=rng.uniform(-3,3,2);old=center-age[:,None]*velocity
            angle=rng.uniform(0,2*np.pi,500);radius=rng.uniform(self.p.r_min+.001,2,500)
            true=old+radius[:,None]*np.column_stack([np.cos(angle),np.sin(angle)])
            noise_angle=rng.uniform(0,2*np.pi,500)
            w=true+.02*np.column_stack([np.cos(noise_angle),np.sin(noise_angle)])
            e=.02+np.linalg.norm(velocity)*age
            r=certify_weighted(w,e,self.p,return_mask=True)
            ix=np.floor((center+self.p.domain)/self.p.step).astype(int)
            self.assertFalse(r['excluded'][ix[0]*60+ix[1]])

    def test_invalid_and_empty(self):
        self.assertEqual(certify_weighted([],[],self.p)['validity_s'],0)
        with self.assertRaises(ValueError):certify_weighted([[0,0]],[-1],self.p)
        with self.assertRaises(ValueError):certify_weighted([[0,0]],[.1],Profile())

    def test_best_uniform_is_covered_by_heterogeneous_bound(self):
        e=np.linspace(.01,.4,len(self.w))
        a=certify_weighted(self.w,e,self.p)
        b=best_uniform(self.w,e,self.p)
        self.assertLessEqual(b['validity_s'],a['validity_s']+1e-12)


if __name__=='__main__':unittest.main()
