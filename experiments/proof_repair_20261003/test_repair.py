import json,os,sys,unittest,zlib
from pathlib import Path
import numpy as np
from repair_runtime import ROOT,Proof,library
from codec import encode
from packet import encode as encode_full
class Repair(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.lib=library(Path(os.environ['MOBI_REPAIR_LIBRARY']))
 def fixture(self,endz):
  xyz=np.tile([0.,0.,endz-5],(320,1)).astype('<f4');mat=np.eye(4);mat[2,3]=5;digest='ab'*32;old=encode_full(xyz,1,1.,mat,4,0,digest);new=encode_full(xyz,2,2.,mat,4,0,digest);source=dict(extent=[.6,.4,.5],anchor=[0,0,0],road_rotation=np.eye(3));lo=np.array([-.01,-.01,.99,-.001,0,-.001]);hi=np.array([.01,.01,1.01,.001,.002,.001]);tree=dict(cells=np.r_[lo,hi][None,:],meta=np.array([[-1,-1,-1,0,0,0]],np.int64),counts=np.zeros((1,2,4),np.int64));proof=Proof(self.lib,old,digest,['fixture'],source,(0,0),dict(numerator=1,denominator=2),5000,tree);return proof,encode(new,old,5000,digest,['fixture'])
 def test_old_unresolved_leaf_can_be_excluded(self):
  p,w=self.fixture(0.)
  try:
   a=p.repaired(w,0);b=p.repaired(w,1);self.assertEqual(a['stat'][0],0);self.assertEqual(b['meta'][0,3],2);self.assertEqual(b['flags'][0],2);self.assertGreater(b['stat'][0],a['stat'][0]);self.assertEqual(b['stat'][5],1)
  finally:p.close()
 def test_message_compatible_witness_tightens_upper(self):
  p,w=self.fixture(1.)
  try:
   a=p.repaired(w,1);self.assertEqual(a['stat'][0],0);self.assertEqual(a['stat'][1],0);self.assertEqual(a['stat'][7],1);self.assertTrue(np.isfinite(a['witness']).all())
  finally:p.close()
 def test_real_saved_baseline_and_monotone_repair(self):
  d=ROOT/'results/tube_evidence_20261003/replay';rows=json.loads((d/'warm.json').read_bytes());w=next(r for r in rows if r['radius_um']==5000 and r['sigma']==.001);cold=next(r for r in json.loads((d/'cold.json').read_bytes()) if r['proof']==w['proof']);sources=json.loads((ROOT/'results/pose_inversion_20261003/replay/sources.json').read_bytes());source=next(s for s in sources if s['case']==w['old_case']);bps=sorted({s['blueprint'] for s in sources});import hashlib
  analysispath=ROOT/'results/terrain_score_20261003/analysis_sheng.json';digest=hashlib.sha256(analysispath.read_bytes()).hexdigest();analysis=json.loads(analysispath.read_bytes());z=np.load(d/w['proof']);tree={k:z[k] for k in z.files};p=Proof(self.lib,zlib.decompress((d/cold['reference']).read_bytes()),digest,bps,source,(-6 if w['query_index']==0 else 6,0),analysis['summary'][w['blueprint']]['threshold'],5000,tree)
  try:
   previous=None
   for budget in (0,16,256):
    a=p.repaired((d/w['message']).read_bytes(),budget);self.assertGreaterEqual(a['stat'][0],w['lower_us'])
    if previous is not None:self.assertGreaterEqual(a['stat'][0],previous['stat'][0]);self.assertLessEqual(a['stat'][1],previous['stat'][1])
    else:self.assertEqual(a['stat'][0],w['lower_us']);self.assertEqual(a['stat'][1],w['upper_us'])
    previous=a
  finally:p.close()
if __name__=='__main__':unittest.main()
