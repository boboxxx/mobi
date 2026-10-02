import unittest
from replay_fifo import schedule

class FifoTests(unittest.TestCase):
    def test_root_transmission_blocks_early_update(self):
        # Root occupies source until100ms, link until600ms. Next evidence is
        # ready at250ms; its500byte update cannot transmit before600ms.
        x=schedule(250000,10.,1.,500,.5,100000,600000)
        self.assertEqual(x,(250000,260000,261000,600000,608000,628000))
    def test_root_source_work_and_existing_link_backlog_are_both_paid(self):
        x=schedule(50000,10.,1.,1000,20.,100000,200000)
        self.assertEqual(x,(100000,110000,111000,200000,200400,220400))
    def test_idle_resources_do_not_add_stale_root_delay(self):
        x=schedule(900000,0.,0.,1000,20.,100000,600000)
        self.assertEqual(x,(900000,900000,900000,900000,900400,920400))
if __name__=='__main__':unittest.main()
