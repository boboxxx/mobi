import math,unittest
import numpy as np
import ellipsoid,heading,search

def independent_flags(c,r,plane,core,outer,error):
    flags=[]
    for v in c:
        u=np.r_[v[2:],0];g=np.eye(3)/core**2+(1/outer**2-1/core**2)*np.outer(u,u);pos=np.column_stack([v[:2]+r[:,6,None]*v[2:],np.full(len(r),plane)]);delta=r[:,3:6]-r[:,:3];rel=pos-r[:,:3];den=np.einsum('ni,ij,nj->n',delta,g,delta);t=np.divide(np.einsum('ni,ij,nj->n',rel,g,delta),den,out=np.zeros(len(r)),where=den>0);left=rel-np.clip(t,0,1)[:,None]*delta;d=np.sqrt(np.einsum('ni,ij,nj->n',left,g,left));flags.append((d>1+error/core+1e-8/core).all())
    return np.array(flags)

class Tests(unittest.TestCase):
    def test_native_matches_quadratic_projection(self):
        rng=np.random.default_rng(8091);r=rng.normal(size=(127,7));r[:,6]=rng.uniform(0,3,len(r));r[0,3:6]=r[0,:3];angles=rng.uniform(-math.pi,math.pi,21);c=np.c_[rng.normal(size=(21,2)),np.cos(angles),np.sin(angles)]
        for core,outer in [(.2,.4),(.55,2.5),(.2,.2)]:np.testing.assert_array_equal(ellipsoid.clear(c,r,.6,core,outer,.018),independent_flags(c,r,.6,core,outer,.018))
    def test_sphere_contact_equivalence(self):
        angle=np.arange(257)*math.pi/128;u=np.c_[np.cos(angle),np.sin(angle)];np.testing.assert_allclose(ellipsoid.contact(u,.2,.2),search.contact_radius(u,np.array([2.3,1.3]),.2),rtol=0,atol=3e-15)
    def test_ellipsoid_contact_and_penetration(self):
        angle=np.arange(257)*math.pi/128;u=np.c_[np.cos(angle),np.sin(angle)];lam=ellipsoid.contact(u,.2,.4);np.testing.assert_allclose(ellipsoid.edge_distance(u,lam,.2,.4),1,rtol=0,atol=5e-15);self.assertTrue((ellipsoid.edge_distance(u,lam-.001,.2,.4)<1).all())
    def test_support_contact_stays_inside_permitted_outer_shape(self):
        future,u,n=heading.contacts(.2,.4);self.assertEqual(len(future),11776);self.assertTrue((np.linalg.norm(u,axis=1)<=1+1e-14).all())
        # Every shifted support point must intersect the rectangle (four edges).
        for j in range(0,len(future),173):
            v=u[j];g=np.eye(2)/.2**2+(1/.4**2-1/.2**2)*np.outer(v,v);minimum=float('inf');q=future[j]
            if (np.abs(q)<=[2.3,1.3]).all():minimum=0
            for fixed,extent in [(0,2.3),(1,1.3)]:
                free=1-fixed
                for side in [-1,1]:
                    point=q.copy();point[fixed]=side*extent;point[free]=np.clip(q[free]-g[free,fixed]*(point[fixed]-q[fixed])/g[free,free],-[2.3,1.3][free],[2.3,1.3][free]);d=point-q;minimum=min(minimum,float(d@g@d))
            self.assertLess(minimum,1)
    def test_normalized_error_bound_for_arbitrary_directions(self):
        rng=np.random.default_rng(1799)
        for _ in range(100):
            angle=rng.uniform(0,2*math.pi);u=np.array([math.cos(angle),math.sin(angle),0]);g=np.eye(3)/.2**2+(1/.4**2-1/.2**2)*np.outer(u,u);e=rng.normal(size=3);e=e/np.linalg.norm(e)*.018;self.assertLessEqual(math.sqrt(float(e@g@e)),.018/.2+1e-15)
    def test_invalid_axis_or_nonunit_heading_rejected(self):
        ray=np.array([[0,0,0,1,0,0,0.]])
        with self.assertRaises(ValueError):ellipsoid.clear(np.array([[0,1,2,0.]]),ray,0,.2,.4,.01)
        with self.assertRaises(ValueError):ellipsoid.clear(np.array([[0,1,1,0.]]),ray,0,.4,.2,.01)
if __name__=='__main__':unittest.main()
