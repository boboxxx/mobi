import copy,hashlib,math,unittest
import numpy as np
import flow
import test_continuity as fixtures

class FlowTests(unittest.TestCase):
    def fixture(self,method='fine_terminal'):
        f=fixtures.ContinuityTests();f.setUp();rx=flow.Receiver(method,f.profiles,f.contract,{n:2.5 for n in f.profiles})
        a=rx.register(f.legacy,f.initial,f.scope,f.motion);rx.reset(10000)
        def packet(t,seq):
            raw=flow.compact.stream.step(f.hidden,f.origin,t,t,f.profiles,f.contract,a,.25,seq)
            return dict(kind='position-flow-v1' if rx.position else 'center-flow-v1',dynamics='observation-speed-age-v1',anchor=a.identity,steps=[raw])
        return f,rx,packet

    def test_two_endpoint_bound_numeric_integration_and_clamps(self):
        rng=np.random.default_rng(8821)
        for _ in range(200):
            v0,v1,a,dt=rng.uniform(.01,10,4);t=np.linspace(0,dt,10001)
            numeric=np.trapz(np.minimum(v0+a*t,v1+a*(dt-t)),t);got=flow.terminal_distance(v0,v1,a,dt)
            self.assertGreaterEqual(got+1e-11,numeric);self.assertLess(got-numeric,1e-5)
            self.assertLessEqual(got,v0*dt+.5*a*dt**2+1e-12)
        self.assertAlmostEqual(flow.terminal_distance(5,5,3,.5),2.6875)
        self.assertAlmostEqual(flow.terminal_distance(1,10,2,1),2)
        self.assertAlmostEqual(flow.terminal_distance(10,1,2,1),2)
        self.assertAlmostEqual(flow.terminal_distance(3,1,0,2),2)
        self.assertEqual(flow.terminal_distance(3,1,2,0),0)

    def test_vector_trajectories_satisfy_path_bound(self):
        rng=np.random.default_rng(911)
        for _ in range(100):
            dt=rng.uniform(.1,3);n=50;ds=dt/n;a=3.;v=rng.normal(size=2);v0=np.linalg.norm(v);disp=np.zeros(2)
            for j in range(n):
                acc=rng.normal(size=2);acc*=a*rng.random()/np.linalg.norm(acc);new=v+acc*ds;disp+=(v+new)*.5*ds;v=new
            self.assertLessEqual(np.linalg.norm(disp),flow.terminal_distance(v0,np.linalg.norm(v),a,dt)+1e-12)

    def test_invalid_bound_inputs(self):
        for value in [-1,math.nan,math.inf]:
            for j in range(4):
                args=[1.,1.,1.,1.];args[j]=value
                with self.assertRaises(ValueError):flow.terminal_distance(*args)

    def test_expired_authority_does_not_erase_fact_or_backdate_new_grant(self):
        f,rx,packet=self.fixture();self.assertFalse(rx.can_act(500000))
        d,s=rx.advance(flow.compact.encode(packet(.3,1)),500000)
        self.assertTrue(d['fact_accepted']);self.assertFalse(rx.can_act(500000));rx.finish(510000)
        self.assertFalse(rx.can_act(509999));self.assertTrue(rx.can_act(510000,0))
        self.assertFalse(rx.can_act(d['endpoint_us'],0))
        self.assertFalse(rx.can_act(d['endpoint_us']-200000))

    def test_malformed_future_wrong_root_replay_do_not_change_facts(self):
        f,rx,packet=self.fixture();good=packet(.15,1);before=rx.ref
        for bad in [dict(good,anchor='x'*64),dict(good,steps=good['steps']*2)]:
            with self.assertRaises(ValueError):rx.advance(flow.compact.encode(bad),200000)
            self.assertEqual(rx.ref,before);self.assertIsNone(rx.pending)
        with self.assertRaises(ValueError):rx.advance(flow.compact.encode(good),100000)
        bad=copy.deepcopy(good);bad['steps'][0]['payload']['rays'][0][1]+=1
        with self.assertRaises(ValueError):rx.advance(flow.compact.encode(bad),200000)
        rx.advance(flow.compact.encode(good),200000);rx.finish(210000)
        with self.assertRaises(ValueError):rx.advance(flow.compact.encode(good),220000)
        with self.assertRaises(ValueError):rx.advance(flow.compact.encode(packet(.3,2)),209999)

    def test_pending_and_finish_integrity(self):
        f,rx,packet=self.fixture()
        with self.assertRaises(ValueError):rx.finish(200000)
        rx.advance(flow.compact.encode(packet(.15,1)),200000)
        with self.assertRaises(ValueError):rx.advance(flow.compact.encode(packet(.3,2)),400000)
        with self.assertRaises(ValueError):rx.finish(199999)
        self.assertFalse(rx.can_act(205000,0));rx.finish(210000)

    def test_changed_geometry_and_gap_equal_uncached_forward(self):
        f,rx,packet=self.fixture('coarse_forward');state=rx.root_state
        for j,t in enumerate([.15,.3,1.2]):
            b=packet(t,j+1)
            if j==1:
                raw=b['steps'][0];raw['payload']['rays'][0][1]+=1;raw['sha256']=hashlib.sha256(flow.body.canonical(raw['payload'])).hexdigest()
            p,o,r=flow.body.decode(flow.body.canonical(b['steps'][0]),f.profiles,f.scope,f.contract);v=flow.body.projections(o,r,p['reference_us'],f.profiles,f.scope,f.contract)
            independent={n:flow.compact.observer.propagate(state.possible[n],g.step,flow.body.travel(t-state.reference_us/1e6,state.effective_profiles[n]))&~flow.compact.observer.exclusion(v[n],g,f.motion) for n,g in rx.core.grid_profiles.items()}
            d,got=rx.advance(flow.compact.encode(b),round(t*1e6)+50000);rx.finish(round(t*1e6)+60000)
            for n in independent:np.testing.assert_array_equal(independent[n],got.possible[n])
            state=got
        self.assertEqual(d['horizon_us'],0);self.assertTrue(d['fact_accepted']);self.assertFalse(rx.can_act(1260000))
        self.assertEqual(len(rx.masks),2)

    def test_reset_discards_caches_and_future_bound_stays_one_sided(self):
        f,rx,packet=self.fixture();d,s=rx.advance(flow.compact.encode(packet(.15,1)),200000);rx.finish(210000)
        for n,g in s.effective_profiles.items():
            self.assertEqual(d['classes'][n],flow.compact.observer.frontier(s.possible[n],g,f.motion))
        self.assertGreater(len(rx.masks),0);rx.reset(10000);self.assertEqual(len(rx.masks),0)
        self.assertEqual(rx.ref,rx.anchor.reference_us);self.assertEqual(rx.previous_h,rx.anchor.endpoint_us-rx.anchor.reference_us)

    def test_same_past_bridge_improvement_given_to_fixed_baseline(self):
        old_budget=5*.495+1.5*.495**2
        self.assertGreater(5*.5+1.5*.5**2,old_budget)
        self.assertLess(flow.terminal_distance(5,5,3,.5),old_budget)
        self.assertGreater(flow.terminal_distance(5,5,3,.55),old_budget)
        f,rx,packet=self.fixture('fixed_terminal');d,s=rx.advance(flow.compact.encode(packet(.15,1)),200000);rx.finish(210000)
        self.assertTrue(d['fact_accepted']);self.assertIsNone(s);rx.reset(10000)
        self.assertEqual(rx.previous_h,rx.anchor.endpoint_us-rx.anchor.reference_us)

if __name__=='__main__':unittest.main()
