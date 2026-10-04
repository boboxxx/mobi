import importlib.util,unittest
from fractions import Fraction as F
from pathlib import Path
E=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('test_useful_certifier',E/'certify.py');C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
class Certificates(unittest.TestCase):
 def test_stationary_zero_risk_is_not_useful(self):
  r=C.risk.certificate([True]*180,[False]*180,policies=6);u=C.U.certificate([False]*180);self.assertTrue(r['accepted']);self.assertFalse(u['accepted'])
 def test_six_tests_require_94_selected(self):
  self.assertEqual(C.risk.zero_failure_required(F(1,20),F(1,20),6),94)
  self.assertFalse(C.risk.certificate([True]*93,[False]*93,policies=6)['accepted']);self.assertTrue(C.risk.certificate([True]*94,[False]*94,policies=6)['accepted'])
 def test_refusals_remain_in_progress_denominator(self):
  u=C.U.certificate([True]*20+[False]*160);self.assertEqual(u['planned'],180);self.assertFalse(u['accepted'])
  u=C.U.certificate([True]*100+[False]*80);self.assertTrue(u['accepted']);self.assertGreater(F(*u['lower']),F(1,4))
if __name__=='__main__':unittest.main()
