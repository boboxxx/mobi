import json,unittest
import numpy as np
import observer,refined
import test_continuity as fixtures


class RefinementTests(unittest.TestCase):
    def test_same_wire_contract_and_finer_feasible_set(self):
        f=fixtures.ContinuityTests();f.setUp()
        coarse=observer.Receiver(f.profiles,f.contract);fine=refined.Receiver(f.profiles,f.contract)
        a=coarse.register(f.legacy,f.initial,f.scope,f.motion);fine.register(f.legacy,f.initial,f.scope,f.motion)
        steps=[observer.stream.step(f.hidden,f.origin,t,t,f.profiles,f.contract,a,.25,i+1) for i,t in enumerate([.15,.3,.45])]
        packet=observer.wire(a,steps);c,cs=coarse.rebuild(packet);r,rs=fine.rebuild(packet)
        self.assertGreaterEqual(r['horizon_us'],c['horizon_us'])
        for n in f.profiles:
            self.assertEqual(fine.profiles[n],f.profiles[n])
            self.assertEqual(fine.grid_profiles[n].step,f.profiles[n].step/2)
            lifted=np.repeat(np.repeat(cs.possible[n],2,axis=0),2,axis=1)
            self.assertFalse(np.any(rs.possible[n]&~lifted))
        self.assertEqual(json.loads(observer.stream.decode(packet))['steps'],steps)

    def test_refinement_does_not_invent_free_hidden_interior(self):
        f=fixtures.ContinuityTests();f.setUp();fine=refined.Receiver(f.profiles,f.contract)
        a=fine.register(f.legacy,f.initial,f.scope,f.motion)
        raw=observer.stream.step(f.hidden,f.origin,3.,3.,f.profiles,f.contract,a,.25,1)
        self.assertEqual(fine.inspect(observer.wire(a,[raw]))['horizon_us'],0)


if __name__=='__main__':unittest.main()
