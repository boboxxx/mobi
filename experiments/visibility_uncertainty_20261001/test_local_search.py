import unittest
import numpy as np
from weighted import certify_weighted,best_uniform
from geometry import Profile
from local_search import compare_local


class LocalSearchTests(unittest.TestCase):
    def test_exact_agreement_with_exhaustive_reference(self):
        rng=np.random.default_rng(76);p=Profile(r_min=.55,r_max=.6,error=0.,domain=3,step=.1)
        for mode in ['empty','sparse','dense','hole']:
            w=rng.uniform(-4,4,(5000 if mode=='dense' else 500,2));e=rng.uniform(0,.4,len(w))
            if mode=='empty':w,e=w[:0],e[:0]
            if mode=='hole':keep=np.linalg.norm(w,axis=1)>1.5;w,e=w[keep],e[keep]
            exact=certify_weighted(w,e,p);uniform=best_uniform(w,e,p)
            for chunk in [1,128,4096]:
                fast=compare_local(w,e,p,chunk=chunk)
                self.assertAlmostEqual(exact['validity_s'],fast['validity_s'],places=12)
                self.assertAlmostEqual(uniform['validity_s'],fast['best_uniform_ttl_s'],places=12)


if __name__=='__main__':unittest.main()
