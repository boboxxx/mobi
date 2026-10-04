import unittest
from engine import replay
from codec import pack,unpack,active_data
from kernel import geometry
class Tests(unittest.TestCase):
 def row(self,key,stamp,status='bounded'):
  return dict(id=key,source_us=stamp,acquisition_us=0,layout=0,methods={'active':dict(source_us=0,receiver_us=0,wire_bytes=0,status=status,lower_us=[500000,500000] if status=='bounded' else [])})
 def test_setup_paid_before_later_jobs(self):
  a=replay([self.row('a',0)],'active',2000000,0,dict(source_us=1000,receiver_us=2000,wire_bytes=100000));self.assertEqual(a['events'][0]['arrival_us'],423000);self.assertEqual(a['grants'],0)
 def test_source_age_and_future_prefix(self):
  row=self.row('old',-450000);a=replay([row],'active',20000000,0);self.assertFalse(any(d['grant'] for d in a['decisions']))
  a=replay([self.row('a',0)],'active',20000000,0);b=replay([self.row('a',0),self.row('later',400000)],'active',20000000,0);self.assertEqual([d for d in a['decisions'] if d['now_us']<400000],[d for d in b['decisions'] if d['now_us']<400000])
 def test_empty_revokes_but_refusal_does_not(self):
  a=replay([self.row('a',0),self.row('bad',100000,'empty')],'active',20000000,0);self.assertFalse(any(d['grant'] for d in a['decisions'] if d['now_us']>=150000))
  a=replay([self.row('a',0),self.row('bad',100000,'refused')],'active',20000000,0);self.assertTrue(any(d['grant'] for d in a['decisions'] if d['now_us']==150000))
 def test_actual_active_packet_and_checksum(self):
  cat={'x':[1.,1.,1.]};body=1732051;g=geometry([[[800,0],[801,0]]],body+8000,body);data=active_data(g);wire=pack('active',data,0,0,42,12345,'00'*32,'11'*32);out=unpack(wire,'active','00'*32,'11'*32,cat,{}, {},{'x':0});self.assertEqual(out['lower_us'],[q['lower_us'] for q in g['queries']]);self.assertEqual(out['source_us'],12345)
  with self.assertRaises(Exception):unpack(wire[:-1]+bytes([wire[-1]^1]),'active','00'*32,'11'*32,cat,{}, {},{'x':0})
if __name__=='__main__':unittest.main()
