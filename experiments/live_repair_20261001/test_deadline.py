import unittest
from deadline import usable, next_sample_ready


class DeadlineTests(unittest.TestCase):
    def test_submicrosecond_remaining_is_not_usable(self):
        self.assertTrue(.4000008 < .400001)
        self.assertFalse(usable(400001,.4000008))
        self.assertTrue(usable(400001,.399999))

    def test_tick_rounding_reservation(self):
        self.assertFalse(next_sample_ready(400001,.3500008))
        self.assertFalse(next_sample_ready(400001,.3500000))
        self.assertTrue(next_sample_ready(400001,.3000008))

    def test_full_action_must_finish_strictly_early(self):
        self.assertFalse(usable(400000,.2,200000))
        self.assertTrue(usable(400000,.19,200000))
        with self.assertRaises(ValueError):usable(400000,float('nan'))


if __name__=='__main__':unittest.main()
