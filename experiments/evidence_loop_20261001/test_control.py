import unittest
from types import SimpleNamespace
from control import TickControl


def state(frame=0,speed=0):return dict(frame=frame,x=0.,y=0.,yaw=0.,speed=speed,body_vertices=[[x,y,0.] for x in [-1.8,1.8] for y in [-.9,.9] for z in [0,1]])

def region(expiry=.4):return SimpleNamespace(center=(0.,0.),yaw=0.,low=(-2.3,-1.3),high=(2.3,1.3),margin=.03,expires=expiry)


class Tests(unittest.TestCase):
    def test_one_tick_then_backup_without_receiver(self):
        c=TickControl([.078,.077,.077,.2]);self.assertTrue(c.issue(region(),state(),0,.13));self.assertEqual(c.command(0)[2],'COMMITTED');self.assertEqual(c.command(1),(0.,1.,'FULL_BRAKE'));self.assertEqual(c.command(100),(0.,1.,'FULL_BRAKE'))
    def test_expiry_and_missing_cannot_authorize(self):
        c=TickControl([.078,.077,.077,.2]);self.assertFalse(c.issue(None,state(),0,0));self.assertFalse(c.issue(region(),state(),0,.2));self.assertFalse(c.issue(region(),dict(state(),x=1.),0,.1))
    def test_breach_latches(self):
        c=TickControl([.078,.077,.077,.2]);self.assertTrue(c.issue(region(),state(),0,.1));c.observe(state(4,.1));self.assertEqual(c.breach,'STOP_TIME');self.assertFalse(c.issue(region(2),state(4),4,.3));self.assertEqual(c.command(4)[2],'FULL_BRAKE')


if __name__=='__main__':unittest.main()
