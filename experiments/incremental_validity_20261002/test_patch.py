import hashlib, json, unittest
import numpy as np
from patch import body, repair, gap_candidates


class PatchTests(unittest.TestCase):
    def setUp(self):
        self.profiles = dict(small=body.Profile(domain=3, step=.1, r_min=.2, r_max=.3,
                                               error=0, query_radius=0, speed=.8, acceleration=0),
                             other=body.Profile(domain=3, step=.1, r_min=.28, r_max=.4,
                                               error=0, query_radius=0, speed=1., acceleration=0))
        self.scope = body.Scope('test', 'map', (0., 0.), .6)
        self.contract = body.Contract()
        self.motion = body.Motion(half_length=.3, half_width=.2, acceleration=0, yaw_rate=0)
        axis = np.arange(-1.8, 1.81, .05)
        x, y = np.meshgrid(axis, axis)
        self.points = np.column_stack([x.ravel() / .6, y.ravel() / .6, np.full(x.size, -1.)])
        self.origin = np.array([0., 0., 3.])
        self.template = body.pack(self.points, self.origin, 0., 0., self.profiles,
                                  self.scope, self.contract, self.motion, None, .2, 0)
        self.assertIsNotNone(self.template)

    def args(self, points=None, observed=.05, reference=.05, prior=None):
        return (self.template, self.points if points is None else points, self.origin,
                observed, reference, self.profiles, self.scope, self.contract,
                self.motion, prior, .475, 1)

    def test_extended_horizon_is_fully_verified_and_actual_rays_only(self):
        for strategy in ['nearest', 'greedy']:
            diagnostic = {}
            blob = repair(*self.args(), strategy=strategy, diagnostics=diagnostic)
            self.assertIsNotNone(blob)
            self.assertEqual(diagnostic['branch'], 'patched')
            self.assertGreater(sum(diagnostic['gaps'].values()), 0)
            self.assertTrue(body.verify(blob, self.profiles, self.scope, self.contract,
                                        self.motion, None, .07, 0))
            _, o, r = body.decode(body.canonical(json.loads(blob)['raw']), self.profiles,
                                  self.scope, self.contract)
            source_o, source_r, _ = body.encode_source(self.points, self.origin, .05, .05)
            self.assertTrue(np.array_equal(o, source_o))
            self.assertTrue(all(tuple(x) in {tuple(row) for row in source_r} for x in r))

    def test_nominally_nearest_but_uncertain_ray_is_not_support(self):
        profile = self.profiles['small']
        # The nearest ray has no usable radius; the farther ray is a valid witness.
        result = dict(witnesses=np.array([[0., 0.], [.02, 0.]]),
                      error=np.array([.2, 0.]), ray_indices=np.array([4, 9]))
        ids = gap_candidates({'small': result}, {'small': profile}, self.motion,
                             {'small': np.array([[0., 0.]])})
        self.assertEqual(ids.tolist(), [9])

    def test_unknown_hole_and_expired_history_are_refused(self):
        points = self.points[np.linalg.norm(self.points[:, :2], axis=1) > .8]
        self.assertIsNone(repair(*self.args(points)))
        prior = body.Region((0., 0.), 0., (-.3, -.2), (.3, .2), .03, 0., .04,
                             'expired', 'test')
        self.assertIsNone(repair(*self.args(prior=prior)))

    def test_aged_rays_and_invalid_metadata_are_refused(self):
        self.assertIsNone(repair(*self.args(observed=0., reference=.3)))
        self.assertIsNone(repair(*self.args(), strategy='untrusted'))
        args = list(self.args());args[-1] = -1
        self.assertIsNone(repair(*args))

    def test_corrupted_new_geometry_does_not_pass_receiver(self):
        blob = repair(*self.args())
        self.assertIsNotNone(blob)
        p = json.loads(blob)
        p['raw']['payload']['rays'] = p['raw']['payload']['rays'][:1]
        p['raw']['sha256'] = hashlib.sha256(body.canonical(p['raw']['payload'])).hexdigest()
        self.assertFalse(body.verify(body.canonical(p), self.profiles, self.scope,
                                    self.contract, self.motion, None, .07, 0))


if __name__ == '__main__':
    unittest.main()
