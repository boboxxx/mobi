import itertools
import unittest
import numpy as np
from projection import bounded_witnesses, select_for_profile


def truth(p,o,q,z):
    t=(o[:,2]-z)/(o[:,2]-p[:,2])
    return (1-t[:,None])*o[:,:2]+t[:,None]*p[:,:2]-q


class ProjectionTests(unittest.TestCase):
    def test_all_input_box_corners(self):
        p=np.array([[12.,-8.,-.3]]);o=np.array([[1.,2.,5.]])
        q=np.array([2.,3.]);e=.03;z=.6
        r=bounded_witnesses(p,o,q,z,e,e,e)
        for signs in itertools.product([-1,1],repeat=8):
            s=np.array(signs)
            w=truth(p+s[:3]*e,o+s[3:6]*e,q+s[6:]*e,z)
            self.assertLessEqual(np.linalg.norm(w-r['witnesses']),r['projection_error'][0])

    def test_random_boxes(self):
        rng=np.random.default_rng(8)
        p=rng.uniform(-20,20,(100,3));p[:,2]=rng.uniform(-2,0,100)
        o=np.tile([0.,0.,8.],(100,1));q=np.array([2.,3.]);z=.6;e=.02
        r=bounded_witnesses(p,o,q,z,e,e,e)
        for _ in range(50):
            w=truth(p+rng.uniform(-e,e,p.shape),o+rng.uniform(-e,e,o.shape),q+rng.uniform(-e,e,2),z)
            self.assertTrue(np.all(np.linalg.norm(w-r['witnesses'],axis=1)<=r['projection_error']))

    def test_ambiguous_plane_crossings_are_not_evidence(self):
        r=bounded_witnesses([[1,0,.59],[2,0,0]],[0,0,2],[0,0],.6,point_error=.02)
        np.testing.assert_array_equal(r['ray_indices'],[1])
        r=bounded_witnesses([[2,0,0]],[0,0,.61],[0,0],.6,origin_error=.02)
        self.assertEqual(len(r['witnesses']),0)

    def test_zero_error_geometry(self):
        r=bounded_witnesses([[2,0,0]],[0,0,2],[0,0],.6)
        np.testing.assert_allclose(r['witnesses'],[[1.4,0]])
        self.assertLess(r['error'][0],1e-7)

    def test_low_elevation_amplifies_vertical_error(self):
        shallow=bounded_witnesses([[20,0,.55]],[0,0,.65],[0,0],.6,.01,.01)
        steep=bounded_witnesses([[20,0,0]],[0,0,8],[0,0],.6,.01,.01)
        self.assertGreater(shallow['error'][0],steep['error'][0]*10)

    def test_old_rays_cannot_borrow_fresh_timestamps(self):
        r=bounded_witnesses([[2,0,0],[2,0,0]],[0,0,2],[0,0],.6,
                            ray_age=[0,.05],speed=5,acceleration=3)
        self.assertEqual(len(select_for_profile(r,.05)),1)
        self.assertAlmostEqual(r['motion_error'][1],.25375)

    def test_invalid_contracts_fail(self):
        for kwargs in [dict(ray_age=-1),dict(point_error=-1),dict(origin_error=float('nan')),dict(speed=-1)]:
            with self.assertRaises(ValueError):
                bounded_witnesses([[2,0,0]],[0,0,2],[0,0],.6,**kwargs)


if __name__=='__main__':unittest.main()
