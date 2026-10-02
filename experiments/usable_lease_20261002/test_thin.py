import hashlib, json, unittest
import numpy as np
from thin import body, pack, delete_redundant


class CoverTests(unittest.TestCase):
    def test_random_deletion_preserves_every_required_cell_and_is_minimal(self):
        rng = np.random.default_rng(413)
        for _ in range(24):
            n, m = 41, 29
            cover = rng.random((m, n)) < .22
            cover[np.arange(n) % m, np.arange(n)] = True
            neighborhoods = {i: np.flatnonzero(cover[i]) for i in range(m)}
            chosen = delete_redundant(neighborhoods, {i: 1 + i % 5 for i in range(m)}, n)
            self.assertTrue(cover[chosen].any(axis=0).all())
            for i in chosen:
                self.assertFalse(cover[[j for j in chosen if j != i]].any(axis=0).all())

    def test_incomplete_and_duplicate_cover_rejected(self):
        with self.assertRaises(ValueError):
            delete_redundant({0: np.array([0])}, {0: 1}, 2)
        with self.assertRaises(ValueError):
            delete_redundant({0: np.array([0, 0])}, {0: 1}, 1)


class PacketTests(unittest.TestCase):
    def setUp(self):
        self.profiles = {
            'small': body.Profile(domain=3, step=.1, r_min=.2, r_max=.3,
                                  error=0, query_radius=0, speed=.2, acceleration=0),
            'other': body.Profile(domain=3, step=.1, r_min=.28, r_max=.4,
                                  error=0, query_radius=0, speed=.3, acceleration=0)}
        self.scope = body.Scope('test', 'map', (0., 0.), .6)
        self.contract = body.Contract()
        self.motion = body.Motion(half_length=.3, half_width=.2, acceleration=0, yaw_rate=0)
        axis = np.arange(-1.5, 1.51, .05)
        x, y = np.meshgrid(axis, axis)
        self.points = np.column_stack([x.ravel() / .6, y.ravel() / .6, np.full(x.size, -1.)])
        self.origin = np.array([0., 0., 3.])

    def args(self, points=None, observed=0., reference=0.):
        return (self.points if points is None else points, self.origin, observed,
                reference, self.profiles, self.scope, self.contract, self.motion, None, .4, 0)

    def test_cross_class_ages_and_actual_source_membership(self):
        ages = np.linspace(0, .05, len(self.points))
        args = self.args(observed=.1 - ages, reference=.1)
        blob = pack(*args)
        self.assertIsNotNone(blob)
        self.assertTrue(body.verify(blob, *args[4:9], .12, 0))
        _, o, r = body.decode(body.canonical(json.loads(blob)['raw']), self.profiles,
                              self.scope, self.contract)
        source_o, source_r, _ = body.encode_source(*args[:4])
        self.assertTrue(np.array_equal(o, source_o))
        source_set = {tuple(row) for row in source_r}
        self.assertTrue(all(tuple(row) in source_set for row in r))

    def test_unobserved_hole_is_not_filled(self):
        points = self.points[np.linalg.norm(self.points[:, :2], axis=1) > .8]
        self.assertIsNone(pack(*self.args(points)))

    def test_expired_rays_and_packet_geometry_corruption_rejected(self):
        with self.assertRaises(ValueError):
            pack(*self.args(observed=0., reference=.3))
        blob = pack(*self.args())
        self.assertIsNotNone(blob)
        packet = json.loads(blob)
        packet['raw']['payload']['rays'] = packet['raw']['payload']['rays'][:1]
        packet['raw']['sha256'] = hashlib.sha256(body.canonical(packet['raw']['payload'])).hexdigest()
        self.assertFalse(body.verify(body.canonical(packet), self.profiles, self.scope,
                                    self.contract, self.motion, None, .02, 0))
        self.assertFalse(body.verify(blob, self.profiles, self.scope, self.contract,
                                    self.motion, None, .4, 0))


if __name__ == '__main__':
    unittest.main()
