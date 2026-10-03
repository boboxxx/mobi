import unittest
from kernel import lens, geometry, feasible, horizon, POINT_SCALE

class TestCertificates(unittest.TestCase):
    def test_corner_lens_tighter_than_either_ball(self):
        r=lens([-3000000,0],[3000000,0],[0,10000000],5000000)
        self.assertLessEqual(r['lower_um'],6000000)
        self.assertGreaterEqual(r['upper_um'],6000000)
        self.assertLessEqual(r['upper_um']-r['lower_um'],2)
        self.assertTrue(feasible(r['point'],[-3000000,0],5000000))
        self.assertTrue(feasible(r['point'],[3000000,0],5000000))
    def test_tangent_has_a_singleton_not_empty_space(self):
        r=lens([-5000000,0],[5000000,0],[0,10000000],5000000)
        self.assertEqual((r['kind'],r['lower_um'],r['upper_um']),('tangent',10000000,10000000))
    def test_disjoint_set_refuses(self):
        r=geometry([[0,0]],[[300,0]],1000000,100000)
        self.assertEqual(r['status'],'empty')
    def test_coincident_balls(self):
        r=lens([0,0],[0,0],[3000000,0],1000000)
        self.assertLessEqual(r['lower_um'],2000000)
        self.assertGreaterEqual(r['upper_um'],2000000)
        self.assertLessEqual(r['upper_um']-r['lower_um'],2)
    def test_near_tangent_keeps_feasible_witness(self):
        r=lens([0,0],[1999999,0],[1000000,3000000],1000000)
        self.assertTrue(feasible(r['point'],[0,0],1000000))
        self.assertTrue(feasible(r['point'],[1999999,0],1000000))
        self.assertLessEqual(r['upper_um']-r['lower_um'],2)
    def test_query_inside_is_exact_zero(self):
        r=lens([0,0],[1000000,0],[0,0],1000000)
        self.assertEqual((r['kind'],r['lower_um'],r['upper_um']),('inside',0,0))
    def test_contact_is_strict_and_cap_does_not_extend(self):
        # D(200ms)=1.06m. Touching at200ms is unsafe.
        self.assertEqual(horizon(1060000,0),199999)
        self.assertEqual(horizon(100000000,0),500000)

if __name__=='__main__':unittest.main()
