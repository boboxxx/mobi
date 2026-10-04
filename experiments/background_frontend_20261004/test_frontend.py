import unittest
import numpy as np
from model import voxel_codes,extract
class Tests(unittest.TestCase):
    def test_unique_boundary_voxels(self):
        p=np.array([[-12,-8,.30001],[-12,-8,.4],[-12,8,.30001],[12,-8,.30001],[12,8,2.999]])
        codes=voxel_codes(p);self.assertTrue(np.all(codes>=0));self.assertEqual(len(set(codes)),len(p))
        self.assertTrue(np.all(voxel_codes(np.array([[0,0,.3],[0,0,3],[12.001,0,1],[0,8.001,1]]))==-1))
    def test_complete_subtraction_refuses(self):
        xyz=np.array([[0,0,1],[.01,.01,1],[.02,.02,1]])
        c,m=extract(xyz,np.eye(4),np.zeros(3),np.eye(3),[1,1,1],voxel_codes(xyz));self.assertEqual(len(c),0);self.assertEqual(m['background_removed'],3)
    def test_no_map_equivalence_and_moved_point(self):
        xyz=np.array([[0,0,1],[.01,.01,1],[.02,.02,1]])
        c,m=extract(xyz,np.eye(4),np.zeros(3),np.eye(3),[1,1,1],[]);np.testing.assert_allclose(c,[[.01,.01]])
        shifted=xyz+[.2,0,0];c,m=extract(shifted,np.eye(4),np.zeros(3),np.eye(3),[1,1,1],voxel_codes(xyz));self.assertEqual(len(c),1);self.assertEqual(m['background_removed'],0)
if __name__=='__main__':unittest.main()
