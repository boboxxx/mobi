import hashlib,json,struct,unittest
from pathlib import Path
import numpy as np
from binary_proof import encode,decode,BinaryVerifier,PREFIX,RAY_DTYPE,timing_after_verified,pp
from strict_policy import verify as json_verify,conditional_stop_gate


class BinaryTests(unittest.TestCase):
    def setUp(self):
        path=Path(__file__).resolve().parents[2]/'results/policy_evidence_20261001/geometry/packets/dense_0_free_00_v0.5_h0.4.json'
        self.original=path.read_bytes();obj=json.loads(self.original);s=obj['raw']['payload']['scope'];self.scope=pp.Scope(s['episode'],s['frame_id'],tuple(s['query']),s['plane_z'])
        self.profiles={k:pp.Profile(**v) for k,v in obj['raw']['payload']['profiles'].items()};self.contract=pp.Contract();self.policy=pp.Policy();self.speed=.5;self.yaw=obj['yaw']
        self.p,self.o,self.r=pp.decode(pp.canonical(obj['raw']),self.profiles,self.scope,self.contract)
        self.blob=encode(self.o,self.r,self.p['reference_us'],self.profiles,self.scope,self.contract,self.policy,self.speed,self.yaw,.4,0)
        self.verifier=BinaryVerifier();self.args=(self.profiles,self.scope,self.contract,self.policy,self.speed,self.yaw)

    def test_exact_integer_roundtrip(self):
        p,o,r=decode(self.blob,*self.args);np.testing.assert_array_equal(o,self.o);np.testing.assert_array_equal(r,self.r)
        for name in ['reference_us','horizon_us','sequence']:self.assertEqual(p[name],self.p[name])
        self.assertLess(len(self.blob),len(self.original))
        self.assertTrue(self.verifier.verify(self.blob,*self.args,1.02))

    def test_deadline_and_timing_equivalence(self):
        for now in [float(np.nextafter(1.,-np.inf)),1.,1.02,1.12,1.121,1.399999,1.4]:
            self.assertEqual(self.verifier.verify(self.blob,*self.args,now),json_verify(self.original,*self.args,now))
            self.assertEqual(timing_after_verified(self.blob,self.policy,self.speed,now),conditional_stop_gate(self.original,*self.args,now))

    def test_lengths_checksums_and_counts(self):
        for b in [self.blob[:-1],self.blob+b'0',b'',self.blob[:90],bytes([self.blob[0]^1])+self.blob[1:]]:self.assertFalse(self.verifier.verify(b,*self.args,1.02))
        b=bytearray(self.blob);struct.pack_into('>H',b,10,8193);b[-32:]=hashlib.sha256(b[:-32]).digest()
        self.assertFalse(self.verifier.verify(bytes(b),*self.args,1.02))

    def test_bad_current_indices_ages_and_coordinates_with_valid_hash(self):
        _,n,no,_=PREFIX.unpack_from(self.blob);offset=PREFIX.size+n+no*12
        for relative,value in [(0,9000),(4,1000000001),(16,-1),(16,200001)]:
            b=bytearray(self.blob);struct.pack_into('<i',b,offset+relative,value);b[-32:]=hashlib.sha256(b[:-32]).digest()
            self.assertFalse(self.verifier.verify(bytes(b),*self.args,1.02))

    def test_metadata_binding(self):
        for speed,yaw in [(0.,self.yaw),(.5,0.)]:self.assertFalse(self.verifier.verify(self.blob,self.profiles,self.scope,self.contract,self.policy,speed,yaw,1.02))
        magic,n,no,nr=PREFIX.unpack_from(self.blob);p=json.loads(self.blob[PREFIX.size:PREFIX.size+n])
        for name,value in [('sequence',False),('horizon_us',0),('reference_us',10**16),('speed',False)]:
            changed=dict(p);changed[name]=value;h=pp.canonical(changed);wire=PREFIX.pack(magic,len(h),no,nr)+h+self.blob[PREFIX.size+n:-32];bad=wire+hashlib.sha256(wire).digest()
            self.assertFalse(self.verifier.verify(bad,*self.args,1.02))


if __name__=='__main__':unittest.main()
