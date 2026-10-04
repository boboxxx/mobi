import unittest
from fractions import Fraction as F
from scores import current_scores,error
class Scores(unittest.TestCase):
    def test_empty_unknown_has_no_exclusion_score(self):
        self.assertEqual(current_scores([], [.5,.2,.2],{'status':'refused'},None,[0.,0.]),{m:F(0) for m in ('joint','ridge','local_mean','local_modes')})
    def test_ridge_and_local_modes_have_distinct_fixed_scores(self):
        p=dict(status='supported',mean_um=[100000,0],centers_um=[[0,0],[200000,0]],single_scale_um=50000,modes_scale_um=50000)
        d=current_scores([[[0,0]]],[.5,.2,.2],p,[100000,0],[0.,0.]);self.assertEqual(d['ridge'],100000);self.assertEqual(d['local_mean'],2);self.assertEqual(d['local_modes'],0);self.assertEqual(d['joint'],0)
    def test_binary_truth_error_is_outward(self):
        self.assertEqual(error([0,0],[.10000000001,0]),100001)
if __name__=='__main__':unittest.main()
