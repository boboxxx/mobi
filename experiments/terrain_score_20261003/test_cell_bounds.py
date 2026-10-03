import importlib.util,sys,unittest
from pathlib import Path
import numpy as np
from fractions import Fraction
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('terrain_point',HERE/'model.py');terrain=importlib.util.module_from_spec(spec);spec.loader.exec_module(terrain)
sys.path.insert(0,str(HERE.parent/'pose_inversion_20261003'))
from bounds import Cell,rotation,value
from cell_bounds import make_index_class
class CellBounds(unittest.TestCase):
    def test_random_point_enclosure_and_index(self):
        rng=np.random.default_rng(8228);p=rng.uniform([-3,-3,-.1],[3,3,3],(900,3));o=np.array([4.,5.,6.]);Index=make_index_class();idx=Index(p,o)
        for _ in range(80):
            m=np.r_[rng.uniform(-1,1,2),1.,rng.uniform(-.1,.1),rng.uniform(0,6),rng.uniform(-.1,.1)];h=np.r_[rng.uniform(.001,.04,3),rng.uniform(.001,.02,3)];cell=Cell(tuple(m-h),tuple(m+h));e=np.array([1.,.8,1.]);b=idx.bound(cell,e,np.zeros(3),np.eye(3));c=idx.bound(cell,e,np.zeros(3),np.eye(3),indexed=False);self.assertEqual(value(b),value(c))
            for _ in range(10):
                pose=rng.uniform(m-h,m+h);s=terrain.score(p,o,pose[:3],rotation(*pose[3:]),e);self.assertLessEqual(value(b),Fraction(s['numerator'],s['denominator']))
if __name__=='__main__':unittest.main()
