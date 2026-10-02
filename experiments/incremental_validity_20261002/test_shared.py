import unittest
import numpy as np
import test_patch
from patch import body, repair
from efficient_renew import repair as old_repair
from native_pack import pack as old_fallback
from projection_once import projections
from baseline_shared import repair as shared_old
from patch_shared import repair as shared_patch
from fallback_shared import pack as shared_fallback


class SharedTests(unittest.TestCase):
    def test_all_projection_fields_bit_identical_for_heterogeneous_origins_and_ages(self):
        rng = np.random.default_rng(61)
        fixture = test_patch.PatchTests();fixture.setUp()
        for n in [1, 17, 3001]:
            points = rng.uniform([-4, -4, -2], [4, 4, .8], size=(n, 3))
            origins = rng.uniform([-1, -1, .55], [1, 1, 6], size=(n, 3))
            observed = .2 - rng.uniform(0, .19, size=n)
            encoded = body.encode_source(points, origins, observed, .2)
            a = projections(*encoded, fixture.profiles, fixture.scope, fixture.contract)
            b = body.projections(*encoded, fixture.profiles, fixture.scope, fixture.contract)
            for name in a:
                for key in a[name]:
                    self.assertTrue(np.array_equal(a[name][key], b[name][key]), (n, name, key))
            if len(a['small']['witnesses']):
                old = a['other']['witnesses'].copy()
                a['small']['witnesses'][:] = 0
                self.assertTrue(np.array_equal(a['other']['witnesses'], old))

    def test_empty_crossing_and_invalid_age_match_original(self):
        fixture = test_patch.PatchTests();fixture.setUp()
        encoded = body.encode_source(np.array([[0., 0., 1.]]), fixture.origin, 0., 0.)
        for fn in [projections, body.projections]:
            result = fn(*encoded, fixture.profiles, fixture.scope, fixture.contract)
            self.assertEqual(len(result['small']['ray_indices']), 0)
            with self.assertRaises(ValueError):
                fn(encoded[0], encoded[1], 300_000, fixture.profiles, fixture.scope, fixture.contract)

    def test_packet_bytes_match_all_original_sources(self):
        fixture = test_patch.PatchTests();fixture.setUp()
        args = fixture.args()
        self.assertEqual(shared_old(*args), old_repair(*args))
        for strategy in ['nearest', 'greedy']:
            blob = shared_patch(*args, strategy=strategy)
            self.assertEqual(blob, repair(*args, strategy=strategy))
            self.assertTrue(body.verify(blob, fixture.profiles, fixture.scope, fixture.contract,
                                        fixture.motion, None, .07, 0))
        self.assertEqual(shared_fallback(*args[1:]), old_fallback(*args[1:]))


if __name__ == '__main__':
    unittest.main()
