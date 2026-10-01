import json,math,unittest
from pathlib import Path
import numpy as np
import policy_proof as pp
from strict_policy import verify,conditional_stop_gate
from tube import Policy


class ProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory=Path(__file__).resolve().parents[2]/'results/policy_evidence_20261001/geometry/packets'
        cls.blob=(cls.directory/'dense_0_free_00_v0.5_h0.4.json').read_bytes()
        p=json.loads(cls.blob);s=p['raw']['payload']['scope']
        cls.scope=pp.Scope(s['episode'],s['frame_id'],tuple(s['query']),s['plane_z'])
        cls.profiles=dict(small=pp.Profile(r_min=.2,r_max=.4,query_radius=0.,step=.05,error=0.),vehicle=pp.Profile(r_min=.55,r_max=2.5,query_radius=0.,step=.1,error=0.))
        cls.policy=Policy();cls.contract=pp.Contract();cls.yaw=p['yaw'];cls.speed=p['speed']

    def check(self,blob=None,now=1.02,**kwargs):
        args=dict(profiles=self.profiles,scope=self.scope,contract=self.contract,policy=self.policy,speed=self.speed,yaw=self.yaw,now=now);args.update(kwargs)
        return verify(self.blob if blob is None else blob,**args)

    def test_current_packet_and_conditional_stop(self):
        self.assertTrue(self.check())
        self.assertTrue(conditional_stop_gate(self.blob,self.profiles,self.scope,self.contract,self.policy,self.speed,self.yaw,1.10))
        self.assertFalse(conditional_stop_gate(self.blob,self.profiles,self.scope,self.contract,self.policy,self.speed,self.yaw,1.121))

    def test_future_reference_and_expiry(self):
        self.assertFalse(self.check(now=float(np.nextafter(1.,-np.inf))))
        self.assertFalse(self.check(now=1.4))
        self.assertTrue(self.check(now=1.3999))
        self.assertFalse(self.check(min_sequence=1))

    def test_policy_and_speed_binding(self):
        for field,value in [('speed',.0),('yaw',0.),('speed',False)]:
            p=json.loads(self.blob);p[field]=value
            self.assertFalse(self.check(blob=pp.canonical(p)))
        p=json.loads(self.blob);p['policy']['traction']=2.
        self.assertFalse(self.check(blob=pp.canonical(p)))

    def test_no_bootstrap_and_scope_substitution(self):
        p=json.loads(self.blob);p['prior']='unverified-initial-free'
        self.assertFalse(self.check(blob=pp.canonical(p)))
        self.assertFalse(self.check(scope=pp.Scope('wrong',self.scope.frame_id,self.scope.query,self.scope.plane_z)))
        self.assertFalse(self.check(profiles={'vehicle':self.profiles['vehicle']}))

    def test_corruption_rejected(self):
        p=json.loads(self.blob);p['raw']['payload']['sequence']+=1
        self.assertFalse(self.check(blob=pp.canonical(p)))

    def test_required_cells_monotone_in_horizon(self):
        pr=self.profiles['vehicle'];old=set()
        for horizon in [.2,.3,.4,.5,.6]:
            new=set(map(tuple,pp.required(pr,self.policy,.5,horizon)))
            self.assertTrue(old<=new);old=new


if __name__=='__main__':unittest.main()
