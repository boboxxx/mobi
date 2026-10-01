import copy,math,unittest
import numpy as np
from model import *


def record(yaw=0,stop=True):
    reference=dict(x=10.,y=-3.,yaw=yaw,speed=.5);rows=[]
    for i in range(41):rows.append(dict(phase='command' if i==0 else 'backup',x=10.+.3*math.cos(math.radians(yaw)),y=-3.+.3*math.sin(math.radians(yaw)),yaw=yaw,speed=0. if stop and i>=2 else .5))
    for r in [reference]+rows:
        c=math.cos(math.radians(yaw));s=math.sin(math.radians(yaw));r['body_vertices']=[[r['x']+c*x-s*y,r['y']+s*x+c*y,z] for x in [-2.,2.] for y in [-1.,1.] for z in [-.5,.5]]
    return dict(reference=reference,body=dict(half_length=2.,half_width=1.,offset_x=0.,offset_y=0.),rows=rows,collisions=[],features=dict(speed=.5,last_acceleration=0.,gear_is_1=1,planned_throttle=.45,planned_brake=0.,target=1.))


class ModelTests(unittest.TestCase):
    def test_joint_targets_rotation_and_stable_suffix(self):
        for yaw in [0.,45.,90.,-170.]:np.testing.assert_allclose(targets(record(yaw)),[.3,0,0,.15],atol=1e-12)
        r=record();r['rows'][-2]['speed']=.1;self.assertTrue(math.isinf(targets(r)[3]))

    def test_collision_and_incomplete_stop_cannot_be_deleted(self):
        r=record();r['collisions']=[{'frame':5}];self.assertTrue(math.isinf(targets(r)[3]));self.assertIsNone(fit([r],'state'))
        self.assertTrue(math.isinf(score(targets(record(stop=False)),np.zeros(4))))
        self.assertTrue(math.isinf(calibrate([record(stop=False)],'constant',np.zeros((1,4)))))

    def test_joint_calibration_covers_every_calibration_outcome(self):
        train=[record()];weights=fit(train,'constant');cal=[record(),record(90)]
        for vertex in cal[1]['rows'][0]['body_vertices']:vertex[0]-=.2
        q=calibrate(cal,'constant',weights)
        for r in cal:self.assertTrue(np.all(targets(r)<=predict(r,'constant',weights)+q*SCALES+1e-12))

    def test_tolerance_confidence_and_binomial_zero_failures(self):
        self.assertLess(max_score_confidence(298),.95);self.assertGreater(max_score_confidence(299),.95)
        self.assertAlmostEqual(upper_failure(0,400),1-.05**(1/400));self.assertEqual(upper_failure(400,400),1.);self.assertIsNone(upper_failure(0,0))

    def test_three_dimensional_corner_extension_is_not_ignored(self):
        r=record();r['rows'][0]['body_vertices'][0][1]=-4.25
        self.assertAlmostEqual(targets(r)[2],.25)
        del r['reference']['body_vertices']
        with self.assertRaises(KeyError):targets(r)


if __name__=='__main__':unittest.main()
