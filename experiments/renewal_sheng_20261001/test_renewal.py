import itertools
import math
import unittest
from scheduler import advance, choose, solve, valid
from certificate import lifetime, supports
from run_suite import episode, stress


class RenewalTests(unittest.TestCase):
    def test_deterministic_exhaustive_reference(self):
        for ttl,service,guard in [((2,6),1,1),((3,7),2,1),((3,4,6),1,2)]:
            initial=tuple(t+1 for t in ttl); required=tuple(range(len(ttl))); scores=[]
            for actions in itertools.product((None,)+required,repeat=3):
                ages=initial; score=cost=0
                for action in actions:
                    ages=advance(ages,ttl,action,True,service)
                    score+=valid(ages,ttl,required,guard);cost+=action is not None
                scores.append((score,-cost))
            got=solve(initial,ttl,required,guard,service,3,1.)
            self.assertEqual((got[0],-got[1]),max(scores))

    def test_service_consumes_validity(self):
        self.assertEqual(advance((4,8),(3,7),0,True,2),(2,8))
        self.assertFalse(valid((2,2),(2,6),(0,1),1))

    def test_group_refresh_repairs_long_first(self):
        self.assertEqual(choose('group_refresh',(3,7),(2,6),(0,1)),1)
        self.assertIsNone(choose('group_refresh',(1,1),(6,6),(0,1)))

    def test_missing_coverage_refuses(self):
        self.assertEqual(lifetime(30,.2,10,2,covered=False),0)
        self.assertEqual(lifetime(30,.2,10,2,observed_free=False),0)
        self.assertEqual(lifetime(.1,.2,10,2),0)

    def test_reachability_root(self):
        t=lifetime(30,.5,10,2,.1)
        self.assertAlmostEqual(10*(t+.1)+(t+.1)**2,29.5)
        self.assertAlmostEqual(lifetime(20,0,10,0),2)
        self.assertTrue(math.isinf(lifetime(20,0,0,0)))

    def test_no_time_reversal_or_boundary_equality(self):
        self.assertFalse(supports(2,1,3,1,10))
        self.assertFalse(supports(0,1,2,1,3))
        self.assertTrue(supports(0,1,2,.5,3))

    def test_evaluation_does_not_trust_overestimated_ttl(self):
        r=episode('edf',dict(ttl=(3,7),true_ttl=(1,1),p=1.),0,20)
        self.assertEqual(r['valid_fraction'],0)
        self.assertGreater(r['false_valid_fraction'],0)

    def test_bounded_stress(self):
        self.assertEqual(stress(1000)['bounded_model_violations'],0)


if __name__=='__main__':unittest.main()
