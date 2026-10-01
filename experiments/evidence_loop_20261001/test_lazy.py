import unittest
import numpy as np
from lazy_compress import choose


class LazyTests(unittest.TestCase):
    def test_matches_exhaustive_greedy_with_ties(self):
        rng=np.random.default_rng(42)
        for _ in range(60):
            neighbors={i:np.flatnonzero(rng.random(60)<.08).tolist() for i in range(100)}
            missing=set(range(60));expected=[]
            while missing:
                score,i=max((len(set(v)&missing),-i) for i,v in neighbors.items());i=-i
                if not score:expected=None;break
                expected.append(i);missing-=set(neighbors[i])
            self.assertEqual(choose(neighbors,60,100),expected)
    def test_limit_empty_and_incomplete(self):
        self.assertEqual(choose({0:[0],1:[1]},2,2),[0,1]);self.assertIsNone(choose({0:[0],1:[1]},2,1));self.assertIsNone(choose({0:[0]},2,4));self.assertEqual(choose({},0,4),[])


if __name__=='__main__':unittest.main()
