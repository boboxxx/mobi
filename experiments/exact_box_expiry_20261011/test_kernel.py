"""Independent analytical roots and continuous-prefix failure fixtures."""
from decimal import Decimal, localcontext
from fractions import Fraction as F
import unittest
from kernel import box_prefix, longest_prefix, sturm


def approach_root(position, speed, radius):
    # Independent quadratic formula, SI units, 80-digit Decimal.
    with localcontext() as context:
        context.prec = 80
        b = Decimal(speed)+Decimal('0.15')
        c = Decimal(position)-Decimal(radius)
        root = (-b+(b*b+Decimal(6)*c).sqrt())/Decimal(3)*Decimal(1000000)
        integer = int(root)
        return integer-1 if root == integer else integer


class Tests(unittest.TestCase):
    def test_head_on_against_decimal_analytic_root(self):
        for position in ('3', '4', '4.7'):
            state = [[int(Decimal(position)*1000000)]*2+[-5000000]*2, [0,0,0,0]]
            self.assertEqual(box_prefix(state, [0,0], 2500000), approach_root(position, '5', '2.5'))

    def test_tangency_is_unsafe_without_sign_change(self):
        # (t-3)^2 is positive at both 0 and 5, but touches zero at 3.
        self.assertEqual(longest_prefix([(F(0),F(5),sturm([9,-6,1]))], 5), 2)
        self.assertEqual(longest_prefix([(F(0),F(5),sturm([6,-5,1]))], 5), 1)

    def test_leave_and_reenter_does_not_reset_prefix(self):
        state = [[1000000,1000000,-5000000,-5000000], [0,0,0,0]]
        self.assertEqual(box_prefix(state,[0,0],200000), approach_root('1','5','0.2'))
        # At cap the point is clear again; endpoint-only permission is invalid.
        self.assertGreater(abs(1-5*.5), .2+.15*.5+1.5*.5**2)

    def test_empty_and_box_at_query(self):
        self.assertEqual(box_prefix(None,[0,0],100), 0)
        self.assertEqual(box_prefix([[-1,1,-5,5],[-1,1,-5,5]],[0,0],100), 0)

    def test_switching_normals_strictly_beats_every_fixed_normal(self):
        state = [[-1250000,-1250000,5000000,5000000], [3770000,3770000,0,0]]
        self.assertEqual(box_prefix(state,[0,0],3500000), 500000)
        # 0 lies in the convex hull of endpoint disks at lambda=13/20:
        # no single plane strictly separates 0 from both disks, although
        # the exact time-dependent tube remains disjoint for the whole cap.
        mix = F(13,20)
        x = -1250000+2500000*mix
        mixed_radius = 3500000+450000*mix
        self.assertLess(x*x+3770000**2, mixed_radius*mixed_radius)


if __name__ == '__main__':
    unittest.main(verbosity=2)
