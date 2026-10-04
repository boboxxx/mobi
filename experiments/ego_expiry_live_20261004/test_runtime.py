import unittest
import runtime as r
import numpy as np

class RuntimeBoundary(unittest.TestCase):
 def test_source_link_epoch_and_fifo(self):
  self.assertEqual(r.source_link(1000000,50000,2000,500,20000,0),(1072200,1052200))
  self.assertEqual(r.source_link(1000000,0,0,500,80000,2000000),(2080200,2000200))
  self.assertEqual(r.roundup(1),50000);self.assertEqual(r.roundup(50000),50000)
 def test_xyz_own_mask_without_target_labels(self):
  own=dict(location=[10.,0.,0.],matrix=np.eye(4).tolist());body=dict(extent=[2.,1.,.5],offset=[0.,0.,0.],rotation=[0.,0.,0.])
  kept,mask=r.own_mask(np.array([[10.,0.,0.],[12.04,0.,0.],[0.,0.,0.]],dtype='<f4'),np.eye(4),own,body)
  self.assertEqual(mask.tolist(),[True,False,False]);self.assertEqual(len(kept),2)
 def test_deadline_domain_and_nonrenewal(self):
  ctx=dict(basis=dict(anchor=[0.,0.,0.],road=np.eye(3).tolist()))
  body=dict(extent=[1.,1.,1.]);own=dict(center=[0.,0.,0.])
  p=dict(status='bounded',source_us=1000000,proposal_valid_until_us=1500000,query_um=[0,0],query_radius_um=r.action_radius(body)+150000)
  c=dict(obj=dict(kind='deadline',proposal=p))
  _,g=r.choose(c,own,body,ctx,1200000);self.assertTrue(g['geometry_eligible']);self.assertFalse(g['deployment_authorized'])
  _,g=r.choose(c,own,body,ctx,1200001);self.assertFalse(g['geometry_eligible'])
  own['center']=[.150001,0.,0.];_,g=r.choose(c,own,body,ctx,1100000);self.assertFalse(g['query_domain_valid'])

if __name__=='__main__':unittest.main()
