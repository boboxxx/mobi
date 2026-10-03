import importlib.util,os,sys,unittest
from pathlib import Path
from fractions import Fraction
import numpy as np
from runtime import library,Proof,ROOT,make_packet,encode,decode
spec=importlib.util.spec_from_file_location('old_lifetime',ROOT/'experiments/shape_evidence_20261002/lifetime.py');lt=importlib.util.module_from_spec(spec);sys.modules[spec.name]=lt;spec.loader.exec_module(lt)
class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.lib=library(Path(os.environ['MOBI_NATIVE_LIBRARY']))
    def test_exact_age_against_rational_oracle(self):
        rng=np.random.default_rng(92701)
        for _ in range(1500):
            x,y=[int(v) for v in rng.integers(0,100000001,2)];r=int(rng.integers(0,10000001));expected=lt.expiry([lt.State(x,y,r,5000000,3000000)],(0,0),750000,500000,True)['safe_through_us'];self.assertEqual(self.lib.exact_age(x,y,r),expected)
        for t in [0,1,199999,200000,499999,500000]:
            r=2250000;reach=Fraction(r+750000)+5*t+Fraction(3*t*t,2000000)
            for d in [reach.numerator//reach.denominator-1,reach.numerator//reach.denominator,reach.numerator//reach.denominator+1]:
                expected=lt.expiry([lt.State(d,0,r,5000000,3000000)],(0,0),750000,500000,True)['safe_through_us'];self.assertEqual(self.lib.exact_age(d,0,r),expected)
    def fixture(self):
        rng=np.random.default_rng(712);xyz=rng.uniform([-5,-5,-5],[5,5,0],(400,3)).astype(np.float32);matrix=np.eye(4);matrix[2,3]=5;digest='a7'*32;packet=encode(xyz,10,1.,matrix,4,0,digest);return xyz,matrix,digest,packet
    def test_delta_counts_and_repeated_current_observations(self):
        xyz,m,digest,packet=self.fixture();proof=Proof(self.lib,packet,digest,['fixture'],[1,.5,1],[0,0,0],np.eye(3),(3,0),dict(numerator=1,denominator=5),2000)
        try:
            for fraction in [0,.01,.5,1.]:
                changed=xyz.copy();n=int(len(xyz)*fraction);changed[:n,0]+=.37;new=encode(changed,11,2.,m,4,0,digest);a=proof.check(new,True);b=proof.check(new,False);np.testing.assert_array_equal(a['counts'],b['counts']);np.testing.assert_array_equal(a['accepted'],b['accepted']);np.testing.assert_array_equal(a['stat'][[0,1,3,4]],b['stat'][[0,1,3,4]])
        finally:proof.close()
    def test_cache_rejects_changed_identity_and_time(self):
        xyz,m,digest,packet=self.fixture();proof=Proof(self.lib,packet,digest,['fixture','other'],[1,.5,1],[0,0,0],np.eye(3),(3,0),dict(numerator=1,denominator=5),20)
        try:
            mm=m.copy();mm[0,3]=.01
            invalid=[packet,encode(xyz,11,2.,mm,4,0,digest),encode(xyz,11,2.,m,4,1,digest),encode(xyz[:-4],11,2.,m,4,0,digest),encode(xyz,11,2.,m,4,0,'11'*32)]
            for data in invalid:
                with self.assertRaises(ValueError):proof.check(data)
        finally:proof.close()
    def test_changed_observation_revokes_a_positive_old_expiry(self):
        import json,hashlib
        sources=json.loads((ROOT/'results/pose_inversion_20261003/replay/sources.json').read_bytes());bps=sorted({s['blueprint'] for s in sources});pair=sorted([s for s in sources if s['blueprint']=='vehicle.audi.a2'],key=lambda s:s['episode_index']);a=ROOT/'results/terrain_score_20261003/analysis_sheng.json';digest=hashlib.sha256(a.read_bytes()).hexdigest();q=json.loads(a.read_bytes())['summary']['vehicle.audi.a2']['threshold'];packets=[make_packet(s,digest,bps) for s in pair];s=pair[0];proof=Proof(self.lib,packets[0],digest,bps,s['extent'],s['anchor'],s['road_rotation'],(6,0),q,16000)
        try:
            self.assertGreater(proof.stat[0],0);current=proof.check(packets[1]);self.assertEqual(current['stat'][0],0);self.assertGreater(current['stat'][4],0)
        finally:proof.close()
    def test_missing_corrupted_reference_refuses(self):
        from runtime import encode_delta,decode_delta
        _,_,_,packet=self.fixture();wire=encode_delta(packet,packet)
        for ref in [None,bytes(len(packet)),packet[:-1]]:
            with self.assertRaises(ValueError):decode_delta(wire,ref)
        wrong=bytearray(wire);wrong[40]^=1
        with self.assertRaises(ValueError):decode_delta(bytes(wrong),packet)
if __name__=='__main__':unittest.main()
