import unittest,json
import test_body as fixtures
import body
from compress import pack


class CompressionTests(unittest.TestCase):
    def setUp(self):self.x=fixtures.BodyTests();self.x.setUp()

    def test_raw_subset_covers_every_required_tile(self):
        x=self.x;b=pack(x.points,x.origin,1.,1.,x.p,x.scope,x.c,x.m,None,.4)
        self.assertIsNotNone(b);self.assertTrue(body.verify(b,x.p,x.scope,x.c,x.m,None,1.02,.05))
        full=body.pack(x.points,x.origin,1.,1.,x.p,x.scope,x.c,x.m,None,.4)
        self.assertLess(len(json.loads(b)['raw']['payload']['rays']),len(json.loads(full)['raw']['payload']['rays']))
        source=body.encode_source(x.points,x.origin,1.,1.)[1]
        self.assertTrue({tuple(r) for r in json.loads(b)['raw']['payload']['rays']}<=set(map(tuple,source)))

    def test_missing_observations_do_not_become_free(self):
        x=self.x
        self.assertIsNone(pack(x.points[:2],x.origin,1.,1.,x.p,x.scope,x.c,x.m,None,.4))


if __name__=='__main__':unittest.main()
