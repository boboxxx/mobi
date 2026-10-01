import unittest,json
import test_body as fixtures
from body import *
from compress import pack
from history import Receiver


class HistoryTests(unittest.TestCase):
    def setUp(self):self.x=fixtures.BodyTests();self.x.setUp()

    def test_unregistered_bootstrap_is_rejected(self):
        x=self.x;prior=Region((0.,0.),0.,(-.5,-.25),(.5,.25),0.,1.,1.,'untrusted-bootstrap','test')
        b=pack(x.points,x.origin,1.,1.,x.p,x.scope,x.c,x.m,prior,.4)
        self.assertTrue(verify(b,x.p,x.scope,x.c,x.m,prior,1.02,0))
        r=Receiver(x.p,x.c,'test','world');self.assertFalse(r.accept(b,x.scope,x.m,1.02))
        self.assertIsNone(r.latest_region())

    def test_inductive_history_requires_timely_root_and_monotone_sequence(self):
        x=self.x;b=pack(x.points,x.origin,1.,1.,x.p,x.scope,x.c,x.m,None,.4)
        r=Receiver(x.p,x.c,'test','world');self.assertFalse(r.accept(b,x.scope,x.m,1.5))
        self.assertTrue(r.accept(b,x.scope,x.m,1.02));self.assertFalse(r.accept(b,x.scope,x.m,1.02))
        prior=r.latest_region()
        fresh=pack(x.points,x.origin,1.1,1.1,x.p,x.scope,x.c,x.m,prior,.4,1)
        self.assertTrue(r.accept(fresh,x.scope,x.m,1.12))
        # Changing only a claimed history token cannot establish a region.
        packet=json.loads(fresh);packet['prior']='invented'
        other=Receiver(x.p,x.c,'test','world');self.assertFalse(other.accept(canonical(packet),x.scope,x.m,1.12))


if __name__=='__main__':unittest.main()
