import copy,json,math,unittest
import numpy as np
from scipy.spatial import cKDTree
import observer
import test_continuity as fixtures


def brute(mask,step,distance):
    n=len(mask);i,j=np.indices(mask.shape);target=np.column_stack([i.ravel(),j.ravel()]);source=np.argwhere(mask)
    answer=np.zeros(n*n,dtype=bool)
    for k,x in enumerate(target):
        if len(source):answer[k]=np.any(np.linalg.norm(np.maximum(np.abs(source-x)-1,0)*step,axis=1)<=distance+1e-9)
        answer[k]|=step*min(x[0],x[1],n-1-x[0],n-1-x[1])<=distance+1e-9
    return answer.reshape(n,n)


class ObserverTests(unittest.TestCase):
    def test_exact_tile_distance_matches_brute_square_union(self):
        rng=np.random.default_rng(20261006)
        for n in [3,7,11]:
            for probability in [0.,.05,.3,1.]:
                p=rng.random((n,n))<probability
                for distance in [0.,.099,.2,.201,.55]:
                    np.testing.assert_array_equal(observer.propagate(p,.2,distance),brute(p,.2,distance))

    def test_native_individual_balls_match_independent_distances(self):
        rng=np.random.default_rng(20261006);p=observer.body.Profile(domain=1.3,step=.1,r_min=.25,r_max=.4)
        c=observer.body.grid(p.domain,p.step)[0]
        for count in [0,1,100]:
            w=rng.uniform(-1.6,1.6,(count,2));error=rng.choice([0,.02,.08,.3],count)
            v=dict(witnesses=w,error=error);mask=observer.exclusion(v,p,observer.body.Motion())
            radius=p.r_min-error-p.step/math.sqrt(2)-1e-9;expected=np.zeros(len(c),dtype=bool)
            for i,r in enumerate(radius):expected|=np.linalg.norm(c-w[i],axis=1)<r
            np.testing.assert_array_equal(mask.ravel(),expected)

    def fixture(self):
        f=fixtures.ContinuityTests();f.setUp()
        rx=observer.Receiver(f.profiles,f.contract);a=rx.register(f.legacy,f.initial,f.scope,f.motion)
        return f,rx,a

    def test_new_observation_can_remove_entrants_after_expiry_gap(self):
        f,rx,a=self.fixture();raw=observer.stream.step(f.hidden,f.origin,.4,.4,f.profiles,f.contract,a,.25,1)
        self.assertIsNotNone(raw)
        legacy_packet=observer.stream.encode(observer.base.wire(a,[raw]))
        self.assertFalse(copy.deepcopy(f.rx).accept(observer.stream.decode(legacy_packet),.42,.05))
        packet=observer.wire(a,[raw]);decision,state=rx.rebuild(packet)
        self.assertGreaterEqual(decision['horizon_us'],250000)
        self.assertTrue(rx.accept(packet,.42,.05))
        self.assertFalse(rx.accept(packet,.42,.05))

    def test_missing_observation_keeps_unseen_entrants_possible(self):
        f,rx,a=self.fixture();raw=observer.stream.step(f.hidden,f.origin,3.,3.,f.profiles,f.contract,a,.25,1)
        # Current rays alone do not see hidden interior. Long enough prediction
        # permits hidden objects inside it, and must not restore K by assertion.
        packet=observer.wire(a,[raw]);decision,state=rx.rebuild(packet)
        self.assertEqual(decision['horizon_us'],0)
        self.assertFalse(rx.accept(packet,3.02))

    def test_schema_future_wrong_root_and_expiry_reject(self):
        f,rx,a=self.fixture();raw=observer.stream.step(f.hidden,f.origin,.15,.15,f.profiles,f.contract,a,.25,1)
        packet=observer.wire(a,[raw]);decision=rx.inspect(packet)
        self.assertFalse(copy.deepcopy(rx).accept(packet,.1))
        self.assertFalse(copy.deepcopy(rx).accept(packet,(decision['endpoint_us']+1)/1e6))
        self.assertFalse(observer.Receiver(f.profiles,f.contract).accept(packet,.2))
        corrupt=json.loads(observer.stream.decode(packet));corrupt['steps'][0]['payload']['scope']['plane_z']+=.1
        self.assertFalse(copy.deepcopy(rx).accept(observer.stream.encode(observer.body.canonical(corrupt)),.2))
        self.assertFalse(copy.deepcopy(rx).accept(packet+b'x',.2))

    def test_continuous_point_trajectory_is_never_lost_by_prediction(self):
        rng=np.random.default_rng(20261006);n=35;step=.1;domain=n*step/2
        for trial in range(20):
            point=rng.uniform(-.8,.8,2);p=np.zeros((n,n),dtype=bool)
            index=np.floor((point+domain)/step).astype(int);p[tuple(index)]=True
            for i in range(10):
                length=rng.uniform(0,.13);angle=rng.uniform(0,2*np.pi)
                new=point+length*np.array([np.cos(angle),np.sin(angle)])
                prediction=observer.propagate(p,step,length)
                idx=np.floor((new+domain)/step).astype(int)
                self.assertTrue(prediction[tuple(idx)])
                # An observation can remove other cells, but never the true one.
                keep=rng.random((n,n))>.4;keep[tuple(idx)]=True
                p=prediction&keep;point=new


if __name__=='__main__':unittest.main()
