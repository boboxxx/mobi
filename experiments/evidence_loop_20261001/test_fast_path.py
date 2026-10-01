import json,unittest
from fast_path import Receiver,body
from strict import Receiver as Reference
from compress import pack
import test_body as fixtures


class FastReceiverTests(unittest.TestCase):
    def setUp(self):
        self.x=fixtures.BodyTests();self.x.setUp();x=self.x
        self.blob=pack(x.points,x.origin,1.,1.,x.p,x.scope,x.c,x.m,None,.4)
        self.assertIsNotNone(self.blob)
    def receivers(self):
        x=self.x;return [cls(x.p,x.c,'test','world') for cls in [Reference,Receiver]]
    def test_expiry_future_corrupt_and_scope_match_reference(self):
        x=self.x
        for blob,scope,now in [(self.blob,x.scope,.99),(self.blob,x.scope,1.4),(self.blob[:-1]+b'x',x.scope,1.02),(self.blob,body.Scope('other','world',x.scope.query,x.scope.plane_z),1.02)]:
            outcomes=[r.accept(blob,scope,x.m,now) for r in self.receivers()];self.assertEqual(outcomes,[False,False])
    def test_valid_history_and_replay_match_reference(self):
        x=self.x;rs=self.receivers()
        self.assertEqual([r.accept(self.blob,x.scope,x.m,1.02) for r in rs],[True,True]);self.assertEqual(rs[0].latest_region(),rs[1].latest_region())
        self.assertEqual([r.accept(self.blob,x.scope,x.m,1.03) for r in rs],[False,False])
        b=pack(x.points,x.origin,1.1,1.1,x.p,x.scope,x.c,x.m,rs[0].latest_region(),.4,1)
        self.assertEqual([r.accept(b,x.scope,x.m,1.12) for r in rs],[True,True]);self.assertEqual(rs[0].latest_region(),rs[1].latest_region())
    def test_unknown_prior_and_expired_parent_cannot_bootstrap(self):
        x=self.x;rs=self.receivers()
        for r in rs:self.assertTrue(r.accept(self.blob,x.scope,x.m,1.02))
        b=pack(x.points,x.origin,1.1,1.1,x.p,x.scope,x.c,x.m,rs[0].latest_region(),.4,1);p=json.loads(b);p['prior']='invented'
        self.assertEqual([r.accept(body.canonical(p),x.scope,x.m,1.12) for r in rs],[False,False])
        p=json.loads(b);p['raw']['payload']['reference_us']=1400000
        self.assertEqual([r.accept(body.canonical(p),x.scope,x.m,1.41) for r in rs],[False,False])


if __name__=='__main__':unittest.main()
