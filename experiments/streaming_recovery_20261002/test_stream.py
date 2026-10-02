import copy, hashlib, json, unittest, zlib
import numpy as np
from scipy.spatial import cKDTree
import stream
from test_continuity import ContinuityTests


class StreamTests(unittest.TestCase):
    def test_corrected_frontier_maximum_and_unregistered_root(self):
        import frontier
        fixture=ContinuityTests();fixture.setUp()
        raw=stream.step(fixture.hidden,fixture.origin,.15,.15,fixture.profiles,fixture.contract,fixture.anchor,.25,1)
        result=frontier.compute(fixture.rx,fixture.anchor.identity,raw)
        h=result['horizon_us'];self.assertGreaterEqual(h,250000)
        self.assertTrue(frontier.check(fixture.rx,fixture.anchor.identity,raw,h))
        self.assertFalse(frontier.check(fixture.rx,fixture.anchor.identity,raw,h+1))
        with self.assertRaises(KeyError):frontier.compute(stream.Receiver(fixture.profiles,fixture.contract),fixture.anchor.identity,raw)

    def test_aged_acceleration_reduces_frontier(self):
        from dataclasses import replace
        import frontier
        fixture=ContinuityTests();fixture.setUp()
        raw=stream.step(fixture.hidden,fixture.origin,.15,.15,fixture.profiles,fixture.contract,fixture.anchor,.25,1)
        profiles={n:replace(p,acceleration=3.) for n,p in fixture.profiles.items()}
        old=stream.base.LegacyReceiver(profiles,fixture.contract,'test','map')
        initial=stream.body.pack(fixture.points,fixture.origin,0.,0.,profiles,fixture.scope,fixture.contract,fixture.motion,None,.25,0)
        self.assertTrue(old.accept(initial,fixture.scope,fixture.motion,.02))
        rx=stream.Receiver(profiles,fixture.contract);anchor=rx.register(old,initial,fixture.scope,fixture.motion)
        fresh=stream.step(fixture.hidden,fixture.origin,.15,.15,profiles,fixture.contract,anchor,.25,1)
        # Reuse the actual fresh selected source; no freshly dated geometry.
        p,o,r=stream.body.decode(stream.body.canonical(fresh),profiles,fixture.scope,fixture.contract)
        aged=json.loads(stream.body.serialize(o,r,p['reference_us']+10000,profiles,fixture.scope,fixture.contract,.25,1))
        fresh_h=frontier.compute(rx,anchor.identity,fresh)['horizon_us'];aged_h=frontier.compute(rx,anchor.identity,aged)['horizon_us']
        self.assertLess(aged_h,fresh_h)

    def test_random_strict_balls_match_independent_tree(self):
        rng=np.random.default_rng(20261005)
        for count in [0,1,40,400]:
            p=stream.body.Profile(domain=1.3,step=.1,r_min=.2,r_max=.4)
            c=stream.body.grid(p.domain,p.step)[0];c=c[rng.random(len(c))>.3]
            w=rng.uniform(-1.5,1.5,(count,2));error=rng.choice([0,.02,.08,.2],count)
            v=dict(a=dict(witnesses=w,error=error,ray_indices=np.arange(count)))
            radius=p.r_min-error-p.step/np.sqrt(2)-1e-9
            covered=np.zeros(len(c),dtype=bool)
            for i,r in enumerate(radius):
                if r>0:covered|=np.linalg.norm(c-w[i],axis=1)<r
            expected=covered.all()
            self.assertEqual(stream.cover(v,dict(a=p),stream.body.Motion(),dict(a=c),count),expected)
            chosen=stream.cover(v,dict(a=p),stream.body.Motion(),dict(a=c),count,True)
            self.assertEqual(chosen is not None,expected)
            if chosen is not None:
                independent=np.zeros(len(c),dtype=bool)
                for i in chosen:independent|=np.linalg.norm(c-w[i],axis=1)<radius[i]
                self.assertTrue(independent.all())

    def test_exact_boundary_is_not_a_witness(self):
        p=stream.body.Profile(domain=1.,step=.1,r_min=.2,r_max=.4)
        c=stream.body.grid(p.domain,p.step)[0][0:1]
        radius=p.r_min-p.step/np.sqrt(2)-1e-9
        w=c+np.array([[radius,0.]])
        v=dict(a=dict(witnesses=w,error=np.zeros(1),ray_indices=np.zeros(1,dtype=int)))
        expected=bool(np.linalg.norm(c-w,axis=1)[0]<radius)
        self.assertEqual(stream.cover(v,dict(a=p),stream.body.Motion(),dict(a=c),1),expected)

    def test_lossless_bounded_transport_and_trailing_data(self):
        data=b'abc'*10000
        self.assertEqual(stream.decode(stream.encode(data)),data)
        for b in [stream.encode(data)+b'x',stream.encode(data)[:-1],b'bad',stream.MAGIC+zlib.compress(b'x'*(stream.base.MAX_BYTES+1))]:
            with self.assertRaises((ValueError,zlib.error)):stream.decode(b)

    def test_full_geometry_receiver_and_native_sender(self):
        fixture=ContinuityTests();fixture.setUp()
        rx=stream.Receiver(fixture.profiles,fixture.contract)
        anchor=rx.register(fixture.legacy,fixture.initial,fixture.scope,fixture.motion)
        steps=[stream.step(fixture.hidden,fixture.origin,t,t,fixture.profiles,fixture.contract,anchor,.25,i+1)
               for i,t in enumerate([.15,.3,.45,.6,.75,.9])]
        packet=stream.encode(stream.base.wire(anchor,steps))
        self.assertTrue(rx.accept(packet,1.,.05))
        self.assertFalse(rx.accept(packet,1.,.05))
        ordinary=copy.deepcopy(fixture.rx)
        self.assertTrue(ordinary.accept(stream.decode(packet),1.,.05))
        p=json.loads(stream.decode(packet));del p['steps'][2]
        self.assertFalse(copy.deepcopy(fixture.rx).accept(stream.body.canonical(p),1.,.05))
        rx=stream.Receiver(fixture.profiles,fixture.contract);rx.register(fixture.legacy,fixture.initial,fixture.scope,fixture.motion)
        self.assertFalse(rx.accept(stream.encode(stream.body.canonical(p)),1.,.05))


if __name__=='__main__':unittest.main()
