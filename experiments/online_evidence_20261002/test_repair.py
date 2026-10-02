import json,unittest
import numpy as np
from efficient_renew import body,repair,reference_repair


class ReuseTests(unittest.TestCase):
    def setUp(self):
        self.profiles={'small':body.Profile(domain=3,step=.1,r_min=.2,r_max=.3,error=0,query_radius=0,speed=.2,acceleration=0)}
        self.scope=body.Scope('test','map',(0.,0.),.6);self.contract=body.Contract()
        self.motion=body.Motion(half_length=.3,half_width=.2,acceleration=0,yaw_rate=0)
        axis=np.arange(-1.5,1.51,.05);x,y=np.meshgrid(axis,axis)
        self.points=np.column_stack([x.ravel()/.6,y.ravel()/.6,np.full(x.size,-1.)]);self.origin=np.array([0.,0.,3.])
        self.template=body.pack(self.points,self.origin,0.,0.,self.profiles,self.scope,self.contract,self.motion,None,.4,0)
        self.assertIsNotNone(self.template)

    def test_reuse_matches_complete_reference_and_receiver(self):
        for shift in [0.,.03,-.025]:
            points=self.points.copy();points[:,0]+=shift
            for horizon in [.4,.45,.475]:
                args=(self.template,points,self.origin,.05,.05,self.profiles,self.scope,self.contract,self.motion,None,horizon,1)
                blob=repair(*args);self.assertEqual(blob,reference_repair(*args));self.assertIsNotNone(blob)
                self.assertTrue(body.verify(blob,self.profiles,self.scope,self.contract,self.motion,None,.07,0))

    def test_no_unobserved_hole_is_filled_without_history(self):
        points=self.points[np.linalg.norm(self.points[:,:2],axis=1)>.8]
        args=(self.template,points,self.origin,.05,.05,self.profiles,self.scope,self.contract,self.motion,None,.4,1)
        self.assertIsNone(repair(*args));self.assertIsNone(reference_repair(*args))

    def test_receiver_recomputes_changed_wire_geometry(self):
        args=(self.template,self.points,self.origin,.05,.05,self.profiles,self.scope,self.contract,self.motion,None,.4,1)
        blob=repair(*args);p=json.loads(blob);payload=p['raw']['payload'];payload['rays']=payload['rays'][:1]
        import hashlib
        p['raw']['sha256']=hashlib.sha256(body.canonical(payload)).hexdigest()
        self.assertFalse(body.verify(body.canonical(p),self.profiles,self.scope,self.contract,self.motion,None,.07,0))


if __name__=='__main__':unittest.main()
