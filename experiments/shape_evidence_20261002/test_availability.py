import unittest
from fractions import Fraction
from availability import FAMILY,family_assessment
class AvailabilityTests(unittest.TestCase):
    def test_missing_member_blocks_every_exclusion(self):
        scores={k:dict(numerator=1,denominator=1,reason=None) for k in FAMILY};scores.pop((1,16));r=family_assessment(scores,Fraction(0));self.assertFalse(r['available']);self.assertEqual(r['nonconformity'],0);self.assertEqual(r['excluded_cases'],[])
    def test_complete_family_and_ties(self):
        scores={k:dict(numerator=1,denominator=2,reason=None) for k in FAMILY};r=family_assessment(scores,Fraction(1,2));self.assertTrue(r['available']);self.assertEqual(r['excluded_cases'],[]);scores[(1,16)]['numerator']=2;self.assertEqual(family_assessment(scores,Fraction(1,2))['excluded_cases'],[(1,16)])
    def test_arbitrary_case_is_not_declared_family(self):
        scores={k:dict(numerator=0,denominator=1,reason=None) for k in FAMILY};scores[(1,8)]=scores[(1,16)];self.assertFalse(family_assessment(scores,Fraction(1))['available'])
if __name__=='__main__':unittest.main()
