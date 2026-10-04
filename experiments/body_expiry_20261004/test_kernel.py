import math,unittest
from kernel import hull,intersection,feasible,PS,geometry,horizon,variance_certificate
class Tests(unittest.TestCase):
 def test_single_and_coincident(self):
  for c in [[[0,0]],[[0,0],[0,0]]]:
   a=intersection(c,[100,0],20);self.assertEqual((a['lower_um'],a['upper_um']),(80,80));self.assertTrue(feasible(a['point'],c,20))
 def test_three_active_empty_pairwise_overlap(self):
  c=[[0,0],[18,0],[9,16]]
  self.assertTrue(all(math.dist(a,b)<20 for a in c for b in c))
  a=intersection(c,[100,0],10);self.assertEqual(a['kind'],'empty');self.assertGreater(a['variance_gap'],0)
 def test_three_ball_singleton(self):
  c=[[5,0],[-3,4],[-3,-4]];a=intersection(c,[20,0],5);self.assertEqual(a['kind'],'singleton');self.assertEqual((a['lower_um'],a['upper_um']),(20,20))
 def test_tangent_and_near_tangent(self):
  a=intersection([[-10,0],[10,0]],[0,20],10);self.assertEqual(a['kind'],'singleton');self.assertEqual(a['lower_um'],20)
  a=intersection([[-999999,0],[999999,0]],[0,2000000],1000000);self.assertEqual(a['kind'],'dual');self.assertLessEqual(a['upper_um']-a['lower_um'],2)
 def test_query_inside_and_full_hull_equivalence(self):
  pts=[[0,0],[10,0],[10,10],[0,10],[4,5],[5,5],[10,4],[0,0]];hh=hull(pts);self.assertEqual(hh,[[0,0],[10,0],[10,10],[0,10]])
  self.assertEqual(intersection(hh,[5,5],20)['kind'],'inside');a=intersection(hh,[100,30],20);b=intersection(pts,[100,30],20);self.assertLessEqual(abs(a['lower_um']-b['lower_um']),1)
 def test_strict_contact_and_union_refusal(self):
  self.assertEqual(horizon(750000,750000),0);self.assertEqual(horizon(5000000+1500000+750000,750000),500000)
  self.assertEqual(geometry([],1000,1000)['status'],'refused');a=geometry([[[0,0],[1000,0]],[[0,0]]],100000,10000);self.assertEqual(a['status'],'bounded');self.assertEqual(a['queries'][0]['proofs'][0]['kind'],'empty')
if __name__=='__main__':unittest.main()
