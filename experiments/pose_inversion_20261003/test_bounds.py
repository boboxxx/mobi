import sys,unittest
from pathlib import Path
import numpy as np
from bounds import Cell,RayIndex,enclosures,rotation,value
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'shape_evidence_20261002'))
from model import score,fraction

class BoundsTests(unittest.TestCase):
    def test_interval_lower_score_at_random_interior_poses(self):
        g=np.random.default_rng(31);origin=np.array([0.,0.,8.]);points=g.uniform([-8,-8,-1],[8,8,3],(3000,3));idx=RayIndex(points,origin);anchor=np.zeros(3);road=np.eye(3);extent=np.array([1.5,.5,.8])
        for _ in range(80):
            m=np.r_[g.uniform([-4,-4,.5],[4,4,1]),g.uniform([-.01,-3,-.01],[.01,3,.01])];h=np.r_[g.uniform(.001,.04,3),g.uniform(.001,.01,3)];cell=Cell(tuple(m-h),tuple(m+h));b=idx.bound(cell,extent,anchor,road)
            full=idx.bound(cell,extent,anchor,road,indexed=False);self.assertEqual({k:v for k,v in b.items() if k!='examined'},{k:v for k,v in full.items() if k!='examined'})
            for _ in range(10):
                pose=g.uniform(cell.lo,cell.hi);s=score(points,origin,pose[:3],rotation(*pose[3:]),extent);self.assertLessEqual(value(b),fraction(s))
    def test_containment_at_all_sampled_pose_corners(self):
        g=np.random.default_rng(4);extent=np.array([2.,1.,.7]);anchor=np.array([4.,-8.,1.]);road=rotation(0,.3,0)
        for _ in range(30):
            m=np.r_[g.normal(size=3),g.uniform(-1,1,3)];h=np.r_[[.05,.1,.02],[.01,.02,.01]];cell=Cell(tuple(m-h),tuple(m+h));c,r,inner,outer=enclosures(cell,extent,anchor,road);corners=np.array([[x,y,z] for x in [-1,1] for y in [-1,1] for z in [-1,1]])
            for _ in range(20):
                pose=g.uniform(cell.lo,cell.hi);rt=rotation(*pose[3:]);ct=anchor+road@pose[:3];actual=(corners*(extent+.03))@rt.T+ct;self.assertTrue(np.all(abs((actual-c)@r)<=outer+1e-12))
                if min(inner)>0:
                    ins=(corners*inner)@r.T+c;self.assertTrue(np.all(abs((ins-ct)@rt)<=extent+.03+1e-12))
    def test_unsupported_and_sensor_inside_retained(self):
        idx=RayIndex(np.ones((7,3))*3,np.array([-3.,0,0]));c=Cell((0,0,0,0,0,0),(0,0,0,0,0,0));self.assertEqual(value(idx.bound(c,[1,1,1],np.zeros(3),np.eye(3))),0)
        idx=RayIndex(np.ones((20,3))*3,np.zeros(3));self.assertEqual(value(idx.bound(c,[1,1,1],np.zeros(3),np.eye(3))),0)
    def test_split_covers_parent(self):
        c=Cell((-2,-1,.5,-.1,0,-.1),(2,1,1,.1,6.28,.1));a,b=c.split([1,.5,.7]);self.assertEqual(a.lo,c.lo);self.assertEqual(b.hi,c.hi);changed=[i for i in range(6) if a.hi[i]!=c.hi[i]];self.assertEqual(len(changed),1);i=changed[0];self.assertEqual(a.hi[i],b.lo[i])
    def test_empty_rays_cannot_exclude(self):
        idx=RayIndex(np.empty((0,3)),[0,0,8]);c=Cell((0,0,1,0,0,0),(0,0,1,0,0,0));self.assertEqual(value(idx.bound(c,[1,1,1],np.zeros(3),np.eye(3))),0)
if __name__=='__main__':unittest.main()
