import unittest
import math
from fractions import Fraction as F
from method import unit, infer, conformity
from conditional import certificate, zero_failure_required, cdf
from integer_state import oracle_age, body_um


class Guarantees(unittest.TestCase):
    def test_empty_observation_does_not_supply_evidence(self):
        pred = dict(status='refused')
        self.assertEqual(conformity([], [1.,1.,1.], pred, [0.,0.], 'balanced_mean'), 0)
        self.assertEqual(infer([], [1.,1.,1.], pred, 0, 'balanced_mean')['status'], 'refused')

    def test_scale_depends_on_type_without_truth(self):
        pred = dict(status='supported', single_scale_um=50000, modes_scale_um=70000)
        self.assertEqual(unit([1.,1.,1.], pred, 'balanced_mean'), 50000)
        self.assertEqual(unit([1.,1.,1.], pred, 'balanced_modes'), 70000)
        self.assertGreater(unit([1.,1.,1.], dict(status='fallback'), 'balanced_mean'), 1000000)

    def test_zero_grants_cannot_certify(self):
        self.assertFalse(certificate([False]*200, [False]*200)['accepted'])

    def test_exact_zero_failure_threshold(self):
        n = zero_failure_required(F(1,20), F(1,20), 192)
        self.assertEqual(n, 161)
        self.assertFalse(certificate([True]*(n-1), [False]*(n-1), policies=192)['accepted'])
        self.assertTrue(certificate([True]*n, [False]*n, policies=192)['accepted'])

    def test_errors_are_not_counted_as_independent_queries(self):
        result = certificate([True,True,False], [True,False,False], policies=1)
        self.assertEqual((result['authorized_episodes'], result['failed_authorized_episodes']), (2,1))
        self.assertFalse(result['accepted'])
        with self.assertRaises(AssertionError):certificate([False], [True])

    def test_exact_tail_example(self):
        self.assertEqual(cdf(1, 3, F(1,2)), F(1,2))

    def test_rational_acceptance_boundary(self):
        c = certificate([True], [False], risk=F(1,3), delta=F(2,3))
        self.assertTrue(c['accepted'])
        self.assertLessEqual(F(*c['conditional_upper']), F(1,3))

    def test_score_boundary_keeps_age_below_exact_oracle(self):
        extent = [.1,.1,.1]
        pred = dict(status='supported', single_scale_um=50000,
                    modes_scale_um=50000, mean_um=[5000000,0],
                    centers_um=[[5000000,0]])
        for family in ('balanced_mean', 'balanced_modes'):
            xy = [5., .02]
            hulls = [[[500,0]]]
            q = conformity(hulls, extent, pred, xy, family)
            out = infer(hulls, extent, pred, q, family)
            self.assertEqual(out['status'], 'bounded')
            self.assertEqual(out['radius_um'], 20001)
            for age, query in zip(out['lower_us'], ((-6000000,0),(6000000,0))):
                self.assertLessEqual(age, oracle_age(xy, body_um(extent), query))
            larger = infer(hulls, extent, pred, 2*q, family)
            self.assertTrue(all(b <= a for a,b in zip(out['lower_us'], larger['lower_us'])))

    def test_random_selection_binomial_type_one_control(self):
        # Exact integration over random selected sample size; selected failure
        # probability 1/4 exceeds the tested target 1/5.
        mass = F(0)
        for n in range(31):
            selection_mass = F(math.comb(30,n), 2**30)
            for k in range(n+1):
                if n and cdf(k,n,F(1,5)) <= F(1,20):
                    mass += selection_mass * math.comb(n,k) * F(1,4)**k * F(3,4)**(n-k)
        self.assertLessEqual(mass, F(1,20))


if __name__ == '__main__':
    unittest.main()
