import unittest
import numpy as np
from codec import encode,decode
from evaluate import geometry

class TestEvidence(unittest.TestCase):
 def test_packet_roundtrip_and_pinned_radius(self):
  c=np.array([[123,-45],[-32,78]],np.int32);wire=encode(c,400001,17,8.5,2,'aa'*32,'bb'*32)
  r=decode(wire,'aa'*32,'bb'*32,2,400001);np.testing.assert_array_equal(r['centers_cm'],c);self.assertEqual(r['frame'],17);self.assertEqual(r['timestamp'],8.5)
  with self.assertRaises(ValueError):decode(wire,'aa'*32,'bb'*32,2,400002)
 def test_corruption_or_wrong_calibration_refused(self):
  wire=encode([[0,0]],1,17,8.5,2,'aa'*32,'bb'*32)
  with self.assertRaises(ValueError):decode(wire[:-1]+bytes([wire[-1]^1]),'aa'*32,'bb'*32,2,1)
  with self.assertRaises(ValueError):decode(wire,'aa'*32,'cc'*32,2,1)
 def test_missing_family_carries_no_partial_authority(self):
  wire=encode([[100,200]],50000,17,8.5,2,'aa'*32,'bb'*32,True);r=decode(wire,'aa'*32,'bb'*32,2,50000);self.assertTrue(r['refused']);self.assertEqual(len(r['centers_cm']),0)
  self.assertEqual(geometry(r['centers_cm'],r['radius_um'],[1,.5,.5],r['refused']),[dict(lower_us=0,upper_us=500000,reason='refused')]*2)
 def test_union_uses_nearest_component(self):
  a=geometry([[0,0]],100000,[1,.5,.5]);b=geometry([[0,0],[-600,0]],100000,[1,.5,.5]);self.assertGreater(a[0]['lower_us'],0);self.assertEqual(b[0]['lower_us'],0);self.assertEqual(b[0]['upper_us'],0)
 def test_empty_state_set_does_not_claim_tight_zero(self):
  self.assertEqual(geometry([],100000,[1,.5,.5])[0]['upper_us'],500000)

if __name__=='__main__':unittest.main()
