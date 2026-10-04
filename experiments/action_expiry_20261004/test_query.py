import unittest
from fractions import Fraction
from query_kernel import Evidence, Motion, decision, horizon, balls, pose

HULLS = [[[-10, -10], [10, -10], [10, 10], [-10, 10]]]
EXTENT = (.8, .4, .5)
PRED = dict(status='supported', mean_um=[0, 0], centers_um=[[0, 0]],
            single_scale_um=50000, modes_scale_um=50000)
THRESHOLD = dict(supported=Fraction(2), fallback_um=0)


class QueryTests(unittest.TestCase):
    def test_strict_maximal_horizon_against_integer_enumeration(self):
        for speed in (0, 1, 5000000):
            for acceleration in (0, 3000000):
                motion = Motion(speed, acceleration, 257)
                for gap in (-2, 0, 1, 8, 64, 1000000):
                    safe = [t for t in range(258) if 2*10**12*gap > 2*10**6*speed*t+acceleration*t*t]
                    self.assertEqual(horizon(27+gap, 17, 10, motion), max(safe) if safe else 0)

    def test_source_epoch_expiry_and_no_certificate_transfer(self):
        e = Evidence(HULLS, EXTENT, PRED, THRESHOLD, 'component_mean', 1000000)
        proposal = e.query([6000000, 0])
        self.assertEqual(proposal['proposal_valid_until_us'], 1000000+proposal['lower_us'])
        self.assertTrue(decision(proposal, 1000000, 220000)['geometry_eligible'])
        self.assertFalse(decision(proposal, 1000000, 220000)['deployment_authorized'])
        self.assertFalse(decision(proposal, proposal['proposal_valid_until_us'], 1)['geometry_eligible'])
        self.assertFalse(decision(proposal, 999999, 1)['geometry_eligible'])

    def test_disjoint_supported_sets_refuse_without_labels(self):
        pred = dict(PRED, mean_um=[50000000, 0])
        e = Evidence(HULLS, EXTENT, pred, THRESHOLD, 'component_mean', 0)
        self.assertEqual(e.status, 'refused_disjoint_supported_sets')
        self.assertEqual(e.query([0, 0])['lower_us'], 0)
        self.assertFalse(decision(e.query([0, 0]), 0, 1)['geometry_eligible'])

    def test_empty_and_multiple_mode_union(self):
        empty = Evidence([], EXTENT, PRED, THRESHOLD, 'component_mean', 0)
        self.assertEqual(empty.status, 'refused_empty_observation')
        pred = dict(PRED, centers_um=[[50000000, 0], [0, 0]])
        e = Evidence(HULLS, EXTENT, pred, THRESHOLD, 'component_modes', 0)
        self.assertEqual(e.status, 'bounded')

    def test_query_radius_and_motion_can_only_shorten_horizon(self):
        e = Evidence(HULLS, EXTENT, PRED, THRESHOLD, 'component_mean', 0)
        ages = [e.query([4000000, 0], r)['lower_us'] for r in (0, 750000, 2500000, 5000000)]
        self.assertEqual(ages, sorted(ages, reverse=True))
        self.assertLessEqual(e.query([4000000, 0], motion=Motion(10000000, 6000000))['lower_us'], ages[1])

    def test_fallback_has_exact_joint_witness(self):
        e = Evidence(HULLS, EXTENT, dict(status='fallback'), THRESHOLD, 'component_mean', 0)
        self.assertEqual(e.status, 'bounded')
        w = e.witness
        self.assertTrue(any(balls.feasible(w['point_num'], c, e.radius_um, w['point_den']) for c in e.ball_groups))
        from query_kernel import rect_contains
        self.assertTrue(any(rect_contains(r, w['point_num'], w['point_den']) for r in e.rects))
        self.assertGreater(e.query([6000000, 0])['lower_us'], 0)

    def test_no_silent_quantization_or_invalid_contract(self):
        with self.assertRaises(ValueError):
            Evidence([[[1.5, 0]]], EXTENT, PRED, THRESHOLD, 'component_mean', 0)
        with self.assertRaises(ValueError):
            Evidence(HULLS, EXTENT, PRED, THRESHOLD, 'component_mean', True)
        with self.assertRaises(ValueError):
            Motion(-1, 0)
        e = Evidence(HULLS, EXTENT, PRED, THRESHOLD, 'component_mean', 0)
        with self.assertRaises(ValueError):
            e.query([1, 0], -1)
        with self.assertRaises(ValueError):
            decision(e.query([6000000, 0]), 0, 0)


if __name__ == '__main__':
    unittest.main()
