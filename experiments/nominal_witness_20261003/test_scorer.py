import ctypes as C
import importlib.util
import os
import unittest
import numpy as np
from run import ROOT,Scorer,initial

spec=importlib.util.spec_from_file_location('independent_terrain',ROOT/'experiments/terrain_score_20261003/audit.py')
terrain=importlib.util.module_from_spec(spec);spec.loader.exec_module(terrain)

class TestScorer(unittest.TestCase):
 def setUp(self):
  self.lib=C.CDLL(os.environ['MOBI_NOMINAL_LIBRARY'])
  self.source=dict(extent=[.6,.4,.5],anchor=[0,0,0],road_rotation=np.eye(3))
  self.origin=np.array([0.,0.,5.])
  rng=np.random.default_rng(31203)
  self.points=np.c_[rng.uniform(-2,2,(400,2)),rng.choice([0.,1.],400)]
 def test_exact_counts_against_world_planes(self):
  scorer=Scorer(self.lib,self.points,self.source,self.origin)
  rng=np.random.default_rng(31003)
  poses=np.c_[rng.uniform(-1,1,(32,2)),rng.uniform(.4,.6,32),rng.uniform(-.03,.03,32),rng.uniform(0,6.28,32),rng.uniform(-.03,.03,32)]
  try:
   out=scorer(poses)
   for i,p in enumerate(poses):
    r=terrain.rot(p[3:])
    for j,step in enumerate((4,1)):
     n,k,_,_=terrain.reference(self.points[::step],self.origin,p[:3],r,np.array(self.source['extent']))
     np.testing.assert_array_equal(out[i,j],[n,k])
  finally:scorer.close()
 def test_sensor_inside_clipped_body_is_zero(self):
  scorer=Scorer(self.lib,self.points,self.source,self.origin)
  try:np.testing.assert_array_equal(scorer(np.array([[0,0,5,0,0,0.]])),np.zeros((1,2,2),np.int64))
  finally:scorer.close()
 def test_population_is_deterministic_and_inside_prior(self):
  lo=np.array([-12,-8,.4,-.035,0,-.035]);hi=np.array([12,8,.6,.035,2*np.pi,.035])
  a,n=initial(self.points,self.source,lo,hi,31003);b,m=initial(self.points,self.source,lo,hi,31003)
  np.testing.assert_array_equal(a,b);self.assertEqual(n,m);self.assertEqual(a.shape,(256,6));self.assertTrue(np.all(a>=lo)&np.all(a<=hi))

if __name__=='__main__':unittest.main()
