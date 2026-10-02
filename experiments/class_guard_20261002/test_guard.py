import copy,json,unittest
import numpy as np
import guard
body=guard.body

class Tests(unittest.TestCase):
    def setUp(self):
        self.profiles=dict(small=body.Profile(r_min=.4,r_max=.6,domain=3.,step=.1,speed=.2,acceleration=.1,clock=.01,query_radius=0,error=0),vehicle=body.Profile(r_min=.5,r_max=.7,domain=3.,step=.1,speed=.2,acceleration=.1,clock=.01,query_radius=0,error=0));self.scope=body.Scope('test','test',(0.,0.),.5);self.motion=body.Motion(half_length=.2,half_width=.1,acceleration=0,yaw_rate=0,pose_error=0);self.contract=body.Contract(point_error=0,origin_error=0,query_error=0,error_bin=.001)
        xy=np.array([(x,y) for x in np.arange(-1.4,1.401,.2) for y in np.arange(-1.4,1.401,.2)]);self.points=np.c_[xy*2/1.5,np.zeros(len(xy))];self.origin=np.array([0.,0.,2.]);self.root=self.raw(1.,0)
        self.blob=body.canonical(dict(kind='body-evidence-v1',motion=body.asdict(self.motion),prior=None,raw=self.root));self.legacy=guard.stream.base.LegacyReceiver(self.profiles,self.contract,'test','test');self.assertTrue(self.legacy.accept(self.blob,self.scope,self.motion,1.001))
    def raw(self,stamp,seq,h=.1):
        o,r,ref=body.encode_source(self.points,self.origin,stamp,stamp);return json.loads(body.serialize(o,r,ref,self.profiles,self.scope,self.contract,h,seq))
    def engine(self):
        c=guard.Receiver(self.profiles,self.contract,dict(small=200000,vehicle=100000));c.register(self.legacy,self.blob,self.scope,self.motion);c.establish_root(self.root);c.reset(1001000);return c
    def wire(self,raw,engine):return guard.compact.encode(dict(kind='class-guard-flow-v1',dynamics='observation-speed-age-v1',anchor=engine.anchor.identity,steps=[raw]))
    def test_verified_extension_retains_fact_but_not_longer_root_action(self):
        c=self.engine();self.assertGreater(c.root_budget['small'],c.root_budget['vehicle']);self.assertEqual(c.authority[0],1100000);self.assertFalse(c.can_act(1110000,1000))
    def test_joint_minimum_and_no_authority_during_verification(self):
        c=self.engine();decision,_=c.advance(self.wire(self.raw(1.15,1),c),1151000);self.assertEqual(decision['horizon_us'],100000);self.assertFalse(c.can_act(1151000,1000));c.finish(1152000);self.assertTrue(c.can_act(1152000,20000));self.assertEqual(c.authority[0],1250000)
    def test_late_verification_never_resurrects_permission(self):
        c=self.engine();c.advance(self.wire(self.raw(1.15,1),c),1151000);c.finish(1300000);self.assertEqual(c.ref,1150000);self.assertFalse(c.can_act(1300000,1000));c.advance(self.wire(self.raw(1.5,2),c),1501000);c.finish(1502000);self.assertTrue(c.can_act(1502000,20000))
    def test_unregistered_root_is_rejected(self):
        c=guard.Receiver(self.profiles,self.contract,dict(small=200000,vehicle=100000))
        with self.assertRaises(ValueError):c.register(object(),self.blob,self.scope,self.motion)
    def test_replay_future_and_incompatible_joint_horizon_fail(self):
        c=self.engine()
        for raw,start in [(self.raw(1.,1),1001000),(self.raw(1.2,1),1151000),(self.raw(1.15,1,h=.2),1151000)]:
            with self.assertRaises(ValueError):c.advance(self.wire(raw,c),start)
        self.assertEqual(c.ref,1000000)
    def test_checksum_error_not_stored_in_dictionary(self):
        c=self.engine();rx=guard.Transport(c);rx.reset(1001000);sender=guard.dictionary.Sender();raw=self.raw(1.15,1);raw['sha256']='0'*64;packet=dict(kind='class-guard-flow-v1',dynamics='observation-speed-age-v1',anchor=c.anchor.identity,steps=[raw])
        with self.assertRaises(ValueError):rx.advance(sender.encode(packet,20),1151000)
        self.assertFalse(rx.templates);self.assertEqual(c.ref,1000000)
    def test_missing_template_fails_closed(self):
        c=self.engine();rx=guard.Transport(c);rx.reset(1001000);sender=guard.dictionary.Sender();raw=self.raw(1.15,1);packet=dict(kind='class-guard-flow-v1',dynamics='observation-speed-age-v1',anchor=c.anchor.identity,steps=[raw]);sender.encode(packet,20);raw2=self.raw(1.2,2);packet['steps']=[raw2]
        with self.assertRaises(KeyError):rx.advance(sender.encode(packet,21),1201000)
        self.assertEqual(c.ref,1000000);self.assertFalse(rx.templates)
    def test_superset_augmentation_preserves_physical_contract_and_all_rays(self):
        c=self.engine();result,stats=guard.augment(self.root,self.points,self.origin,1.,self.profiles,self.contract,c.anchor,c.horizons);self.assertIsNotNone(result);_,o,r=body.decode(body.canonical(result),self.profiles,self.scope,self.contract);_,oo,rr=body.decode(body.canonical(self.root),self.profiles,self.scope,self.contract)
        keys=lambda a,b:{tuple(a[x[0]])+tuple(x[1:]) for x in b};self.assertTrue(keys(oo,rr)<=keys(o,r));self.assertEqual(result['payload']['horizon_us'],100000);self.assertEqual(result['payload']['profiles'],self.root['payload']['profiles'])
if __name__=='__main__':unittest.main()
