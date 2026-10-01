import json,hashlib,unittest
from dataclasses import replace
import numpy as np
from proof import Contract,Scope,Profile,pack,verify,renew,canonical,decode,projections


def resign(payload):
    return canonical(dict(payload=payload,sha256=hashlib.sha256(canonical(payload)).hexdigest()))


class ProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        x,y=np.meshgrid(np.arange(-3.5,3.5,.15),np.arange(-3.5,3.5,.15))
        cls.points=np.column_stack([x.ravel()/.85,y.ravel()/.85,np.zeros(x.size)])
        cls.origin=np.array([0.,0.,4.]);cls.scope=Scope('test','world',(0.,0.),.6)
        cls.contract=Contract(.002,.002,.002)
        cls.profiles={n:Profile(r_min=lo,r_max=hi,query_radius=.3,error=0.,speed=1.,acceleration=1.,clock=.01,domain=3.,step=.1)
                      for n,lo,hi in [('small',.4,.5),('large',.55,.6)]}
        cls.blob=pack(cls.points,cls.origin,10.,10.,cls.profiles,cls.scope,cls.contract,sequence=7)
        assert cls.blob is not None

    def check(self,blob,now=10.02,**kw):
        return verify(blob,self.profiles,self.scope,self.contract,now,.05,**kw)

    def test_joint_roundtrip_and_compact_raw_rays(self):
        self.assertTrue(self.check(self.blob))
        p,_,r=decode(self.blob,self.profiles,self.scope,self.contract)
        self.assertLess(len(r),len(self.points));self.assertNotIn('error',p)
        self.assertEqual(set(p['profiles']),set(self.profiles))

    def test_expiry_future_and_sequence(self):
        self.assertFalse(self.check(self.blob,now=10.2))
        self.assertFalse(self.check(self.blob,now=9.99))
        self.assertFalse(self.check(self.blob,min_sequence=8))

    def test_contract_and_scope_cannot_be_weakened(self):
        p=json.loads(self.blob)['payload'];p['contract']['point_error']=0.
        self.assertFalse(self.check(resign(p)))
        self.assertFalse(verify(self.blob,self.profiles,replace(self.scope,query=(1.,0.)),self.contract,10.02,.05))

    def test_omitted_class_or_forged_error_field_rejected(self):
        p=json.loads(self.blob)['payload'];del p['profiles']['small']
        self.assertFalse(self.check(resign(p)))
        p=json.loads(self.blob)['payload'];p['errors']=[0.]*len(p['rays'])
        self.assertFalse(self.check(resign(p)))

    def test_geometry_is_recomputed_from_first_returns(self):
        p=json.loads(self.blob)['payload']
        for row in p['rays']:row[3]=800  # Ground ray replaced by return above plane.
        self.assertFalse(self.check(resign(p)))

    def test_ray_times_are_not_trusted_as_fresh(self):
        p=json.loads(self.blob)['payload']
        for row in p['rays']:row[4]-=300000
        self.assertFalse(self.check(resign(p)))
        p=json.loads(self.blob)['payload'];p['rays'][0][4]=p['reference_us']+1
        self.assertFalse(self.check(resign(p)))

    def test_quantization_and_time_debits_recomputed(self):
        p,o,r=decode(self.blob,self.profiles,self.scope,self.contract)
        results=projections(o,r,p['reference_us'],self.profiles,self.scope,self.contract)
        self.assertTrue(all(np.all(v['error']>0) for v in results.values()))

    def test_renewal_needs_current_rays(self):
        b=renew(self.blob,self.points,self.origin,11.,11.,self.profiles,self.scope,self.contract,8)
        self.assertIsNotNone(b);self.assertTrue(self.check(b,now=11.02))
        self.assertFalse(self.check(self.blob,now=11.02))
        hidden=self.points.copy();hidden[:,2]=.8
        self.assertIsNone(renew(self.blob,hidden,self.origin,11.,11.,self.profiles,self.scope,self.contract,8))

    def test_uniform_baseline_and_empty_data(self):
        b=pack(self.points,self.origin,10.,10.,self.profiles,self.scope,self.contract,mode='uniform')
        self.assertTrue(self.check(b))
        self.assertIsNone(pack(self.points[:0],self.origin,10.,10.,self.profiles,self.scope,self.contract))

    def test_malformed_packets_fail_closed(self):
        for blob in [b'',b'{}',b'null',b'[]',b'{"payload":null}',b'x'*2000001]:self.assertFalse(self.check(blob))
        p=json.loads(self.blob)['payload'];p['rays'][0][0]=-1
        self.assertFalse(self.check(resign(p)))


if __name__=='__main__':unittest.main()
