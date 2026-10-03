import importlib.util,os,unittest
from pathlib import Path
from fractions import Fraction
import numpy as np
from runtime import library,ROOT
from codec import encode as encode_tube,decode as decode_tube,decode_full
from packet import encode as encode_full
spec=importlib.util.spec_from_file_location('terrain_reference_model',ROOT/'experiments/terrain_score_20261003/model.py');model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
spec2=importlib.util.spec_from_file_location('independent_pose',ROOT/'experiments/pose_inversion_20261003/audit.py');geometry=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(geometry)
def lower(c):
 n,m,k,h=map(int,c);return max(Fraction(k,n),Fraction(max(0,m-h),m)) if m>=8 else Fraction(0)
class Tubes(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.lib=library(Path(os.environ['MOBI_TUBE_LIBRARY']))
 def count(self,p,o,c,r,inn,out,eps):
  result=np.zeros((2,4),np.int64);self.lib.tube_test_counts(np.ascontiguousarray(p),np.where(np.arange(len(p))%4==0,16,4).astype(np.int32),len(p),np.asarray(o,float),np.asarray(c,float),np.ascontiguousarray(r),np.asarray(inn,float),np.asarray(out,float),eps,result);return result
 def test_endpoint_ball_bound_and_nonmonotone_directions(self):
  rng=np.random.default_rng(13107);positive=0
  for _ in range(100):
   o=np.array([4.,3.,5.]);c=rng.uniform(-.5,.5,3);c[2]=.9;r=geometry.rotation(rng.uniform(-1,1,3));ext=np.array([1.,.6,.8]);e=ext+.03;p=rng.uniform([-2,-2,-.2],[2,2,2],(240,3));eps=.05;count=self.count(p,o,c,r,e,e,eps);positive+=lower(count[1])>0
   for __ in range(12):
    v=rng.normal(size=p.shape);v/=np.linalg.norm(v,axis=1)[:,None];moved=p+v*(rng.uniform(0,eps,len(p))[:,None]);truth=model.score(moved,o,c,r,ext);self.assertLessEqual(lower(count[1]),Fraction(truth['numerator'],truth['denominator']))
  self.assertEqual(positive,100,'The bound comparison must not pass vacuously at zero')
 def test_joint_pose_cell_and_endpoint_ball(self):
  rng=np.random.default_rng(918)
  for _ in range(80):
   lo=np.r_[rng.uniform(-1,1,2),.9,-.03,rng.uniform(0,5),-.03];hi=lo+np.array([.02,.02,.02,.02,.04,.02]);ext=np.array([.8,.5,.9]);p=rng.uniform([-3,-3,-.2],[3,3,2],(350,3));o=np.array([4.,5.,6.]);b=geometry.boxes(dict(lo=lo.tolist(),hi=hi.tolist()),ext,np.zeros(3),np.eye(3),True);cc=self.count(p,o,*b,.01)
   for __ in range(8):
    pose=rng.uniform(lo,hi);delta=rng.normal(size=p.shape);delta*=.01*rng.uniform(0,1,(len(p),1))/np.linalg.norm(delta,axis=1)[:,None];s=model.score(p+delta,o,pose[:3],geometry.rotation(pose[3:]),ext);self.assertLessEqual(lower(cc[1]),Fraction(s['numerator'],s['denominator']))
 def test_eroded_empty_is_unknown_not_zero_denominator(self):
  p=np.tile([0.,0.,0.],(20,1));cc=self.count(p,[0,0,5],[0,0,1],np.eye(3),[.001,.001,.001],[1,1,1],.05);np.testing.assert_array_equal(cc[1],[20,0,0,20]);self.assertEqual(lower(cc[1]),0)
 def test_ground_plane_moves_both_directions(self):
  p=np.tile([0.,0.,.14],(12,1));o=np.array([0,0,5.]);cc=self.count(p,o,[0,0,1],np.eye(3),[1,1,1],[1,1,1],.05)
  for dz in [-.049,.049]:
   moved=p+np.array([0,0,dz]);s=model.score(moved,o,[0,0,1],np.eye(3),[.97,.97,.97]);self.assertLessEqual(lower(cc[1]),Fraction(s['numerator'],s['denominator']))
 def test_codec_ball_membership_and_refusals(self):
  rng=np.random.default_rng(71);xyz=rng.normal(size=(400,3)).astype('<f4');mat=np.eye(4);mat[2,3]=5;digest='ab'*32;old=encode_full(xyz,10,1.,mat,4,0,digest);current=xyz.copy();current+=rng.normal(0,.001,xyz.shape).astype('<f4');current[8]+=.3;new=encode_full(current,11,2.,mat,4,0,digest);wire=encode_tube(new,old,5000,digest,['fixture']);d=decode_tube(wire,old,digest,['fixture']);oldp=decode_full(old,digest,1)['views'][-1]['points'];newp=decode_full(new,digest,1)['views'][-1]['points'];mask=np.ones(len(oldp),bool);mask[d['indices']]=False;self.assertTrue(np.all(np.linalg.norm(newp[mask]-oldp[mask],axis=1)<=.005));np.testing.assert_array_equal(d['exact_world'],newp[d['indices']]);self.assertIn(2,d['indices'])
  with self.assertRaises(ValueError):encode_tube(old,old,5000,digest,['fixture'])
  with self.assertRaises(ValueError):decode_tube(wire,None,digest,['fixture'])
  with self.assertRaises(ValueError):decode_tube(wire,old,'cd'*32,['fixture'])
  broken=bytearray(wire);broken[0]^=1
  with self.assertRaises(ValueError):decode_tube(bytes(broken),old,digest,['fixture'])
if __name__=='__main__':unittest.main()
