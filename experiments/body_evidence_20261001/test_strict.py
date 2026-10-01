import unittest,json
from strict import within_deadline,Receiver
import test_body as fixtures
from body import established_region
from compress import pack


class DeadlineTests(unittest.TestCase):
    def packet(self,ref,h):return json.dumps({'raw':{'payload':{'reference_us':ref,'horizon_us':h}}}).encode()

    def test_decimal_endpoint_never_admitted(self):
        for ref in range(100000,12000000,50000):
            b=self.packet(ref,200000);end=(ref+200000)/1e6
            self.assertFalse(within_deadline(b,end,0))
            self.assertFalse(within_deadline(b,end+1e-6,0))
            self.assertTrue(within_deadline(b,end-3e-6,0))

    def test_history_cannot_cross_integer_expiry(self):
        x=fixtures.BodyTests();x.setUp()
        b=pack(x.points,x.origin,5.15,5.15,x.p,x.scope,x.c,x.m,None,.2)
        receiver=Receiver(x.p,x.c,'test','world');self.assertTrue(receiver.accept(b,x.scope,x.m,5.17))
        old=established_region(b,x.p,x.scope,x.c,x.m,None,5.17)
        self.assertGreater(old.expires,5.35)  # Legacy float addition reproduces the defect.
        forged=pack(x.points,x.origin,5.35,5.35,x.p,x.scope,x.c,x.m,old,.2,1)
        self.assertIsNotNone(forged)
        self.assertFalse(receiver.accept(forged,x.scope,x.m,5.37))

    def test_two_durations_are_both_rounded_up(self):
        b=self.packet(1000000,200000)
        self.assertFalse(within_deadline(b,1.1,.1))
        self.assertTrue(within_deadline(b,1.1,.099997))
        self.assertFalse(within_deadline(b,1.1,-.1))


if __name__=='__main__':unittest.main()
