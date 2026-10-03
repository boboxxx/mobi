import hashlib,unittest
from fractions import Fraction
import numpy as np
from bounds import RayIndex
from packet import encode,decode
from solver import solve,CAP_US

class InversionTests(unittest.TestCase):
    def test_nested_packets_and_source_time(self):
        raw=np.arange(303,dtype=np.float32).reshape(-1,3);matrix=np.eye(4);matrix[:3,3]=[10,20,30];cal=hashlib.sha256(b'calibration').hexdigest()
        for stride in (16,4,1):
            data=encode(raw,71,12.375,matrix,stride,0,cal);d=decode(data,cal,1);self.assertEqual(d['timestamp'],12.375);self.assertEqual(d['frame'],71)
            for v in d['views']:np.testing.assert_array_equal(v['points'],raw[::v['stride']]+[10,20,30])
        broken=bytearray(data);broken[-40]^=1
        with self.assertRaises(ValueError):decode(bytes(broken),cal,1)
        with self.assertRaises(ValueError):decode(data,'00'*32,1)
    def test_no_rays_retains_collision_witness(self):
        idx=RayIndex(np.empty((0,3)),[0,0,8]);r=solve([idx],[1,.5,.8],np.zeros(3),np.eye(3),[6,0],Fraction(1,2),20)
        self.assertEqual(r['lower_us'],0);self.assertEqual(r['upper_us'],0);self.assertEqual(r['witness']['kind'],'retained_pose')
    def test_uninformative_threshold_never_excludes(self):
        g=np.random.default_rng(1);idx=RayIndex(g.uniform([-10,-10,0],[10,10,0],(1000,3)),[0,0,8]);r=solve([idx],[1,.5,.8],np.zeros(3),np.eye(3),[6,0],Fraction(1),20)
        self.assertEqual(r['excluded_leaves'],0);self.assertEqual(r['upper_us'],0)
    def test_both_schedulers_preserve_domain(self):
        g=np.random.default_rng(2);idx=RayIndex(g.uniform([-10,-10,-2],[10,10,-1],(1000,3)),[0,0,8])
        for policy in ('priority','fifo'):
            r=solve([idx],[1,.5,.8],np.zeros(3),np.eye(3),[6,0],Fraction(0),40,policy);self.assertLessEqual(r['lower_us'],r['upper_us']);self.assertLessEqual(r['upper_us'],CAP_US)
            for n in r['nodes']:
                if n['status']=='split':
                    a,b=[r['nodes'][i] for i in n['children']];self.assertEqual(a['lo'],n['lo']);self.assertEqual(b['hi'],n['hi']);changed=[i for i in range(6) if a['hi'][i]!=n['hi'][i]];self.assertEqual(len(changed),1);self.assertEqual(a['hi'][changed[0]],b['lo'][changed[0]])
if __name__=='__main__':unittest.main()
