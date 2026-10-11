import random
import unittest
from fractions import Fraction as F
import observer as O


class ObserverTests(unittest.TestCase):
    def test_exact_clipping(self):
        square = [(F(0), F(0)), (F(4), F(0)), (F(4), F(4)), (F(0), F(4))]
        poly = O.clip(square, F(1), F(2), F(3))
        self.assertEqual(set(poly), {(F(0), F(0)), (F(3), F(0)), (F(0), F(3, 2))})

    def test_history_covers_bounded_acceleration(self):
        # Constant accelerations through source and future; check exact states.
        for accel in (-O.ACCEL, 0, O.ACCEL):
            for v0 in (-1000000, 0, 1000000):
                history = []
                for tick in range(7):
                    t = F(tick, 10)
                    p = 5000000+v0*t+F(accel, 2)*t*t
                    bounds = [[p-10000, p+10000], [-10000, 10000]]
                    history.append((tick*100000, bounds))
                poly = O.infer(history)
                t = F(3, 5)
                self.assertTrue(O.contains(poly, [5000000+v0*t+F(accel, 2)*t*t, 0], [v0+accel*t, 0]))
                for future in range(0, O.CAP+1, 50000):
                    dt = F(future, 1000000)
                    p = 5000000+v0*(t+dt)+F(accel, 2)*(t+dt)**2
                    self.assertLessEqual(O.margin(poly[0], 1, 0, 0, future), p)

    def test_whole_prefix_and_fees(self):
        history = [(0, [[6000000, 6001000], [-100, 100]])]
        polys = O.infer(history)
        expiry = O.expiry(polys, [0, 0], 1000000)
        self.assertGreater(expiry, 0)
        # Check every millisecond in the proven prefix against exact support.
        self.assertTrue(all(O.margin(polys[0], 1, 0, 3500000, t) > 0 for t in range(0, expiry+1, 1000)))
        self.assertFalse(O.permit(1000000, expiry, 999999))
        self.assertEqual(O.permit(1000000, expiry, 1000000+expiry-O.ACTION), expiry >= O.ACTION)
        self.assertFalse(O.permit(1000000, expiry, 1000000+expiry-O.ACTION+1))

    def test_future_axis_support_factorization_identity(self):
        # With only past axis bands, low-p/low-v and high-p/high-v co-occur.
        # Therefore separating p/v does NOT weaken future axis support.
        rng = random.Random(20261011)
        for _ in range(150):
            history = []
            p0 = rng.randrange(-5000000, 5000000)
            vel = rng.randrange(-2000000, 2000000)
            for i in range(7):
                p = F(p0)+F(i, 10)*vel
                width = rng.randrange(10000, 1000000)
                history.append((i*100000, [[p-width, p+width], [-100000, 100000]]))
            poly = O.infer(history)
            box = O.factorize(poly)
            for axis in (0, 1):
                for t in (0, 100000, 300000, 500000):
                    for sign in (-1, 1):
                        self.assertEqual(O.margin(poly[axis], sign, 0, 0, t), O.margin(box[axis], sign, 0, 0, t))

    def test_missing_inconsistent_and_stamps(self):
        self.assertIsNone(O.infer([(0, None)]))
        self.assertIsNone(O.infer([(0, [[0, 1], [0, 1]]), (100000, [[10000000, 10000001], [0, 1]])]))
        with self.assertRaises(ValueError):
            O.infer([(1, [[0, 1], [0, 1]]), (1, [[0, 1], [0, 1]])])


if __name__ == '__main__':
    unittest.main()
