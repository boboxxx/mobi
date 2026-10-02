import unittest
import numpy as np
from shell_frontier import body,frontier,ordered
from frontier import frontier as reference


class ShellTests(unittest.TestCase):
    def test_complete_and_missing_fields_match_reference(self):
        rng=np.random.default_rng(21002)
        for index in range(10):
            p=body.Profile(domain=3,step=.1,r_min=.2,r_max=.3,error=0,query_radius=0,speed=.4,acceleration=.1)
            q=body.Profile(domain=3,step=.2,r_min=.4,r_max=.5,error=0,query_radius=0,speed=.5,acceleration=.2)
            motion=body.Motion(half_length=.3,half_width=.2,acceleration=0,yaw_rate=0,yaw=index*.1)
            scope=body.Scope('test','map',(0.,0.),.6)
            axis=np.arange(-1.5,1.51,.08);x,y=np.meshgrid(axis,axis);w=np.column_stack([x.ravel(),y.ravel()])
            if index%3==0:w=w[np.linalg.norm(w,axis=1)>.25]
            if index%3==1:w=w[w[:,0]<1.2]
            w=(w+rng.normal(0,.003,w.shape))@body.rotation(motion.yaw).T
            result=dict(witnesses=w,error=rng.choice([.01,.02],len(w)))
            profiles=dict(small=p,large=q);results={n:result for n in profiles}
            for cap in [50000,500000,2000000]:
                expected=reference(results,profiles,scope,motion,None,0,cap)
                actual=frontier(results,profiles,scope,motion,None,0,cap)
                self.assertEqual(expected['horizon_us'],actual['horizon_us'])
                for n,c in actual['classes'].items():
                    if c['nearest_unexcluded_distance_m'] is not None:
                        self.assertEqual(expected['classes'][n]['nearest_unexcluded_distance_m'],c['nearest_unexcluded_distance_m'])

    def test_history_cannot_be_expired(self):
        p=body.Profile(domain=3,step=.1,r_min=.2,r_max=.3,error=0,query_radius=0)
        m=body.Motion(half_length=.3,half_width=.2,acceleration=0,yaw_rate=0);s=body.Scope('test','map',(0.,0.),.6)
        r=body.Region((0.,0.),0.,(-.3,-.2),(.3,.2),.03,0.,.1,'parent','test')
        result=dict(witnesses=np.empty((0,2)),error=np.empty(0))
        with self.assertRaises(ValueError):frontier({'x':result},{'x':p},s,m,r,.1)

    def test_empty_fields_give_zero_and_stop_early(self):
        p=body.Profile(domain=3,step=.1,r_min=.2,r_max=.3,error=0,query_radius=0)
        m=body.Motion(half_length=.3,half_width=.2,acceleration=0,yaw_rate=0);s=body.Scope('test','map',(0.,0.),.6)
        result=dict(witnesses=np.empty((0,2)),error=np.empty(0));a=frontier({'x':result},{'x':p},s,m,None,0)
        self.assertEqual(a['horizon_us'],0);self.assertLess(a['classes']['x']['cells_examined'],a['classes']['x']['grid_cells'])


if __name__=='__main__':unittest.main()
