import unittest
import numpy as np
from geometry import Profile
from proof_packet import pack,verify
from renewal import renew,verify_all

class RenewalTests(unittest.TestCase):
    def setUp(self):
        self.p=Profile(r_min=.55,r_max=.6,domain=3,step=.1)
        a=np.arange(-2.95,3,.15);x,y=np.meshgrid(a,a);self.w=np.column_stack([x.ravel(),y.ravel()])
        self.template=pack(self.w,self.p,'old',0,.1)

    def test_fresh_data_can_renew_after_old_expiry(self):
        blob=renew(self.template,self.w,self.p,'new',10)
        self.assertTrue(verify(blob,self.p,'new',10.01,.02))
        self.assertFalse(verify(self.template,self.p,'old',10,.02))

    def test_new_occlusion_and_empty_scan_cannot_renew(self):
        hidden=self.w[np.linalg.norm(self.w,axis=1)>1]
        self.assertIsNone(renew(self.template,hidden,self.p,'new',10))
        self.assertIsNone(renew(self.template,[],self.p,'new',10))

    def test_all_required_classes_mandatory(self):
        self.assertFalse(verify_all({'car':self.template},{'car':self.p,'small':self.p},{'car':'old','small':'old'},.01,.02))
        self.assertTrue(verify_all({'car':self.template,'small':self.template},{'car':self.p,'small':self.p},{'car':'old','small':'old'},.01,.02))
        self.assertFalse(verify_all({}, {}, {}, .01,.02))

if __name__=='__main__':unittest.main()
