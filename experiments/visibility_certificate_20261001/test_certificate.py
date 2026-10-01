import unittest
import json
import math
from dataclasses import replace
import numpy as np
from geometry import Profile,certify,plane_witnesses,inverse_travel,covers_horizon
from proof_packet import pack,verify,canonical


class CertificateTests(unittest.TestCase):
    def setUp(self):
        self.p=Profile(r_min=.55,r_max=.6,domain=3,step=.1)
        a=np.arange(-2.95,3,.15);x,y=np.meshgrid(a,a);self.w=np.column_stack([x.ravel(),y.ravel()])

    def test_ray_plane_is_before_first_return(self):
        w=plane_witnesses(np.array([[2,0,0],[2,0,1]]),[0,0,2],[0,0],.6)
        np.testing.assert_allclose(w,[[1.4,0]])

    def test_no_scan_no_certificate(self):
        self.assertEqual(certify([],self.p)['validity_s'],0)

    def test_tiny_hole_vs_real_hidden_pocket(self):
        small=self.w[np.linalg.norm(self.w,axis=1)>.12]
        big=self.w[np.linalg.norm(self.w,axis=1)>1.0]
        self.assertGreater(certify(small,self.p)['validity_s'],0)
        self.assertEqual(certify(big,self.p)['validity_s'],0)

    def test_outside_domain_limits_even_complete_coverage(self):
        r=certify(self.w,self.p)
        self.assertLessEqual(r['clearance_m'],3-.5-.6)

    def test_uncertainty_and_outer_size_never_increase_clearance(self):
        base=certify(self.w,self.p)['clearance_m']
        self.assertLessEqual(certify(self.w,replace(self.p,error=.4))['clearance_m'],base)
        self.assertLessEqual(certify(self.w,replace(self.p,r_max=1.))['clearance_m'],base)

    def test_packet_scope_expiry_profile_and_corruption(self):
        b=pack(self.w,self.p,'action-v1',10,.1);self.assertIsNotNone(b)
        self.assertTrue(verify(b,self.p,'action-v1',10.02,.02))
        self.assertFalse(verify(b,self.p,'action-v2',10.02,.02))
        self.assertFalse(verify(b,self.p,'action-v1',10.1,0))
        self.assertFalse(verify(b,replace(self.p,error=.1),'action-v1',10.02,.02))
        bad=json.loads(b);bad['payload']['produced_at']=9
        self.assertFalse(verify(canonical(bad),self.p,'action-v1',10.02,.02))
        self.assertFalse(verify(b,self.p,'action-v1',9,.02))

    def test_sparse_class_cannot_borrow_large_core_assumption(self):
        a=np.arange(-3,3,.4);x,y=np.meshgrid(a,a);w=np.column_stack([x.ravel(),y.ravel()])
        self.assertGreater(certify(w,self.p)['validity_s'],0)
        self.assertEqual(certify(w,replace(self.p,r_min=.1))['validity_s'],0)

    def test_kinematic_inverse(self):
        t=inverse_travel(2,self.p)+self.p.clock
        self.assertAlmostEqual(self.p.speed*t+.5*self.p.acceleration*t*t,2)

    def test_nonfinite_inputs_fail(self):
        with self.assertRaises(ValueError):Profile(error=float('nan'))
        with self.assertRaises(ValueError):certify([[float('nan'),0]],self.p)
        self.assertFalse(covers_horizon(self.w,self.p,float('nan')))

if __name__=='__main__':unittest.main()
