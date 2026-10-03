import sys,unittest
from pathlib import Path
import numpy as np
from bounds import Cell,rotation,value
from refined import RefinedIndex,refined_enclosures,rotation_difference
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'shape_evidence_20261002'))
from model import score,fraction

class RefinementTests(unittest.TestCase):
    def test_relative_rotation_matrix_bounds(self):
        g=np.random.default_rng(46)
        for _ in range(200):
            m=g.uniform(-3,3,3);h=g.uniform(0,.5,3);bound=rotation_difference(m,h)
            for _ in range(20):
                actual=rotation(*m).T@rotation(*g.uniform(m-h,m+h))-np.eye(3);self.assertTrue(np.all(abs(actual)<=bound+1e-12))
    def test_nested_boxes_and_scores(self):
        g=np.random.default_rng(47);origin=np.array([0.,0.,8.]);points=g.uniform([-10,-10,-1],[10,10,2],(3000,3));extent=np.array([1.8,.8,.7]);idx=RefinedIndex(points,origin);corner=np.array([[x,y,z] for x in (-1,1) for y in (-1,1) for z in (-1,1)])
        for _ in range(100):
            m=np.r_[g.uniform([-4,-4,.5],[4,4,1]),g.uniform(-.2,.2,3)];h=np.r_[g.uniform(.001,.08,3),g.uniform(.001,.03,3)];cell=Cell(tuple(m-h),tuple(m+h));c,r,inner,outer=refined_enclosures(cell,extent,np.zeros(3),np.eye(3));bound=idx.bound(cell,extent,np.zeros(3),np.eye(3));full=idx.bound(cell,extent,np.zeros(3),np.eye(3),indexed=False)
            self.assertEqual({k:v for k,v in bound.items() if k!='examined'},{k:v for k,v in full.items() if k!='examined'})
            for _ in range(10):
                p=g.uniform(cell.lo,cell.hi);rt=rotation(*p[3:]);actual=(corner*(extent+.03))@rt.T+p[:3];self.assertTrue(np.all(abs((actual-c)@r)<=outer+1e-12))
                if min(inner)>0:self.assertTrue(np.all(abs(((corner*inner)@r.T+c-p[:3])@rt)<=extent+.03+1e-12))
                self.assertLessEqual(value(bound),fraction(score(points,origin,p[:3],rt,extent)))
    def test_correlated_counts_improve_empty_ray_bound(self):
        g=np.random.default_rng(48);origin=np.array([0.,0.,8.]);points=np.c_[g.uniform(-2,2,(10000,2)),np.full(10000,-2.)];c=Cell((-.03,-.03,.9,-.005,-.005,-.005),(.03,.03,1.1,.005,.005,.005));old=RefinedIndex(points,origin,count_refinement=False).bound(c,[1,.5,.7],np.zeros(3),np.eye(3));new=RefinedIndex(points,origin).bound(c,[1,.5,.7],np.zeros(3),np.eye(3));self.assertEqual(value(new),1);self.assertLess(value(old),value(new))
if __name__=='__main__':unittest.main()
