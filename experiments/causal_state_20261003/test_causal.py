import unittest
from engine import replay

def row(key,stamp,layout=0,source=100,receiver=100,wire=100,available=True,horizon=500000):
    return dict(id=key,source_us=stamp,layout=layout,acquisition_us=0,available=available,bounds=[dict(lower_us=horizon)]*2,methods={m:dict(source_us=source,receiver_us=receiver,wire_bytes=wire) for m in ('union','lossless_centers','full_xyz','fixed200')})

class TestCausal(unittest.TestCase):
    def test_future_suffix_cannot_change_past_decisions(self):
        first=row('now',0);future=row('future',300000)
        a=replay([first],'union',20000000,0,range(6));b=replay([first,future],'union',20000000,0,range(6))
        self.assertEqual(a['decisions'],b['decisions'])
    def test_arrival_never_refreshes_source_expiry(self):
        d=replay([row('slow',0,wire=100000)],'union',2000000,0)
        self.assertEqual(d['events'][0]['deadlines_us'],[500000]*2)
        self.assertEqual(d['grants'],0)
    def test_sender_transport_receiver_each_queue_pay(self):
        d=replay([row('a',0,source=10000,receiver=50000,wire=10000),row('b',0,1,source=10000,receiver=50000,wire=10000)],'union',2000000,0)
        a,b=d['events'];self.assertEqual(b['source_start_us'],a['source_end_us']);self.assertEqual(b['tx_start_us'],a['tx_end_us']);self.assertEqual(b['receiver_start_us'],a['arrival_us'])
    def test_refusal_does_not_create_or_extend_authority(self):
        d=replay([row('good',0),row('missing',250000,available=False)],'union',20000000,0)
        self.assertTrue(all(x['deadline_us']==500000 for x in d['decisions'] if x['grant']))
        self.assertFalse(any(x['grant'] for x in d['decisions'] if x['now_us']>280000))
    def test_expired_source_is_not_used_before_delivery(self):
        d=replay([row('late',0,receiver=600000)],'union',20000000,0)
        self.assertEqual(d['grants'],0)
    def test_same_frame_two_views_are_independently_useful(self):
        d=replay([row('bad',0,0,available=False),row('good',0,1)],'union',20000000,0)
        self.assertGreater(d['grants'],0)
        self.assertTrue(all(x['fact_id']=='good' for x in d['decisions'] if x['grant']))
    def test_missing_whole_episode_remains_in_denominator(self):
        d=replay([],'union',20000000,0);self.assertEqual(d['scheduled_queries'],32);self.assertEqual(d['grants'],0)

if __name__=='__main__':unittest.main()
