import unittest,json
import numpy as np
import test_body as fixtures
from body import *
from compress import pack
from renew import renew


class RenewalTests(unittest.TestCase):
    def test_translated_body_uses_fresh_rays(self):
        x=fixtures.BodyTests();x.setUp();b=pack(x.points,x.origin,1.,1.,x.p,x.scope,x.c,x.m,None,.4)
        s=Scope('test','world',(.01,0.),.6)
        fresh=renew(b,x.points,x.origin,2.,2.,x.p,s,x.c,x.m,None,.4,1)
        self.assertIsNotNone(fresh);self.assertTrue(verify(fresh,x.p,s,x.c,x.m,None,2.02,.05))
        rows=json.loads(fresh)['raw']['payload']['rays'];self.assertTrue(all(r[4]==2000000 for r in rows))
        self.assertFalse(verify(fresh,x.p,x.scope,x.c,x.m,None,2.02,0))
        self.assertIsNone(renew(b,x.points[:2],x.origin,2.,2.,x.p,s,x.c,x.m,None,.4,1))


if __name__=='__main__':unittest.main()
