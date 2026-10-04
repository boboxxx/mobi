import importlib.util,math,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('test_receiver_fixed_runtime',Path(__file__).resolve().parent/'runtime.py');R=importlib.util.module_from_spec(s);s.loader.exec_module(R)
class Protocol(unittest.TestCase):
 def test_late_decode_is_not_usable_before_budget(self):
  now=100000;ready=R.ready_at(now,90000,90000,'immediate');limit=R.usable_by(now,90000,'immediate');self.assertGreater(ready,limit);self.assertFalse(R.command_clock(now,90000,1)[1])
  self.assertLessEqual(ready,R.usable_by(now+100000,0,'immediate'))
 def test_processing_cannot_renew_source_epoch(self):
  p=dict(status='bounded',lower_us=500000,source_us=0,proposal_valid_until_us=500000,deployment_authorized=False,risk_certificate_applicable=False)
  self.assertTrue(R.decision(p,200000,300000)['geometry_eligible']);decision,ok=R.command_clock(200000,200,100);self.assertTrue(ok);self.assertFalse(R.decision(p,decision,300000)['geometry_eligible']);self.assertEqual(p['source_us'],0);self.assertEqual(p['proposal_valid_until_us'],500000)
 def test_body_contains_processing_and_action_motion(self):
  body=dict(extent=[1.8,.9,.8]);radius=R.action_radius(body);base=math.ceil(math.sqrt(sum(x*x for x in body['extent']))*1000000);self.assertGreaterEqual(radius-base,750000*(R.ACTION+R.BUDGET)//1000000+20000)
  self.assertEqual(R.PARENT.BASE.action_radius(body),radius);self.assertEqual(R.PARENT.action_radius(body),radius)
if __name__=='__main__':unittest.main()
