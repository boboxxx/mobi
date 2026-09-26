import itertools
import unittest
import tempfile
from pathlib import Path

import numpy as np

from run_bayes_probe import greedy, pairwise, values
from run_opv2v_probe import (encode_box, decode_box, request_packet, request_decode,
                            delivery_expectation, subset_tables, make_actions, impacts, read_route, nonself_mask)


class PilotTests(unittest.TestCase):
    def test_known_self_removed_without_gt_matching(self):
        self_box=np.array([[-1.,-1.],[3.,-1.],[3.,1.],[-1.,1.]])
        adjacent=self_box+np.array([0.,3.])
        np.testing.assert_array_equal(nonself_mask(np.array([self_box,adjacent])),[False,True])

    def test_missing_recorded_route_is_explicitly_ineligible(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'frame.yaml'
            p.write_text('lidar_pose: [0,0,0,0,0,0]\nplan_trajectory: []\nego_speed: 0\n')
            with self.assertRaisesRegex(ValueError,'missing_or_empty'):
                read_route(p)

    def test_packet_roundtrip_and_corruption(self):
        box = np.array([[4,-1,0],[6,-1,0],[6,1,0],[4,1,0]]*2,dtype=float)
        raw = encode_box(2,7,box,.8)
        self.assertEqual(len(raw),32)
        decoded, score = decode_box(raw)
        np.testing.assert_allclose(decoded,box[:4,:2])
        self.assertAlmostEqual(score,.8,places=3)
        bad = bytearray(raw);bad[10] ^= 1
        with self.assertRaises(ValueError):decode_box(bytes(bad))

    def test_request_preserves_only_transmitted_state(self):
        path = np.array([[0.,0.],[10.,1.]])
        risk = np.array([0.,.51,.82])
        packet = request_packet(1,path,risk)
        a,b = request_decode(packet)
        self.assertEqual(len(packet),12+path.size*2+risk.size*2)
        np.testing.assert_allclose(a,path)
        np.testing.assert_allclose(b,risk,atol=.001)

    def test_erasure_expectation_against_enumeration(self):
        rng = np.random.default_rng(3)
        val = rng.normal(size=8);q=.63
        actual = delivery_expectation(val,3,q)
        for mask in range(8):
            ids = [i for i in range(3) if mask >> i & 1]
            expected = 0
            for outcomes in itertools.product([0,1],repeat=len(ids)):
                received = sum((1 << i)*x for i,x in zip(ids,outcomes))
                prob = np.prod([q if x else 1-q for x in outcomes])
                expected += prob*val[received]
            self.assertAlmostEqual(actual[mask],expected)
        np.testing.assert_allclose(delivery_expectation(val,3,0),val[0])
        np.testing.assert_allclose(delivery_expectation(val,3,1),val)

    def test_complementary_two_action_messages(self):
        # Two moving actions, each blocked by a different message. A distractor
        # improves an unrelated tie score but cannot improve the decision.
        risk = np.array([[0,1,0],[0,0,1],[0,0,0.]])
        action,regret,_ = subset_tables(np.zeros(3),risk,np.array([1.,0.,.1]))
        self.assertEqual(action[0],1)
        self.assertEqual(action[3],0)
        self.assertGreater(regret[1],regret[3])
        self.assertGreater(regret[2],regret[3])
        value=np.array([0,0,0,1,.1,.1,.1,1.1])
        self.assertEqual(pairwise(value,2,np.array([0,0,1.])),3)
        self.assertNotEqual(greedy(value,2,np.array([0,0,1.])),3)

    def test_bayesian_two_zone_example_without_hidden_outcome(self):
        deps=np.array([[0,0],[1,1]])
        val,haz,prog=values(np.array([.1,.1]),deps,np.array([0.,1.]),
                            np.zeros(2),np.zeros(2),1.,alpha=.05)
        np.testing.assert_allclose(val,[0,0,0,.81],atol=1e-12)
        np.testing.assert_allclose(haz,0)

    def test_geometry_known_blocker_and_empty_receiver(self):
        shapes,base,_=make_actions(np.array([[0.,0.],[20.,0.]]),'route_prefix')
        box=np.array([[[14.,-1.],[16.,-1.],[16.,1.],[14.,1.]]])
        m=impacts(box,np.array([.9]),shapes)
        self.assertEqual(m[0,0],0)
        self.assertEqual(m[0,1],0)
        self.assertEqual(m[0,-1],.9)
        action,regret,_=subset_tables(np.zeros(len(base)),m,base)
        self.assertNotEqual(action[0],action[1])
        self.assertGreater(regret[0],0)
        self.assertEqual(regret[1],0)


if __name__ == '__main__':unittest.main()
