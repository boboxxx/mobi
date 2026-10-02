import copy,json,unittest,zlib
import numpy as np
import compact
import test_continuity as fixtures
import test_observer


class CompactTests(unittest.TestCase):
    def fixture(self):
        f=fixtures.ContinuityTests();f.setUp()
        rx=compact.PositionReceiver(f.profiles,f.contract,{n:2.5 for n in f.profiles},2)
        a=rx.register(f.legacy,f.initial,f.scope,f.motion)
        steps=[compact.stream.step(f.hidden,f.origin,t,t,f.profiles,f.contract,a,.25,i+1) for i,t in enumerate([.15,.3,.45])]
        return f,rx,a,dict(kind='position-observations-v1',dynamics='observation-speed-age-v1',anchor=a.identity,steps=steps)

    def test_native_transform_matches_brute_and_previous_edt(self):
        rng=np.random.default_rng(20261007)
        for n in [3,7,11,24]:
            for prob in [0.,.05,.3,1.]:
                p=rng.random((n,n))<prob
                for dist in [0.,.099,.2,.201,.55,2.8]:
                    got=compact.propagate(p,.2,dist)
                    np.testing.assert_array_equal(got,compact.observer.propagate(p,.2,dist))
                    np.testing.assert_array_equal(got,test_observer.brute(p,.2,dist))

    def test_dictionary_is_lossless_with_changed_rays_ages_and_horizon(self):
        f,rx,a,b=self.fixture();x=copy.deepcopy(b)
        x['steps'][1]['payload']['rays'][0][1]+=1
        x['steps'][2]['payload']['rays'][0][4]-=1
        x['steps'][2]['payload']['horizon_us']+=1
        self.assertEqual(compact.body.canonical(compact.decode(compact.encode(x))),compact.body.canonical(x))
        with self.assertRaises(ValueError):rx.inspect(compact.encode(x)) # unchanged checksums
        self.assertEqual(compact.decode(compact.encode(b)),b)
        self.assertGreater(rx.inspect(compact.encode(b))['horizon_us'],0)

    def test_dictionary_bounds_bad_id_type_trailing_truncation(self):
        f,rx,a,b=self.fixture();data=compact.encode(b)
        for broken in [data+b'x',data[:-1],b'wrong'+data]:
            self.assertFalse(rx.accept(broken,.5))
        d=json.loads(zlib.decompress(data[len(compact.MAGIC):]))
        for field,value in [('templates',[]),('steps',d['steps']*33)]:
            x=copy.deepcopy(d);x[field]=value
            with self.assertRaises(ValueError):compact.decode(compact.MAGIC+zlib.compress(compact.body.canonical(x)))
        for tid in [-1,100,True]:
            x=copy.deepcopy(d);x['steps'][0][0]=tid
            with self.assertRaises(ValueError):compact.decode(compact.MAGIC+zlib.compress(compact.body.canonical(x)))
        with self.assertRaises(ValueError):compact.decode(compact.MAGIC+zlib.compress(b' '* (compact.LIMIT+1)))

    def test_window_keeps_unknown_arrivals_and_future_domain_guard(self):
        f,rx,a,b=self.fixture()
        raw=compact.stream.step(f.hidden,f.origin,3.,3.,f.profiles,f.contract,a,.25,10)
        b['steps']=[raw];self.assertEqual(rx.inspect(compact.encode(b))['horizon_us'],0)
        mask=np.zeros((10,10),dtype=bool);pred=compact.propagate(mask,.1,.15)
        self.assertTrue(pred[:2,:].all());self.assertTrue(pred[-2:,:].all());self.assertFalse(pred[5,5])
        with self.assertRaises(ValueError):compact.PositionReceiver(f.profiles,f.contract,{n:2.51 for n in f.profiles},2)

    def test_geometry_cache_changes_with_actual_source_and_clock(self):
        o=np.array([[0,0,0]],dtype=np.int64);r=np.array([[0,1,2,3,100]],dtype=np.int64)
        key=compact.geometry_key(o,r,101)
        self.assertEqual(key,compact.geometry_key(o,r+np.array([[0,0,0,0,100]]),201))
        for row in [np.array([[0,2,2,3,100]],dtype=np.int64),np.array([[0,1,2,3,99]],dtype=np.int64)]:
            self.assertNotEqual(key,compact.geometry_key(o,row,101))
        self.assertNotEqual(key,compact.geometry_key(o+1,r,101))

    def test_cached_rebuild_equals_fully_uncached_changed_observations(self):
        f,rx,a,b=self.fixture();x=copy.deepcopy(b)
        x['steps'][1]['payload']['rays'][0][1]+=1
        for raw in x['steps']:raw['sha256']=compact.hashlib.sha256(compact.body.canonical(raw['payload'])).hexdigest()
        got,state=rx.rebuild(compact.encode(x));old=rx._states[a.identity]
        for raw in x['steps']:
            p,o,r=compact.body.decode(compact.body.canonical(raw),f.profiles,f.scope,f.contract)
            ref=p['reference_us'];v=compact.body.projections(o,r,ref,f.profiles,f.scope,f.contract);possible={};effective={}
            for n,g in rx.grid_profiles.items():
                possible[n]=compact.observer.propagate(old.possible[n],g.step,compact.body.travel((ref-old.reference_us)/1e6,old.effective_profiles[n]))&~compact.observer.exclusion(v[n],g,f.motion)
                effective[n]=compact.base.reference_speed(g,r,ref)
            old=compact.observer.State(ref,p['sequence'],possible,effective)
        for n in f.profiles:np.testing.assert_array_equal(state.possible[n],old.possible[n])
        h=min(compact.observer.frontier(old.possible[n],old.effective_profiles[n],f.motion)['horizon_us'] for n in f.profiles)
        self.assertEqual(got['horizon_us'],h);self.assertGreaterEqual(got['cache']['mask_misses'],2)


if __name__=='__main__':unittest.main()
