import unittest
from core import CONFIGS, PROVIDER, deliver, joint_success, run_episode, select_messages
import random


class CoreTests(unittest.TestCase):
    def test_contention_same_channel_cannot_complete_pair(self):
        self.assertEqual(joint_success(["A0","B0"], CONFIGS["contention"]), 0)
        for seed in range(20):
            self.assertLessEqual(len(deliver(["A0","B0"], CONFIGS["contention"], random.Random(seed))), 1)

    def test_joint_selector_diversifies_contention(self):
        chosen = select_messages("set_joint", {}, 0, CONFIGS["contention"])
        self.assertEqual({PROVIDER[x].region for x in chosen}, {"A","B"})
        self.assertEqual(len({PROVIDER[x].channel for x in chosen}), 2)

    def test_independent_selector_uses_best_marginals(self):
        chosen = select_messages("set_independent", {}, 0, CONFIGS["contention"])
        self.assertEqual(set(chosen), {"A0","B0"})

    def test_full_info_safe_progress(self):
        r=run_episode("full_info","contention","hazard_a",0,false_free=0,false_occupied=0)
        self.assertEqual(r["unsafe_go_fraction"],0)
        self.assertEqual(r["decision_delay_cycles"],0)

    def test_network_delivery_has_one_cycle_delay(self):
        r=run_episode("coverage_greedy","ideal","free",0,false_free=0,false_occupied=0,horizon=5)
        self.assertEqual(r["first_go_cycle"],1)

    def test_no_comm_never_goes(self):
        r=run_episode("no_comm","ideal","free",0)
        self.assertEqual(r["progress_fraction"],0)

    def test_permanent_block_no_progress(self):
        for method in ("coverage_greedy","set_joint","full_info"):
            self.assertEqual(run_episode(method,"ideal","permanent_block",1)["progress_fraction"],0)


if __name__ == "__main__": unittest.main()
