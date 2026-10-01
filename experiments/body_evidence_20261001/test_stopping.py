import unittest
from dataclasses import replace
import test_body as fixtures
from body import pack
from stopping import admit,Stopping


class StopTests(unittest.TestCase):
    def setUp(self):self.x=fixtures.BodyTests();self.x.setUp()

    def test_inconsistent_brake_and_motion_contract_is_rejected(self):
        x=self.x;b=pack(x.points,x.origin,1.,1.,x.p,x.scope,x.c,x.m,None,.4)
        self.assertFalse(admit(b,x.p,x.scope,x.c,x.m,None,1.02))
        with self.assertRaises(ValueError):Stopping(braking_lower=8.,braking_upper=4.)

    def test_consistent_contract_covers_action_and_complete_stop(self):
        x=self.x;m=replace(x.m,acceleration=8.)
        b=pack(x.points,x.origin,1.,1.,x.p,x.scope,x.c,m,None,.4)
        self.assertIsNotNone(b)
        self.assertTrue(admit(b,x.p,x.scope,x.c,m,None,1.02))
        self.assertFalse(admit(b,x.p,x.scope,x.c,m,None,1.35))


if __name__=='__main__':unittest.main()
