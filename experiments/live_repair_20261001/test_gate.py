import sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'evidence_loop_20261001'))
from control import TickControl


class GateTests(unittest.TestCase):
    def test_cached_region_reuse_does_not_extend_expiry(self):
        r=SimpleNamespace(center=(0.,0.),yaw=0.,low=(-2.3,-1.3),high=(2.3,1.3),margin=.03,expires=.4)
        c=TickControl([.07732,.077,.077,.2]);s=dict(x=0.,y=0.,yaw=0.,speed=0.)
        self.assertTrue(c.issue(r,s,10,.13));self.assertTrue(c.issue(r,s,11,.18));self.assertFalse(c.issue(r,s,12,.23));self.assertEqual(c.issued,2);self.assertEqual(c.command(12),(0.,1.,'FULL_BRAKE'));self.assertEqual(c.active['complete'],15)
    def test_no_cache_cannot_issue_while_new_proof_is_pending(self):
        c=TickControl([.07732,.077,.077,.2]);self.assertFalse(c.issue(None,dict(x=0.,y=0.,yaw=0.,speed=0.),0,.1));self.assertEqual(c.command(0),(0.,1.,'FULL_BRAKE'))


if __name__=='__main__':unittest.main()
