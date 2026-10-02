import json, os, unittest
import numpy as np
from thin import delete_redundant
from native_pack import select, pack
import test_thin
from compress import pack as reference_greedy
from thin import pack as reference_thin


@unittest.skipUnless(os.environ.get('MOBI_COVER_LIBRARY'), 'Compiled cover library not configured')
class NativeTests(unittest.TestCase):
    def test_both_native_heuristics_match_independent_discrete_references(self):
        rng = np.random.default_rng(921)
        for _ in range(100):
            n, cells = 29, 61
            cover = rng.random((n, cells)) < .18
            cover[np.arange(cells) % n, np.arange(cells)] = True
            neighborhoods = {i: np.flatnonzero(cover[i]) for i in range(n)}
            lengths = np.asarray([len(neighborhoods[i]) for i in range(n)])
            ptr = np.concatenate(([0], np.cumsum(lengths)))
            cols = np.concatenate(list(neighborhoods.values()))
            costs = {i: 1 + i % 5 for i in range(n)}
            order = sorted(range(n), key=lambda i: (-costs[i] / max(1, lengths[i]), i))
            self.assertEqual(select(ptr, cols, order, cells, 0).tolist(),
                             delete_redundant(neighborhoods, costs, cells))
            missing = np.ones(cells, dtype=bool)
            chosen = []
            while missing.any():
                gain = cover[:, missing].sum(axis=1)
                i = int(np.argmax(gain))
                self.assertGreater(gain[i], 0)
                chosen.append(i)
                missing[cover[i]] = False
            self.assertEqual(select(ptr, cols, np.arange(n), cells, 1).tolist(), chosen)

    def test_invalid_graphs_rejected_before_memory_access(self):
        for ptr, cols, order in [([0, 2], [0], [0]), ([0, 1], [3], [0]),
                                 ([0, 2], [0, 0], [0]), ([0, 1], [0], [2])]:
            with self.assertRaises(ValueError):
                select(ptr, cols, order, 2, 0)

    def test_actual_packet_bytes_and_receiver_match_both_references(self):
        fixture = test_thin.PacketTests()
        fixture.setUp()
        for strategy, reference in [('greedy', reference_greedy), ('thin', reference_thin)]:
            b = pack(*fixture.args(), strategy=strategy)
            self.assertEqual(b, reference(*fixture.args()))
            self.assertTrue(fixture.profiles)
            from thin import body
            self.assertTrue(body.verify(b, fixture.profiles, fixture.scope, fixture.contract,
                                        fixture.motion, None, .02, 0))
