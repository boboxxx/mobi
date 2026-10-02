import math,unittest
import numpy as np
import search

def numpy_clear(candidates,rays,plane,radius):
    result=[]
    for c in candidates:
        centers=np.column_stack([c[:2]+rays[:,6,None]*c[2:],np.full(len(rays),plane)])
        d=rays[:,3:6]-rays[:,:3];n=np.sum(d*d,axis=1);t=np.divide(np.sum((centers-rays[:,:3])*d,axis=1),n,out=np.zeros(len(rays)),where=n>0);t=np.clip(t,0,1)
        result.append(bool((np.linalg.norm(centers-rays[:,:3]-t[:,None]*d,axis=1)>radius).all()))
    return np.asarray(result)

class Tests(unittest.TestCase):
    def test_random_segments_match_independent_numpy(self):
        rng=np.random.default_rng(1791);r=rng.normal(size=(123,7));r[:,6]=rng.uniform(0,4,123);r[0,3:6]=r[0,:3];c=rng.normal(size=(17,4))
        for radius in [.01,.2,.55,2.]:np.testing.assert_array_equal(search.clear(c,r,.6,radius),numpy_clear(c,r,.6,radius))
    def test_segment_endpoints_and_degenerate_not_infinite_lines(self):
        r=np.array([[0,0,0,1,0,0,0],[3,0,0,3,0,0,0]],dtype=float);c=np.array([[2,0,0,0],[3,0,0,0],[.5,0,0,0]])
        np.testing.assert_array_equal(search.clear(c,r,0,.2),[True,False,False])
    def test_tangent_rejected_and_component_error_margin(self):
        r=np.array([[0,0,0,1,0,0,0]],dtype=float);c=np.array([[.5,.2,0,0],[.5,.201,0,0]])
        np.testing.assert_array_equal(search.clear(c,r,0,.2),[False,True]);self.assertFalse(search.clear(c[1:],r,0,.2+math.sqrt(3)*.0105)[0])
    def test_past_endpoint_triangle_and_reference_age(self):
        stamps=np.array([0,500000,1000000,0]);back,times,cumulative=search.backwards(stamps,1100000,5,3)
        np.testing.assert_allclose(back,[5.375+.515,2.6875+.515,.515,5.375+.515],rtol=0,atol=1e-14)
        np.testing.assert_array_equal(times,[0,500000,1000000]);self.assertEqual(cumulative[-1],.515)
    def test_intermediate_speed_sample_tightens_displacement(self):
        long=search.backwards(np.array([0,1000000]),1000000,5,3)[0][0]
        split=search.backwards(np.array([0,500000,1000000]),1000000,5,3)[0][0]
        self.assertGreater(long,split);self.assertAlmostEqual(long-split,.375)
    def test_contact_hits_rounded_rectangle_with_strict_radial_penetration(self):
        angles=np.linspace(0,2*math.pi,257);u=np.c_[np.cos(angles),np.sin(angles)];extent=np.array([2.3,1.3]);r=.2
        lam=search.contact_radius(u,extent,r);d=np.linalg.norm(np.maximum(np.abs(u*lam[:,None])-extent,0),axis=1)
        np.testing.assert_allclose(d,r,rtol=0,atol=2e-15);self.assertTrue((np.linalg.norm(np.maximum(np.abs(u*(lam-.001)[:,None])-extent,0),axis=1)<r).all())
    def test_invalid_native_input_fails(self):
        with self.assertRaises(ValueError):search.clear(np.ones((1,4)),np.ones((1,6)),0,.2)
        with self.assertRaises(ValueError):search.clear(np.array([[math.nan,0,0,0]]),np.ones((1,7)),0,.2)
        with self.assertRaises(ValueError):search.clear(np.ones((1,4)),np.ones((0,7)),0,.2)
    def test_search_failure_is_none_and_simple_hidden_sphere_returns_witness(self):
        ray=np.array([[0,0,10,1,0,10,0]],dtype=float)
        w,counts=search.find(ray,.6,np.zeros(2),.2,1000000,1000000,.2,.01)
        self.assertEqual(w['time_us'],0);self.assertEqual(counts['native_calls'],1)
        # One enormous sphere would overlap the distant segment for every time.
        w,counts=search.find(np.array([[0,0,0,0,0,0,0]],dtype=float),0,np.zeros(2),0,0,0,.2,100.)
        self.assertIsNone(w);self.assertEqual(counts['native_calls'],31)
if __name__=='__main__':unittest.main()
