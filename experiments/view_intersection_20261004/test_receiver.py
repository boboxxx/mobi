import copy,unittest
from receiver import replay,cache_job

def rows_and_pairs():
    rows=[]
    for layout in (0,1):
        rows.append(dict(id='v%d'%layout,episode_id='e',blueprint='b',frame=1,source_us=0,acquisition_us=0,layout=layout,available=True,bounds=[dict(lower_us=240000)]*2,pair_id='joined',methods={'union':dict(source_us=1,receiver_us=1,wire_bytes=1)},extra={'union':dict(store=dict(us=10),combine=dict(us=100000))}))
    pairs={'joined':dict(id='joined',source_ids=['v0','v1'],geometry=dict(status='bounded',queries=[dict(lower_us=500000)]*2))}
    return rows,pairs

class TestReceiver(unittest.TestCase):
    def test_refinement_waits_for_paid_completion(self):
        rows,pairs=rows_and_pairs();t=replay(rows,pairs,'union',20000000,0)
        self.assertFalse(any(d['grant'] for d in t['decisions'] if d['now_us']<=100000))
        self.assertTrue(any(d['grant'] for d in t['decisions'] if d['now_us']==150000))
        self.assertEqual(t['jobs'][1]['receiver_start_us'],t['jobs'][0]['receiver_end_us'])
    def test_arrival_cannot_refresh_original_expiry(self):
        rows,pairs=rows_and_pairs()
        for r in rows:r['acquisition_us']=300000
        self.assertEqual(replay(rows,pairs,'union',20000000,0)['grants'],0)
    def test_empty_intersection_revokes_authority(self):
        rows,pairs=rows_and_pairs();pairs['joined']['geometry']=dict(status='empty')
        for r in rows:r['bounds']=[dict(lower_us=500000)]*2
        t=replay(rows,pairs,'union',20000000,0)
        self.assertTrue(any(d['grant'] for d in t['decisions'] if d['now_us']==50000))
        self.assertFalse(any(d['grant'] for d in t['decisions'] if d['now_us']>=150000))
    def test_future_suffix_does_not_change_past(self):
        rows,pairs=rows_and_pairs();future=copy.deepcopy(rows[0]);future.update(id='future',frame=2,source_us=1000000)
        self.assertEqual(replay(rows,pairs,'union',20000000,0)['decisions'],replay(rows+[future],pairs,'union',20000000,0)['decisions'])
    def test_different_source_epochs_do_not_join(self):
        first=dict(id='a',episode_id='e',blueprint='b',frame=1,source_us=0,layout=0,centers_cm=[[0,0]],radius_um=1000000,body_um=100000,contract_sha256='x',calibration_sha256='y')
        second=dict(first,id='b',layout=1,source_us=1)
        cache={};self.assertIsNone(cache_job(cache,first));self.assertIsNone(cache_job(cache,second))

if __name__=='__main__':unittest.main()
