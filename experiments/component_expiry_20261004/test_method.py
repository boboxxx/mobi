import unittest
from fractions import Fraction as F
from method import conformity,infer,simultaneous_error_bound
from geometry import infer as old_infer,conformity as old_score
from integer_state import body_um,oracle_age
class SeparateEvidence(unittest.TestCase):
    def test_empty_refuses(self):
        self.assertEqual(set(conformity([], [.1]*3,dict(status='refused'),[0.,0.]).values()),{F(0)})
        self.assertEqual(infer([], [.1]*3,dict(status='refused'),dict(supported=F(0),fallback_um=0),'component_mean')['status'],'refused')
    def test_supported_unchanged_and_fallback_event_zero(self):
        p=dict(status='supported',mean_um=[5000000,0],centers_um=[[5000000,0],[5010000,0]],single_scale_um=50000,modes_scale_um=70000);hh=[[[500,0],[499,0]]];ext=[.1]*3;xy=[5.,.02];s=conformity(hh,ext,p,xy)
        self.assertEqual(s['fallback_um'],0)
        for mode in ('mean','modes'):
            q=s['supported_'+mode];self.assertEqual(q,old_score(hh,ext,p,xy,'local_'+mode))
            a=infer(hh,ext,p,dict(supported=q,fallback_um=99999999),'component_'+mode);b=old_infer(hh,ext,p,q,'local_'+mode,'max')
            self.assertEqual((a['status'],a['lower_us']),(b['status'],b['lower_us']))
    def test_fallback_in_direct_length_unit_and_truth_covered(self):
        hh=[[[500,0]]];ext=[.1]*3;xy=[5.,.020001];p=dict(status='fallback');s=conformity(hh,ext,p,xy)
        self.assertEqual(s['supported_mean'],0);self.assertEqual(s['supported_modes'],0);self.assertEqual(s['fallback_um'].denominator,1)
        a=infer(hh,ext,p,dict(supported=F(999),fallback_um=int(s['fallback_um'])),'component_mean');self.assertEqual(a['delta_um'],int(s['fallback_um']))
        if a['status']=='bounded':
            for t,q in zip(a['lower_us'],((-6000000,0),(6000000,0))):self.assertLessEqual(t,oracle_age(xy,body_um(ext),q))
    def test_confidence_counts_shared_fallback_once(self):
        self.assertGreater(simultaneous_error_bound(259),F(1,40));self.assertLessEqual(simultaneous_error_bound(260),F(1,40))
        self.assertGreater(simultaneous_error_bound(125),F(1,40))
    def test_invalid_threshold_rejected(self):
        with self.assertRaises(AssertionError):infer([[[500,0]]],[.1]*3,dict(status='fallback'),dict(supported=0,fallback_um=F(1,2)),'component_mean')
if __name__=='__main__':unittest.main()
