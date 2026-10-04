import unittest
from body_support import score_um,covered
class Tests(unittest.TestCase):
    def test_submicron_outward_rounding_and_strict_membership(self):
        p=[[1,0]];self.assertEqual(score_um(p,10000,[0.,0.]),0)
        true=[-.0000005,0.];self.assertEqual(score_um(p,10000,true),1)
        self.assertFalse(covered([p],10000,true));self.assertTrue(covered([p],10001,true))
    def test_irrational_distance_and_component_union(self):
        p=[[0,1],[1,1]];self.assertEqual(score_um(p,14000,[0.,0.]),143)
        self.assertFalse(covered([p],14142,[0.,0.]));self.assertTrue(covered([p],14143,[0.,0.]))
        self.assertTrue(covered([p,[[0,0]]],0,[0.,0.]));self.assertTrue(covered([],0,[0.,0.]))
if __name__=='__main__':unittest.main()
