import unittest
import numpy as np
import test_proof as fixtures
from proof import encode_source,renew
from optimized import encode_source as fast_encode,renew as fast_renew


class OptimizedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):fixtures.ProofTests.setUpClass()

    def test_encoding_exact_for_shared_and_per_ray_poses(self):
        x=fixtures.ProofTests
        for origins in [x.origin,np.broadcast_to(x.origin,x.points.shape)]:
            a=encode_source(x.points,origins,10.,10.);b=fast_encode(x.points,origins,10.,10.)
            for first,second in zip(a,b):np.testing.assert_array_equal(first,second)

    def test_packets_identical_for_both_methods_and_missing_scan(self):
        x=fixtures.ProofTests
        for mode in ['heterogeneous','uniform']:
            for points in [x.points,x.points[:0]]:
                args=(x.blob,points,x.origin,11.,11.,x.profiles,x.scope,x.contract,8,mode)
                self.assertEqual(renew(*args),fast_renew(*args))


if __name__=='__main__':unittest.main()
