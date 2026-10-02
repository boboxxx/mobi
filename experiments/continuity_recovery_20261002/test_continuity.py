import copy, hashlib, json, sys, unittest
from pathlib import Path
import numpy as np
from continuity import body, LegacyReceiver, Receiver, collar, step, wire, reference_speed


class ContinuityTests(unittest.TestCase):
    def setUp(self):
        self.profiles = dict(small=body.Profile(domain=3., step=.05, r_min=.2, r_max=.4,
                                               error=0, query_radius=0, speed=.5, acceleration=0),
                             other=body.Profile(domain=3., step=.05, r_min=.28, r_max=.4,
                                               error=0, query_radius=0, speed=.5, acceleration=0))
        self.scope = body.Scope('test', 'map', (0., 0.), .6)
        self.contract = body.Contract()
        self.motion = body.Motion(half_length=.3, half_width=.2, acceleration=0., yaw_rate=0.)
        axis = np.arange(-1.8, 1.801, .04);x, y = np.meshgrid(axis, axis)
        self.w = np.column_stack([x.ravel(), y.ravel()])
        self.points = np.column_stack([self.w / .6, np.full(len(self.w), -1.)])
        self.origin = np.array([0., 0., 3.])
        self.initial = body.pack(self.points, self.origin, 0., 0., self.profiles,
                                 self.scope, self.contract, self.motion, None, .25, 0)
        self.assertIsNotNone(self.initial)
        self.legacy = LegacyReceiver(self.profiles, self.contract, 'test', 'map')
        self.assertTrue(self.legacy.accept(self.initial, self.scope, self.motion, .02))
        self.rx = Receiver(self.profiles, self.contract)
        self.anchor = self.rx.register(self.legacy, self.initial, self.scope, self.motion)
        low, high, margin = body.envelope(self.motion, 0., .02)
        keep = body.box_distance(self.w, low, high) >= margin + .4
        self.hidden = self.points[keep]

    def make(self, times=(.15, .3, .45, .6, .75, .9), strategy='greedy'):
        return wire(self.anchor, [step(self.hidden, self.origin, t, t, self.profiles,
                                      self.contract, self.anchor, .25, i + 1, strategy)
                                 for i, t in enumerate(times)])

    def test_proved_initial_state_and_partial_collars_restore_fact(self):
        for strategy in ['nearest', 'greedy']:
            b = self.make(strategy=strategy);self.assertIsNotNone(b)
            rx = copy.deepcopy(self.rx)
            self.assertTrue(rx.accept(b, 1., .05))
            self.assertEqual(rx.last['endpoint_us'], 1_150_000)
        # No new ray traverses the entire hidden interior. A current-only proof
        # cannot infer it free, and old legacy action authority remains expired.
        self.assertIsNone(body.pack(self.hidden, self.origin, .9, .9, self.profiles,
                                    self.scope, self.contract, self.motion, None, .25, 6))
        self.assertFalse(copy.deepcopy(self.legacy).accept(self.initial, self.scope, self.motion, 1.))

    def test_temporal_gap_and_removed_step_reject(self):
        p = json.loads(self.make());del p['steps'][2]
        self.assertFalse(self.rx.accept(body.canonical(p), 1., .05))
        self.assertIsNotNone(self.make(times=(.15, .6)))
        self.assertFalse(self.rx.accept(self.make(times=(.15, .6)), .62))

    def test_missing_ingress_collar_cannot_extend(self):
        points = self.hidden[self.hidden[:, 0] < 0]
        self.assertIsNone(step(points, self.origin, .15, .15, self.profiles,
                               self.contract, self.anchor, .25, 1))

    def test_unregistered_anchor_schema_mismatch_and_corruption(self):
        blob = self.make()
        self.assertFalse(Receiver(self.profiles, self.contract).accept(blob, 1.))
        with self.assertRaises(ValueError):
            self.rx.register(LegacyReceiver(self.profiles, self.contract, 'test', 'map'),
                             self.initial, self.scope, self.motion)
        p = json.loads(blob);p['steps'][0]['payload']['rays'] = p['steps'][0]['payload']['rays'][:1]
        # A fresh checksum cannot turn an unexcluded collar into evidence.
        p['steps'][0]['sha256'] = hashlib.sha256(body.canonical(p['steps'][0]['payload'])).hexdigest()
        self.assertFalse(self.rx.accept(body.canonical(p), 1.))
        p = json.loads(blob);p['steps'][0]['payload']['scope']['plane_z'] += .1
        p['steps'][0]['sha256'] = hashlib.sha256(body.canonical(p['steps'][0]['payload'])).hexdigest()
        self.assertFalse(self.rx.accept(body.canonical(p), 1.))

    def test_replay_future_and_exact_expiry_reject(self):
        blob = self.make()
        self.assertFalse(copy.deepcopy(self.rx).accept(blob, .5))
        self.assertFalse(copy.deepcopy(self.rx).accept(blob, 1.15))
        self.assertFalse(copy.deepcopy(self.rx).accept(blob, 1., .15))
        self.assertTrue(self.rx.accept(blob, 1., .05))
        self.assertFalse(self.rx.accept(blob, 1., .05))

    def test_fixed_region_guard_and_straddling_tiles(self):
        from dataclasses import replace
        with self.assertRaises(ValueError):
            self.rx.register(self.legacy, self.initial, self.scope, replace(self.motion, vx=.1))
        p = self.profiles['small'];encoded = body.encode_source(self.hidden, self.origin, .15, .15)
        c = collar(p, self.anchor, .25, encoded[1], encoded[2])
        low, high, margin = body.envelope(self.motion, 0., p.clock)
        # Some centers inside K belong to tiles straddling its boundary; they
        # still require actual rays and must not be removed as known interior.
        distance = body.box_distance(c, low, high)
        self.assertTrue(np.any(distance < margin + p.r_max))

    def test_wrong_dynamics_version_and_changed_contract_reject(self):
        p = json.loads(self.make());p['dynamics'] = 'initial-speed-only'
        self.assertFalse(self.rx.accept(body.canonical(p), 1.))
        p = json.loads(self.make());p['steps'][0]['payload']['profiles']['small']['clock'] = 0.
        p['steps'][0]['sha256'] = hashlib.sha256(body.canonical(p['steps'][0]['payload'])).hexdigest()
        self.assertFalse(self.rx.accept(body.canonical(p), 1.))

    def test_observation_age_future_acceleration_cross_term_is_not_dropped(self):
        from dataclasses import replace
        p = replace(self.profiles['small'], acceleration=3.)
        encoded = body.encode_source(self.hidden, self.origin, 0., .1)
        v = reference_speed(p, encoded[1], encoded[2]).speed
        self.assertAlmostEqual(v, p.speed + .3)
        age, future = .1, .27
        separate = p.speed * age + .5 * p.acceleration * age**2 + v * future + .5 * p.acceleration * future**2
        combined = p.speed * (age + future) + .5 * p.acceleration * (age + future)**2
        self.assertAlmostEqual(separate, combined)
        self.assertGreater(separate, p.speed * age + .5 * p.acceleration * age**2 + p.speed * future + .5 * p.acceleration * future**2)

    def test_newest_timestamp_premise_survives_geometry_selection(self):
        from dataclasses import replace
        profiles = {n: replace(p, acceleration=3.) for n, p in self.profiles.items()}
        # Latest actual observation does not cross the queried plane; it must
        # nevertheless travel with the packet if its timestamp bounds speed.
        points = np.vstack([self.hidden, [0., 0., 1.]])
        observed = np.full(len(points), .13);observed[-1] = .149
        raw = step(points, self.origin, observed, .15, profiles, self.contract,
                   self.anchor, .25, 1)
        self.assertIsNotNone(raw)
        p, o, rays = body.decode(body.canonical(raw), profiles, self.scope, self.contract)
        self.assertEqual(int(rays[:, 4].max()), 149_000)
        self.assertAlmostEqual(reference_speed(profiles['small'], rays, p['reference_us']).speed, .503)

    def test_independent_interval_observer_preserves_hidden_interior(self):
        # 1D set-membership reference: unknown starts outside [-1.5,1.5].
        # At each sample, observed side collars exclude [.4,1.5] and its
        # reflection, while [-.4,.4] remains completely invisible. Propagate
        # ALL unknown intervals by bounded travel; do not invent an empty prior.
        left, right = -1.5, 1.5
        times = np.arange(0, 1.01, .1)
        for t in times[1:]:
            left += .5 * .1;right -= .5 * .1
            self.assertLess(left, -.4);self.assertGreater(right, .4)
            left, right = min(left, -1.5), max(right, 1.5)
        # Without observations the initial clearance eventually vanishes.
        self.assertGreaterEqual(-1.5 + .5 * 3., 0.)


if __name__ == '__main__':
    unittest.main()
