import math,sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'body_expiry_20261004'))
from kernel import hull
from observer import projections,parameters,score,membership,geometry,distance,DIRECTIONS,enclosing_radius_um
class Tests(unittest.TestCase):
 def test_partial_points_do_not_force_visible_centroid(self):
  gg=[[[-100,0],[-99,0],[-98,0]]];p=projections(gg);self.assertEqual(score(p,[2.,.4,.5],[1000000,0],1),0);self.assertTrue(membership(p,parameters([2.,.4,.5]),[1000000,0]));self.assertNotEqual(100,(-100-99-98)/3)
 def test_continuous_yaw_and_tilt_cover(self):
  ext=[1.8,.8,.7];params=parameters(ext)
  for degrees in (0.,.49999,.5,.500001,43.123,89.999,91.2,179.99,214.5):
   y=math.radians(degrees);t=math.radians(4.);Ry=np.array([[math.cos(y),-math.sin(y),0],[math.sin(y),math.cos(y),0],[0,0,1]]);Rt=np.array([[math.cos(t),0,math.sin(t)],[0,1,0],[-math.sin(t),0,math.cos(t)]]);p=np.array([[x*ext[0],z*ext[1],w*ext[2]] for x in (-1,1) for z in (-1,1) for w in (-1,1)])@(Ry@Rt).T;cm=np.rint(p[:,:2]*100).astype(int).tolist();pr=projections([cm]);self.assertTrue(membership(pr,params,[0,0]),degrees);self.assertEqual(score(pr,ext,[0,0],1),0)
 def test_hull_projection_is_exact(self):
  g=[[0,0],[10,0],[10,10],[0,10],[2,4],[7,7]];self.assertEqual(projections([g]),projections([hull(g)]))
 def test_minimal_integer_slack(self):
  pr=projections([[[1000,0],[1000,1],[1001,0]]]);ext=[1.,.5,.5];s=score(pr,ext,[0,0],1);self.assertGreater(s,0);self.assertTrue(membership(pr,parameters(ext,s),[0,0]));self.assertFalse(membership(pr,parameters(ext,s-1),[0,0]))
 def test_rational_rect_distance_witness(self):
  c,s=DIRECTIONS[0];N=math.isqrt(c*c+s*s)+1;rect=dict(cell=0,group=0,bounds=[-100*N,100*N,-50*N,50*N],norm_sq=c*c+s*s);d=distance([rect],(200,0));self.assertLessEqual(d['upper_um']-d['lower_um'],1);point=d['closest_num_um'];den=d['closest_den'];u=c*point[0]+s*point[1];v=-s*point[0]+c*point[1];self.assertTrue(rect['bounds'][0]*den<=u<=rect['bounds'][1]*den);self.assertTrue(rect['bounds'][2]*den<=v<=rect['bounds'][3]*den);self.assertEqual(sum((point[k]-(200,0)[k]*den)**2 for k in (0,1))*d['squared_den'],d['squared_num']*den*den)
 def test_missing_is_not_empty(self):
  self.assertEqual(geometry([],parameters([1,1,1]))['status'],'refused');self.assertEqual(geometry(projections([[[0,0],[1000,1000]]]),parameters([.1,.1,.1]))['status'],'empty')
 def test_exact_radius_for_binary_extent(self):self.assertEqual(enclosing_radius_um([3.,4.]),5000000);self.assertEqual(enclosing_radius_um([.0000001,0]),1)
if __name__=='__main__':unittest.main()
