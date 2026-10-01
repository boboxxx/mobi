import unittest
import numpy as np
import test_proof as fixtures
from proof import renew
from optimized_local import renew as local_renew


class LocalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):fixtures.ProofTests.setUpClass()

    def test_reference_packets_match_with_ties_holes_and_motion(self):
        x=fixtures.ProofTests
        alternatives=[x.points,np.repeat(x.points,2,axis=0),x.points[np.linalg.norm(x.points[:,:2],axis=1)>1.],x.points+np.array([.01,0,0])]
        for points in alternatives:
            for mode in ['heterogeneous','uniform']:
                args=(x.blob,points,x.origin,11.,11.,x.profiles,x.scope,x.contract,8,mode)
                self.assertEqual(renew(*args),local_renew(*args))


if __name__=='__main__':unittest.main()
