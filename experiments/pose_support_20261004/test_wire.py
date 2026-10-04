import hashlib,json,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'body_expiry_20261004'))
from codec import pack,pack_raw
from frontend import groups
from kernel import hull
from wire import unpack,infer
from observer import DIRECTIONS
class Tests(unittest.TestCase):
 def context(self):return dict(catalog={'x':[1.,.5,.5]},basis={'anchor':[0,0,0],'road':np.eye(3).tolist()},background={'layouts':{'0':{'codes':[]}}},slacks_um={'x':0},raw_transport={'contract':'00'*32,'calibration':'11'*32,'transforms':{'0':np.eye(4).tolist()}},directions=DIRECTIONS,tilt_operator_norm_upper=[87267,1000000],yaw_cell_distance_factor=[8730,1000000])
 def test_same_actual_hull_and_raw_model(self):
  ctx=self.context();xyz=np.array([[6.9,-.1,.5],[7.1,-.1,.5],[7.1,.1,.5],[6.9,.1,.5]],dtype='<f4');T=np.eye(4);gg=groups(xyz,T,np.zeros(3),np.eye(3),ctx['catalog']['x'],[]);hh=[hull(g) for g in gg];wire=pack('hull',hh,0,0,42,250000,'22'*32,'33'*32);raw=pack_raw(xyz,T,0,42,.25,'00'*32,'11'*32);a=unpack(wire,'joint_hull',ctx,'22'*32,'33'*32);b=unpack(raw,'joint_raw',ctx,'22'*32,'33'*32);self.assertEqual(a,b);self.assertEqual(a['source_us'],250000);sphere=unpack(wire,'sphere_hull',ctx,'22'*32,'33'*32);self.assertTrue(all(x>=y for x,y in zip(a['lower_us'],sphere['lower_us'])))
 def test_registered_grid_and_checksum(self):
  ctx=self.context();wire=pack('hull',[],0,0,42,0,'22'*32,'33'*32);ctx['directions']=[]
  with self.assertRaises(AssertionError):unpack(wire,'pose_hull',ctx,'22'*32,'33'*32)
  with self.assertRaises(Exception):unpack(wire[:-1]+bytes([wire[-1]^1]),'pose_hull',self.context(),'22'*32,'33'*32)
if __name__=='__main__':unittest.main()
