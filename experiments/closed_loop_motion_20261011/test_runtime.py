import random
import unittest
from fractions import Fraction as F
import runtime as R
from importlib.util import spec_from_file_location, module_from_spec

spec = spec_from_file_location('old_polygon', R.ROOT/'experiments/joint_motion_expiry_20261011/observer.py')
O = module_from_spec(spec)
spec.loader.exec_module(O)


class Tests(unittest.TestCase):
    def test_exact_roots_against_independent_bisection(self):
        rng = random.Random(2026101101)
        for _ in range(400):
            c = F(rng.randrange(-100, 10000000), rng.randrange(1, 100))
            b = F(rng.randrange(-100, 100), 10)
            a = F(rng.randrange(1, 100), 2000000)
            expected = 0
            if c > 0:
                low, high = 0, 500001
                while low+1 < high:
                    mid = (low+high)//2
                    if c+b*mid-a*mid*mid > 0:
                        low = mid
                    else:
                        high = mid
                expected = low
            self.assertEqual(R.prefix(c, b, a), expected)

    def test_extrema_against_frozen_polygons(self):
        rng = random.Random(2026101102)
        for _ in range(60):
            velocity = rng.randrange(-1500000, 1500000)
            h = [(i*100000, [[F(6000000)+F(i, 10)*velocity-100000, F(6000000)+F(i, 10)*velocity+100000], [-300000, 300000]]) for i in range(7)]
            expanded = [(t, [[lo-150000*F(h[-1][0]-t, 1000000), hi+150000*F(h[-1][0]-t, 1000000)] for lo, hi in b]) for t, b in h]
            polygons = O.infer(expanded)
            extrema = R.extrema(h)
            for poly, ext in zip(polygons, extrema):
                self.assertEqual(ext, [min(p[0] for p in poly), max(p[0] for p in poly), min(p[1] for p in poly), max(p[1] for p in poly)])

    def test_radial_baseline_and_continuous_prefix(self):
        state = [[F(5000000), F(5000000), F(0), F(0)], [F(5000000), F(5000000), F(0), F(0)]]
        # A diagonal can certify separation when neither cardinal direction can.
        tau = R.expiry(state, [0, 0], 1000000, 'snapshot')
        self.assertGreater(tau, 400000)
        self.assertEqual(R.expiry(state, [0, 0], 1000000, 'history'), 500000)
        self.assertEqual(R.expiry(None, [0, 0], 1000000, 'history'), 0)
        context = dict(extent=[.18767888844013214, .18767888844013214, .9300000071525574])
        cache = dict(source_us=1000000, states=dict(history=state))
        self.assertFalse(R.choose(cache, [0, 0], context, 999999, 'history')['allowed'])
        self.assertFalse(R.choose(cache, [0, 0], context, 1200001, 'history')['allowed'])
        self.assertEqual(R.prefix(2000000, -5, 0), 399999)


if __name__ == '__main__':
    unittest.main()
