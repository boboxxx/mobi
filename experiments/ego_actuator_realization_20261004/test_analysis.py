import importlib.util
import unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('independent_ego_analyzer',Path(__file__).with_name('analyze.py'))
analyzer=importlib.util.module_from_spec(spec);spec.loader.exec_module(analyzer)


class AnalysisBoundary(unittest.TestCase):
    def test_stop_requires_three_consecutive_states(self):
        rows=lambda speeds:[dict(velocity=[v,0.,0.]) for v in speeds]
        self.assertIsNone(analyzer.stop_index(rows([0.,.03,0.,0.])))
        self.assertEqual(analyzer.stop_index(rows([.3,.02,.01,0.,.4])),1)
        self.assertIsNone(analyzer.stop_index(rows([0.,0.])))

    def test_rotated_offset_and_body_corners(self):
        body=dict(extent=[2.,1.,.5],offset=[.3,-.2,.4],rotation=[0.,0.,0.])
        row=dict(rotation=[0.,90.,0.],location=[10.,20.,3.],center=[10.2,20.3,3.4],matrix=[[0.,-1.,0.,10.],[1.,0.,0.,20.],[0.,0.,1.,3.],[0.,0.,0.,1.]])
        row['body_vertices']=[[10.2+y,20.3+x,3.4+z] for x in (-2.,2.) for y in (-1.,1.) for z in (-.5,.5)]
        self.assertLess(analyzer.body_error(body,row),1e-12)
        row['center'][0]+=.001
        with self.assertRaises(AssertionError):analyzer.body_error(body,row)


if __name__=='__main__':unittest.main()
