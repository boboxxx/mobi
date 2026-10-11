"""Prospective execution epoch, spatial scope, and causal CPU queue tests."""
import hashlib
import unittest
import model as M

class Tests(unittest.TestCase):
    def fixture(self):
        ctx=dict(fixture=True)
        lease=dict(version=1,episode='e',context=hashlib.sha256(M.R.canonical(ctx)).hexdigest(),seq=1,
            controller_sample_us=100000,source_us=0,expiry_us=500000,query_um=[0,0],radius_um=2500000,action_us=300000)
        return lease,lease['context']

    def test_admission_at_execution_not_at_query(self):
        lease,h=self.fixture()
        self.assertTrue(M.admit(lease,200000,[0,0],2198221,'e',h)['allowed'])
        self.assertFalse(M.admit(lease,200001,[0,0],2198221,'e',h)['allowed'])
        self.assertEqual(lease['source_us'],0)
        self.assertFalse(M.admit(lease,200000,[0,0],2198221,'other',h)['allowed'])

    def test_scope_includes_future_full_body_not_only_current_centre(self):
        lease,h=self.fixture()
        self.assertTrue(M.admit(lease,150000,[56779,0],2198221,'e',h)['allowed'])
        self.assertFalse(M.admit(lease,150000,[56780,0],2198221,'e',h)['allowed'])
        self.assertFalse(M.admit(lease,150000,[40000,41000],2198221,'e',h)['allowed'])

    def test_queue_cannot_complete_before_arrival_or_previous_job(self):
        finish=M.service(80000,90000,200)
        self.assertEqual(finish,90200)
        free,arrival=M.transmit(finish,100000,250)
        self.assertEqual((free,arrival),(100100,120100))
        lease,h=self.fixture()
        self.assertEqual(M.unpack(M.pack(lease)),lease)

if __name__=='__main__':
    unittest.main(verbosity=2)
