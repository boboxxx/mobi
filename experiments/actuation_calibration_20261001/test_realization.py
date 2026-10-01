import math,unittest
from fractions import Fraction
from realize_ticks import outward_ticks


class RealizationTests(unittest.TestCase):
    def test_enlargement_does_not_shrink_any_sampled_time_bound(self):
        for i in range(10001):
            seconds=i/10000.;n=outward_ticks(seconds)
            self.assertGreaterEqual(n*Fraction.from_float(.05),Fraction.from_float(seconds))
        self.assertEqual(outward_ticks(.2),4);self.assertEqual(outward_ticks(.197),4);self.assertEqual(outward_ticks(.099),2)
        self.assertIsNone(outward_ticks(math.inf))


if __name__=='__main__':unittest.main()
