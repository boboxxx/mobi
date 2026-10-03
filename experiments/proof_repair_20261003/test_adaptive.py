import math,os,unittest
from pathlib import Path
import numpy as np
from adaptive_runtime import library,repaired
from repair_runtime import Proof
import test_repair
class Adaptive(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.fixture=test_repair.Repair();cls.fixture.lib=library(Path(os.environ['MOBI_ADAPTIVE_LIBRARY']))
 def prepared(self,endz):
  p,w=self.fixture.fixture(endz);p.saved_tree=p.export();return p,w
 def test_expired_upper_stops_before_repair(self):
  p,w=self.prepared(0.)
  try:r=repaired(p,w,500000);self.assertEqual(r['gate'][0],2);self.assertEqual(r['stat'][4],0);self.assertEqual(r['stat'][0],0)
  finally:p.close()
 def test_current_exclusion_can_recover_a_grant(self):
  p,w=self.prepared(0.)
  try:r=repaired(p,w,240000);self.assertEqual(r['stat'][0],500000);self.assertEqual(r['stat'][4],1);self.assertGreater(r['stat'][0]-240000-r['receiver_s']*1e6,0)
  finally:p.close()
 def test_sufficient_baseline_skips_repairs(self):
  old,w=self.prepared(0.);tree=old.saved_tree;tree['cells'][0,0]=3.99;tree['cells'][0,6]=4.01;rad=math.ceil(np.linalg.norm([.6,.4,.5])*1e6);tree['meta'][0,4]=self.fixture.lib.exact_age(3989999,0,rad);source=dict(extent=[.6,.4,.5],anchor=[0,0,0],road_rotation=np.eye(3));p=Proof(self.fixture.lib,old.packet,old.digest,old.bps,source,(0,0),dict(numerator=1,denominator=2),5000,tree);old.close();p.saved_tree=tree
  try:r=repaired(p,w,240000);self.assertEqual(r['gate'][0],1);self.assertEqual(r['stat'][4],0)
  finally:p.close()
if __name__=='__main__':unittest.main()
