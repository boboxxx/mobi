import unittest
from fractions import Fraction as F
from method import unit,conformity,infer
from geometry import infer as previous_infer,conformity as previous_score
from integer_state import body_um,oracle_age

class TypedEvidence(unittest.TestCase):
    def prediction(self):
        return dict(status='supported',single_scale_um=50000,modes_scale_um=70000,
                    mean_um=[5000000,0],centers_um=[[5000000,0],[5010000,10000]])

    def test_empty_is_unknown(self):
        self.assertEqual(conformity([], [.1,.1,.1],dict(status='refused'),[0.,0.],'typed_mean'),0)
        self.assertEqual(infer([], [.1,.1,.1],dict(status='refused'),0,'typed_mean')['status'],'refused')

    def test_supported_pose_unit_stays_fixed(self):
        p=self.prediction();self.assertEqual(unit([.1,.1,.1],p,'typed_mean'),(10000,50000))
        g=infer([[[500,0]]],[.1,.1,.1],p,F(3,2),'typed_mean')
        self.assertEqual((g['delta_um'],g['radius_um']),(15000,75000))

    def test_supported_same_threshold_equals_original(self):
        p=self.prediction();hh=[[[500,0],[499,0]]];ext=[.1,.1,.1]
        for family,original in [('typed_mean','local_mean'),('typed_modes','local_modes')]:
            q=F(7,3);g=infer(hh,ext,p,q,family);old=previous_infer(hh,ext,p,q,original,'max')
            self.assertEqual((g['status'],g['lower_us']),(old['status'],old['lower_us']))
            self.assertEqual(conformity(hh,ext,p,[5.,.02],family),previous_score(hh,ext,p,[5.,.02],original))

    def test_supported_boundary_is_conservative(self):
        p=self.prediction();hh=[[[500,0]]];ext=[.1,.1,.1];xy=[5.,.02]
        for family in ('typed_mean','typed_modes'):
            q=conformity(hh,ext,p,xy,family);g=infer(hh,ext,p,q,family)
            self.assertEqual(g['status'],'bounded')
            for a,query in zip(g['lower_us'],((-6000000,0),(6000000,0))):self.assertLessEqual(a,oracle_age(xy,body_um(ext),query))

    def test_fallback_uses_body_scale_and_checked_joint(self):
        p=dict(status='fallback');hh=[[[500,0]]];ext=[.1,.1,.1];xy=[5.,.02]
        units=unit(ext,p,'typed_mean');self.assertEqual(units,(body_um(ext),body_um(ext)))
        g=infer(hh,ext,p,conformity(hh,ext,p,xy,'typed_mean'),'typed_mean')
        self.assertEqual(g['kind'],'fallback_joint');self.assertIn('sphere',g['joint_geometry'])
        if g['status']=='bounded':
            for a,query in zip(g['lower_us'],((-6000000,0),(6000000,0))):self.assertLessEqual(a,oracle_age(xy,body_um(ext),query))
if __name__=='__main__':unittest.main()
