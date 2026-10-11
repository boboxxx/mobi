import itertools
import unittest
from fractions import Fraction as F
import kernel as k

def enumerate_hit(b, matrix, hazard, length):
    risk=F(0)
    for path in itertools.product(range(len(b)),repeat=length+1):
        prob=b[path[0]]
        for a,c in zip(path,path[1:]):prob*=matrix[a][c]
        if any(x in hazard for x in path):risk+=prob
    return risk

class ReferenceTests(unittest.TestCase):
    def test_first_hit_enumeration_and_union(self):
        for stay in (F(0),F(1,3),F(1)):
            matrix=((stay,1-stay),(1-stay,stay))
            for mass in (F(0),F(1,4),F(1)):
                b=(mass,1-mass)
                for length in range(5):
                    risk=k.first_hit(b,matrix,{1},length)
                    end,union=k.marginal_bounds(b,matrix,{1},length)
                    self.assertEqual(risk,enumerate_hit(b,matrix,{1},length))
                    self.assertLessEqual(end,risk)
                    self.assertLessEqual(risk,union)

    def test_endpoint_counterexample(self):
        matrix=((F(0),F(1),F(0)),(F(0),F(0),F(1)),(F(0),F(0),F(1)))
        b=(F(1),F(0),F(0))
        self.assertEqual(k.first_hit(b,matrix,{1},2),1)
        self.assertEqual(k.marginal_bounds(b,matrix,{1},2)[0],0)

    def test_model_specific_posterior(self):
        for model in k.MODELS:
            matrix=k.transition(model)
            self.assertTrue(all(sum(row)==1 for row in matrix))
            for state in range(9):
                self.assertEqual(sum(k.likelihood(model,o,state) for o in range(4)),1)
            for obs in range(4):self.assertEqual(sum(k.posterior(model,obs)),1)
        self.assertNotEqual(k.posterior(k.MODELS[0],0),k.posterior(k.MODELS[1],0))

    def test_all_small_codecs(self):
        for mask in itertools.product((False,True),repeat=7):
            for bitmap in (False,True):
                packet=k.encode(mask,0,2,F(1,20),bitmap)
                self.assertEqual(k.decode(packet)['allowed'],list(mask))
                for bad in (packet[:-1],packet+b'0',packet[:8]+bytes([packet[8]^1])+packet[9:]):
                    with self.assertRaises(ValueError):k.decode(bad)

    def test_paid_age_and_context(self):
        mask=[False,False,True,False,False,False,True]
        packet=k.encode(mask,0,2,F(1,20))
        digest=k.context_digest(0)
        check=lambda now,fee,length=2,alpha=F(1,20),d=digest:k.admissible(packet,d,length,alpha,now,fee)
        self.assertFalse(check(1_000_000,0))
        self.assertTrue(check(1_000_000,100_000))
        self.assertFalse(check(1_000_000,99_999))
        self.assertFalse(check(1_100_000,0,length=1))
        self.assertFalse(check(1_100_000,0,alpha=F(1,10)))
        self.assertFalse(check(1_100_000,0,d=k.context_digest(1)))
        self.assertFalse(check(999_999,0))
        self.assertFalse(check(1_350_000,0))
        self.assertEqual(k.decode(packet)['source'],1_000_000)

if __name__=='__main__':unittest.main()
