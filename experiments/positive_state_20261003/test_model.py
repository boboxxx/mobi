import unittest
import numpy as np
from model import centers,quantized_centers,radius_um,score

class TestPositiveModel(unittest.TestCase):
 def test_disjoint_components_are_all_retained(self):
  p=np.array([[0,0,.8],[.01,.01,.8],[.1,.1,.8],[3,0,.8],[3.01,.01,.8],[3.1,.1,.8]])
  c,meta=centers(p,[0,0,0],np.eye(3),[1,.5,1]);np.testing.assert_allclose(c,[[.05,.05],[3.05,.05]]);self.assertEqual(meta['retained'],2)
 def test_ground_and_unsupported_components_are_not_centers(self):
  c,meta=centers(np.array([[0,0,.1],[.01,.01,.1],[0,0,.8]]),[0,0,0],np.eye(3),[1,.5,1]);self.assertEqual(len(c),0);self.assertEqual(meta['selected'],1)
 def test_diagonal_grid_adjacency_is_connected(self):
  p=np.array([[.19,.19,.8],[.21,.21,.8],[.22,.22,.8]])
  c,_=centers(p,[0,0,0],np.eye(3),[1,.5,1]);self.assertEqual(len(c),1)
 def test_quantized_discs_contain_original_discs(self):
  c=np.random.default_rng(71003).uniform(-10,10,(1000,2));d=np.linalg.norm(quantized_centers(c)/100.-c,axis=1);self.assertTrue(np.all(d<=.008))
 def test_joint_rank_and_missing_refusal_score(self):
  self.assertEqual(radius_um(list(range(39))),37008001);self.assertIsNone(radius_um([1.]));self.assertEqual(score(np.empty((0,2)),[0,0]),0.)

if __name__=='__main__':unittest.main()
