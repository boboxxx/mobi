import copy,json,unittest
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from incremental import Verifier,pp,timing_after_verified
from local_renew import nearest
from strict_policy import verify,conditional_stop_gate


class IncrementalTests(unittest.TestCase):
    def setUp(self):
        path=Path(__file__).resolve().parents[2]/'results/policy_evidence_20261001/geometry/packets/dense_0_free_00_v0.5_h0.4.json'
        self.blob=path.read_bytes();p=json.loads(self.blob);s=p['raw']['payload']['scope']
        self.scope=pp.Scope(s['episode'],s['frame_id'],tuple(s['query']),s['plane_z'])
        self.profiles={k:pp.Profile(**v) for k,v in p['raw']['payload']['profiles'].items()}
        self.policy=pp.Policy();self.contract=pp.Contract();self.speed=.5;self.yaw=p['yaw'];self.v=Verifier()

    def check(self,blob=None,now=1.02):
        args=(blob or self.blob,self.profiles,self.scope,self.contract,self.policy,self.speed,self.yaw,now)
        self.assertEqual(self.v.verify(*args),verify(*args));return self.v.verify(*args)

    def test_current_checks_and_lost_coverage(self):
        self.assertTrue(self.check());self.assertTrue(self.check());self.assertGreater(self.v.counts['hint_hits'],0)
        p=json.loads(self.blob);payload,o,r=pp.decode(pp.canonical(p['raw']),self.profiles,self.scope,self.contract)
        r=r[:3]
        p['raw']=json.loads(pp.serialize(o,r,payload['reference_us'],self.profiles,self.scope,self.contract,.4,0))
        self.assertFalse(self.check(pp.canonical(p)))

    def test_corrupted_and_expired_packets_cannot_use_hint(self):
        self.assertTrue(self.check());self.assertFalse(self.check(now=1.4));self.assertFalse(self.check(now=float(np.nextafter(1.,-np.inf))))
        p=json.loads(self.blob);p['raw']['payload']['sequence']+=1
        self.assertFalse(self.check(pp.canonical(p)))

    def test_random_current_witness_changes_match_exhaustive(self):
        rng=np.random.default_rng(2911);profile=pp.Profile(r_min=.5,r_max=.5,query_radius=0,step=.2,error=0,speed=.1,acceleration=0,clock=0,domain=4.)
        policy=pp.Policy(half_length=.3,half_width=.2,pose_error=0,yaw_rate=0,traction=0)
        cells=pp.required(profile,policy,0.,.2)
        for trial in range(100):
            w=cells+rng.normal(0,.03 if trial%4 else .7,cells.shape)
            error=rng.uniform(0,.1,len(w));order=rng.permutation(len(w))
            if trial%7==0:order=order[:len(order)//3]
            result=dict(witnesses=w[order],error=np.round(error[order],2),ray_indices=np.arange(len(order)))
            expected=pp.coverage(result,profile,policy,0.,0.,.2)[0]
            self.assertEqual(self.v.covered(result,profile,policy,0.,0.,.2),expected)

    def test_hint_near_boundary_falls_back(self):
        profile=pp.Profile(r_min=.5,r_max=.5,query_radius=0,step=.2,error=0,speed=0,acceleration=0,clock=0,domain=4.)
        policy=pp.Policy(half_length=.1,half_width=.1,pose_error=0,yaw_rate=0,traction=0)
        cells=pp.required(profile,policy,0.,.2);radius=profile.r_min-profile.step/np.sqrt(2)-1e-9
        for shift in [0.,radius-1e-13,radius,radius+1e-13,1.]:
            result=dict(witnesses=cells+np.array([shift,0]),error=np.zeros(len(cells)),ray_indices=np.arange(len(cells)))
            self.assertEqual(self.v.covered(result,profile,policy,0.,0.,.2),pp.coverage(result,profile,policy,0.,0.,.2)[0])

    def test_local_query_matches_full_with_ties_and_fallback(self):
        rng=np.random.default_rng(27)
        for trial in range(30):
            current=rng.uniform(-4,4,(5000,2));targets=current[:100]+rng.normal(0,.001,(100,2))
            if trial%3==0:current[100:200]=current[:100]
            if trial%5==0:targets+=10
            actual,_=nearest(current,targets);expected=cKDTree(current).query(targets,k=1)[1]
            np.testing.assert_array_equal(actual,expected)

    def test_timing_matches_reference_after_valid_geometry(self):
        self.assertTrue(self.check())
        for now in [1.,1.02,1.10,1.12,1.121,1.4]:
            self.assertEqual(timing_after_verified(self.blob,self.policy,self.speed,now),conditional_stop_gate(self.blob,self.profiles,self.scope,self.contract,self.policy,self.speed,self.yaw,now))


if __name__=='__main__':unittest.main()
