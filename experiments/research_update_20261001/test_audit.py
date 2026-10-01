import itertools
import unittest
import audit_baselines as audit
from validity_scheduler import advance, choose, sufficient, solve


class AuditTests(unittest.TestCase):
    def test_collision_aware_baseline_matches_frozen_joint_policy(self):
        rows = audit.state_audit()
        self.assertTrue(all(r['selection_mismatches'] == 0 for r in rows if r['config'] != 'ideal'))

    def test_existing_contention_changes_conditional_marginals(self):
        # If both 0-channel senders contend, each wins with probability 1/2.
        self.assertEqual(.5 * audit.core.PROVIDER['A0'].marginal, .46)
        self.assertNotEqual(.46, audit.core.marginal_success(audit.core.PROVIDER['A0'], audit.core.CONFIGS['contention']))

    def test_commit_guard_expires_old_free_evidence(self):
        self.assertFalse(sufficient((2, 1), (2, 6), (0, 1), guard=1))
        self.assertTrue(sufficient((1, 2), (2, 6), (0, 1), guard=1))

    def test_renewal_order_matters(self):
        # Two transmissions, one slot each, both regions initially unknown.
        ttl=(2, 6); initial=(3, 7)
        short_first=advance(advance(initial, ttl, 0), ttl, 1)
        long_first=advance(advance(initial, ttl, 1), ttl, 0)
        self.assertFalse(sufficient(short_first, ttl, (0, 1)))
        self.assertTrue(sufficient(long_first, ttl, (0, 1)))
        self.assertEqual(choose('finite_horizon', initial, ttl, (0, 1), horizon=2, success_p=1), 1)

    def test_oracle_agrees_with_bruteforce(self):
        ttl=(2,4); initial=(3,5); horizon=3
        rewards=[]
        for schedule in itertools.product((None,0,1), repeat=horizon):
            ages=initial; reward=cost=0
            for action in schedule:
                ages=advance(ages,ttl,action)
                reward+=sufficient(ages,ttl,(0,1))
                cost+=action is not None
            rewards.append((reward,-cost))
        expected=max(rewards)
        result=solve(initial,ttl,(0,1),1,horizon,1.)
        self.assertEqual((result[0],-result[1]),expected)

    def test_unreachable_validity_does_not_manufacture_evidence(self):
        self.assertEqual(choose('finite_horizon',(2,2),(1,1),(0,1),guard=1),None)


if __name__ == '__main__':unittest.main()
