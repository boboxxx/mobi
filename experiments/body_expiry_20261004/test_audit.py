import unittest
from audit import verify_proof,check_hull,independent_replay
from kernel import intersection
from codec import pack_raw,unpack
import numpy as np
class Tests(unittest.TestCase):
 def test_independent_dual_and_corruption(self):
  points=[[0,0],[2,0]];vertices=points;cc=[[x*10000,y*10000] for x,y in points];c=intersection(cc,[100000,0],30000);self.assertEqual(verify_proof(c,vertices,points,[100000,0],30000),(70000,70000));bad=dict(c,lower_um=70001)
  with self.assertRaises(AssertionError):verify_proof(bad,vertices,points,[100000,0],30000)
 def test_hull_cannot_omit_extreme(self):
  with self.assertRaises(AssertionError):check_hull([[0,0],[2,0],[1,1]],[[0,0],[2,0]])
 def test_registered_raw_same_model(self):
  xyz=np.zeros((0,3),dtype='<f4');T=np.eye(4);wire=pack_raw(xyz,T,0,42,.25,'00'*32,'11'*32);rc=dict(contract='00'*32,calibration='11'*32,transforms={'0':T.tolist()});out=unpack(wire,'raw','22'*32,'33'*32,{'x':[1.,1.,1.]},{'layouts':{'0':{'codes':[]}}},{'anchor':[0,0,0],'road':T[:3,:3].tolist()},{'x':0},rc);self.assertEqual(out['status'],'refused');self.assertEqual(out['source_us'],250000)
if __name__=='__main__':unittest.main()
