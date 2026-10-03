import unittest
from fractions import Fraction
import numpy as np
from model import score, fraction, threshold, rejected

class ShapeTests(unittest.TestCase):
    def s(self,end,origin=(-3,0,0),n=8):return score(np.tile(end,(n,1)),origin,[0,0,0],np.eye(3),[1,1,1])
    def test_pass_hit_foreground(self):
        self.assertEqual(fraction(self.s([3,0,0])),1)
        self.assertEqual(fraction(self.s([-1,0,0])),0)
        self.assertEqual(self.s([-2,0,0])['reason'],'insufficient_visible_rays')
    def test_missing_support_abstains(self):
        self.assertEqual(self.s([3,0,0],n=7)['reason'],'insufficient_visible_rays')
        self.assertEqual(self.s([3,0,0],n=0)['visible_count'],0)
    def test_parallel_miss(self):
        self.assertEqual(self.s([3,2,0],origin=(-3,2,0))['visible_count'],0)
    def test_origin_inside(self):self.assertEqual(self.s([3,0,0],origin=(0,0,0))['reason'],'sensor_inside_hypothesis')
    def test_rotation_and_shape_validation(self):
        with self.assertRaises(ValueError):score([[1,2,3]],[0,0,0],[1,1,1],np.ones((3,3)),[1,1,1])
        with self.assertRaises(ValueError):score([[float('nan'),2,3]],[0,0,0],[1,1,1],np.eye(3),[1,1,1])
    def test_small_calibration_vacuous(self):
        q=threshold([Fraction(0)]*18);self.assertTrue(q['vacuous']);self.assertFalse(rejected(self.s([3,0,0]),q))
    def test_strict_ties(self):
        q=threshold([Fraction(1,2)]*19);s=dict(numerator=1,denominator=2,reason=None)
        self.assertFalse(rejected(s,q));self.assertTrue(rejected(dict(s,numerator=2),q));self.assertEqual(q['rank'],19)
    def test_joint_family_needed(self):
        qfull=threshold([Fraction(1,4)]*19);qjoint=threshold([Fraction(3,4)]*19);s=dict(numerator=1,denominator=2,reason=None)
        self.assertTrue(rejected(s,qfull));self.assertFalse(rejected(s,qjoint))
    def test_translation_rotation_invariance(self):
        p=np.array([[3.,0.,0.]]*8);o=np.array([-3.,0.,0.]);r=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]]);t=np.array([17.,21.,8.]);a=score(p,o,np.zeros(3),np.eye(3),[1,1,1]);b=score(p@r.T+t,o@r.T+t,t,r,[1,1,1]);self.assertEqual(a,b)
if __name__=='__main__':unittest.main()
