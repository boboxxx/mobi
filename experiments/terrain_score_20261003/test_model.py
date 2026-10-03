import unittest
import numpy as np
import importlib.util
from pathlib import Path
def load(name):
    spec=importlib.util.spec_from_file_location('terrain_'+name,Path(__file__).parent/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
score=load('model').score
reference=load('audit').reference
rot=load('audit').rot
class TerrainScore(unittest.TestCase):
    def test_ground_is_free_ray_above_plane(self):
        p=np.tile([0,0,0.],(8,1));s=score(p,[0,0,5],[0,0,1],np.eye(3),[1,1,1]);self.assertEqual((s['numerator'],s['denominator']),(8,8))
    def test_real_above_ground_hit_and_missing(self):
        p=np.tile([0,0,1.],(8,1));self.assertEqual(score(p,[0,0,5],[0,0,1],np.eye(3),[1,1,1])['numerator'],0);self.assertEqual(score(p[:7],[0,0,5],[0,0,1],np.eye(3),[1,1,1])['reason'],'insufficient_support')
    def test_empty_clipped_shape_retained(self):
        s=score(np.tile([0,0,-2.],(8,1)),[0,0,5],[0,0,-1],np.eye(3),[.2,.2,.2]);self.assertEqual(s['visible_count'],0);self.assertEqual(s['numerator'],0)
    def test_independent_oblique_planes(self):
        rng=np.random.default_rng(8137)
        for _ in range(100):
            p=rng.uniform(-3,3,(300,3));o=np.array([5.,4.,6.]);c=rng.uniform(-1,1,3);r=rot(rng.uniform(-3,3,3));e=rng.uniform(.1,1.5,3);s=score(p,o,c,r,e);self.assertEqual(reference(p,o,c,r,e),(s['visible_count'],s['pass_count'],s['numerator'],s['denominator']))
if __name__=='__main__':unittest.main()
