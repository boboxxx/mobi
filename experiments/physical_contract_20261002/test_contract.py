import hashlib,json,unittest
from pathlib import Path
import numpy as np
import eligibility
ROOT=Path(__file__).resolve().parents[2];RESULTS=ROOT/'results/physical_contract_20261002'
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.analysis=json.loads((RESULTS/'analysis_sheng.json').read_bytes());cls.audit=RESULTS/'audit_local.json' if (RESULTS/'audit_local.json').exists() else RESULTS/'audit_sheng.json';cls.pin=hashlib.sha256(cls.audit.read_bytes()).hexdigest()
 def gate(self,pop):return eligibility.ContractGate(RESULTS/'analysis_sheng.json',self.audit,self.pin,pop)
 def test_hidden_population_cannot_be_replaced_by_detected_only(self):
  a=self.gate(['vehicle.audi.a2','vehicle.diamondback.century']).assess(475000);self.assertEqual(a.physical_status,'refuted');self.assertEqual(a.conditional_horizon_us,475000);self.assertFalse(a.permits_physical_action())
 def test_passed_finite_frames_do_not_certify_unseen_poses(self):
  a=self.gate(['vehicle.audi.a2']).assess(475000);self.assertEqual(a.physical_status,'unverified');self.assertFalse(a.permits_physical_action())
 def test_outer_model_failure_is_not_hidden_by_opaque_core_success(self):
  a=self.gate(['vehicle.mercedes.sprinter']).assess(475000);self.assertEqual(a.physical_status,'refuted');self.assertTrue(any('every_center' in r for r in a.reasons))
 def test_new_radius_cannot_reuse_old_validation(self):
  a=self.gate(['vehicle.audi.a2']).assess(475000,'new-model');self.assertEqual(a.physical_status,'unverified');self.assertFalse(a.permits_physical_action())
 def test_unknown_population_and_corrupted_registry_fail_closed(self):
  self.assertEqual(self.gate(['unseen.actor']).assess(475000).physical_status,'unverified')
  with self.assertRaises(ValueError):eligibility.ContractGate(RESULTS/'analysis_sheng.json',self.audit,'0'*64,['vehicle.audi.a2'])
  with self.assertRaises(ValueError):self.gate([])
 def test_actual_legacy_projection_excludes_real_bicycle_center(self):
  # Reproduce a real contradictory ray with the unchanged legacy geometry.
  import sys
  sys.path.insert(0,str(ROOT/'experiments/body_evidence_20261001'));import body
  row=next(x for x in self.analysis['rows'] if x['blueprint']=='vehicle.diamondback.century' and x['receiver_excludes_actual_tile']);meta=next(x for x in json.loads((RESULTS/'capture/record.json').read_bytes()) if x['id']==row['id'])
  with np.load(RESULTS/'capture'/meta['cloud_file']) as z:points=z['xyz'][[row['proof_ray_index']]];origin=z['origin'];stamp=float(z['timestamp'])
  scope=body.Scope(meta['id'],meta['map'],tuple(meta['query']),meta['plane_z']);g=body.Profile(r_min=.55,r_max=2.5,query_radius=0,step=.1,error=0);o,r,ref=body.encode_source(points,origin,stamp,stamp);v=body.projections(o,r,ref,{'vehicle':g},scope,body.Contract())['vehicle'];margin=g.r_min-v['error'][0]-g.step/np.sqrt(2)-np.linalg.norm(v['witnesses'][0]-row['tile_center_local']);self.assertGreater(margin,.1);self.assertEqual(self.gate([meta['blueprint']]).assess(475000).physical_status,'refuted')
if __name__=='__main__':unittest.main()
