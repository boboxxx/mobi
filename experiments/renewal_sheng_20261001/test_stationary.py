import itertools
import unittest
from scheduler import solve,advance,valid
from stationary_reference import build

class StationaryTests(unittest.TestCase):
    def test_horizon_six_end_effect_is_actual_finite_optimum(self):
        scores=[]
        for actions in itertools.product((None,0,1),repeat=6):
            ages=(3,7);reward=cost=0
            for action in actions:
                ages=advance(ages,(2,6),action,True)
                reward+=valid(ages,(2,6),(0,1),1);cost+=action is not None
            scores.append((reward,-cost))
        result=solve((3,7),(2,6),(0,1),1,1,6,1.)
        self.assertEqual((result[0],-result[1]),max(scores))
        self.assertIsNone(result[2])

    def test_stationary_does_not_postpone_forever(self):
        policy,diagnostic=build((2,6),(0,1),1,1,1.)
        self.assertEqual(policy[(3,7)],1)
        self.assertLess(diagnostic['residual'],1e-10)
        ages=(3,7);reward=0
        for _ in range(100):
            ages=advance(ages,(2,6),policy[ages],True)
            reward+=valid(ages,(2,6),(0,1),1)
        self.assertGreaterEqual(reward,79)

if __name__=='__main__':unittest.main()
