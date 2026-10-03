import unittest
from lifetime import State,expiry,remaining,safe_at

class LifetimeTests(unittest.TestCase):
    def test_exact_boundary_and_age(self):
        s=State(10000000,0,1000000,2000000,0);r=expiry([s],(0,0),1000000,6000000,True)
        self.assertEqual(r['safe_through_us'],3999999);self.assertFalse(safe_at(s,(0,0),1000000,4000000));self.assertEqual(remaining(r,10000000,11000000,20000,200000),2779999)
    def test_acceleration_boundary(self):
        s=State(5000000,0,1000000,0,2000000);r=expiry([s],(0,0),0,4000000,True);self.assertEqual(r['safe_through_us'],1999999)
    def test_earliest_retained_witness(self):
        states=[State(10,0,1,2,0),State(5,0,1,2,0)];r=expiry(states,(0,0),1,9000000,True);self.assertEqual(r['witness_index'],1);self.assertEqual(r['safe_through_us'],1499999)
        self.assertGreater(expiry(states[:1],(0,0),1,9000000,True)['safe_through_us'],r['safe_through_us'])
    def test_unknown_support_and_empty_fail_closed(self):
        s=State(100,0,1,0,0);self.assertEqual(expiry([s],(0,0),0,100)['reason'],'unestablished_support');self.assertEqual(expiry([],(0,0),0,100,True)['reason'],'unestablished_support')
    def test_contact_no_authority(self):
        r=expiry([State(1,0,1,0,0)],(0,0),0,100,True);self.assertEqual(remaining(r,0,0,0),0);self.assertEqual(r['reason'],'unsafe_at_observation')
    def test_initial_contact_overrides_another_zero_tick_limit(self):
        states=[State(2,0,1,1000000,0),State(0,0,1,0,0)];r=expiry(states,(0,0),0,100,True);self.assertEqual(r['reason'],'unsafe_at_observation');self.assertEqual(r['witness_index'],1)
    def test_cap_future_date_and_stale(self):
        r=expiry([State(100,0,1,0,0)],(0,0),0,100,True);self.assertTrue(r['capped']);self.assertEqual(remaining(r,101,0,100),0);self.assertEqual(remaining(r,0,200,0),0)
    def test_invalid_units(self):
        with self.assertRaises(ValueError):State(0,0,1,-1,0)
        with self.assertRaises(ValueError):State(0.,0,1,0,0)
if __name__=='__main__':unittest.main()
